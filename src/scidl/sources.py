"""Discover legitimate full-text locations from scholarly APIs and publisher pages."""

import html
import re
import time
import urllib.parse
from dataclasses import dataclass

import requests

from scidl.access_policy import AccessDecision, evaluate_response, reject_unsupported_url
from scidl.models import PdfCandidate

_PDF_META = re.compile(r'citation_pdf_url["\']?\s+content=["\']([^"\']+)', re.I)
_OA_MARKERS = ("open access", "creativecommons.org/licenses", "cc by", "free full text")


@dataclass
class DiscoveryResult:
    title: str | None
    candidates: list[PdfCandidate]
    restriction: AccessDecision | None = None


class ScholarlySources:
    """Sequential, rate-limited discovery client with bounded retries."""

    def __init__(self, email: str = "", requests_per_second: float = 1.0,
                 timeout: int = 45, max_retries: int = 3,
                 authorized: bool = False, session: requests.Session | None = None):
        contact = f"; mailto:{email}" if email else ""
        self.headers = {"User-Agent": f"sci-dl/0.3 (+https://github.com/GEROGEFLOOD/sci_download{contact})"}
        self.email = email
        self.interval = 1.0 / max(0.1, min(1.0, requests_per_second))
        self.timeout = timeout
        self.max_retries = min(3, max(1, max_retries))
        self.authorized = authorized
        self.session = session or requests.Session()
        self._last_request = 0.0

    def _get(self, url: str, **kwargs):
        reject_unsupported_url(url)
        wait = self.interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()
        headers = dict(self.headers)
        headers.update(kwargs.pop("headers", {}) or {})
        return self.session.get(url, headers=headers, timeout=self.timeout, **kwargs)

    @staticmethod
    def _append(items: list[PdfCandidate], source: str, url: str | None,
                is_open_access: bool = True) -> None:
        if url and url.startswith("https://") and all(x.url != url for x in items):
            reject_unsupported_url(url)
            items.append(PdfCandidate(source, url, is_open_access))

    def discover(self, doi: str) -> DiscoveryResult:
        doi = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        encoded = urllib.parse.quote(doi, safe="")
        title = None
        candidates: list[PdfCandidate] = []

        # Crossref metadata is resolved first. Its resource links are retained only when
        # explicitly marked as unrestricted or when authorized access was requested.
        try:
            response = self._get(f"https://api.crossref.org/works/{encoded}")
            if response.ok:
                message = response.json().get("message", {})
                title = next(iter(message.get("title", [])), None)
                if self.authorized:
                    for link in message.get("link", []):
                        self._append(candidates, "crossref", link.get("URL"), False)
        except (requests.RequestException, ValueError, KeyError):
            pass

        # PMC / Europe PMC has the highest download priority.
        try:
            response = self._get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={"query": f'DOI:"{doi}"', "format": "json"},
            )
            if response.ok:
                records = response.json().get("resultList", {}).get("result", [])
                for record in records:
                    pmcid = record.get("pmcid") or (record.get("id") if record.get("source") == "PMC" else None)
                    if pmcid:
                        self._append(candidates, "europe_pmc", f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextPDF")
        except (requests.RequestException, ValueError, KeyError):
            pass

        if self.email:
            try:
                response = self._get(
                    f"https://api.unpaywall.org/v2/{encoded}", params={"email": self.email}
                )
                if response.ok:
                    data = response.json()
                    location = data.get("best_oa_location") or {}
                    self._append(candidates, "unpaywall", location.get("url_for_pdf") or location.get("url"))
            except (requests.RequestException, ValueError, KeyError):
                pass

        try:
            response = self._get(f"https://api.openalex.org/works/https://doi.org/{encoded}")
            if response.ok:
                data = response.json()
                title = title or data.get("display_name")
                locations = [data.get("best_oa_location") or {}, *(data.get("locations") or [])]
                for location in locations:
                    if location.get("is_oa") or location.get("pdf_url"):
                        self._append(candidates, "openalex", location.get("pdf_url"))
        except (requests.RequestException, ValueError, KeyError):
            pass

        # Publisher page: stop on restrictions. Only explicit OA pages yield a PDF by
        # default; user credentials are honored solely in --authorized-access mode.
        restriction = None
        try:
            response = self._get(f"https://doi.org/{urllib.parse.quote(doi, safe='/')}", allow_redirects=True)
            decision = evaluate_response(response)
            if decision not in (AccessDecision.ALLOW, AccessDecision.UNKNOWN):
                restriction = decision
            elif "html" in response.headers.get("Content-Type", "").lower():
                body = response.text[:524_288]
                match = _PDF_META.search(body)
                is_oa = any(marker in body.lower() for marker in _OA_MARKERS)
                if match and (is_oa or self.authorized):
                    url = urllib.parse.urljoin(response.url, html.unescape(match.group(1)))
                    self._append(candidates, "publisher", url, is_oa)
        except requests.RequestException:
            pass

        priority = {"europe_pmc": 0, "unpaywall": 1, "openalex": 2,
                    "crossref": 3, "publisher": 5}
        candidates.sort(key=lambda item: priority.get(item.source, 4))
        return DiscoveryResult(title, candidates, restriction)
