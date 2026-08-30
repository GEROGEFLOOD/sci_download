"""High-level policy-aware download pipeline."""

from pathlib import Path

import requests

from scidl.access_policy import AccessDecision, UnsupportedSourceError
from scidl.downloader import download_pdf
from scidl.models import DownloadResult, DownloadStatus
from scidl.parser import doi_to_filename
from scidl.sources import ScholarlySources


_RESTRICTION_STATUS = {
    AccessDecision.AUTH_REQUIRED: DownloadStatus.AUTH_REQUIRED,
    AccessDecision.PAYWALL: DownloadStatus.PAYWALL,
    AccessDecision.CAPTCHA_REQUIRED: DownloadStatus.CAPTCHA_REQUIRED,
    AccessDecision.ACCESS_DENIED: DownloadStatus.ACCESS_DENIED,
}


def download_one(doi: str, output: Path, sources: ScholarlySources, *,
                 auth_headers: dict[str, str] | None = None,
                 cookies: dict[str, str] | None = None) -> DownloadResult:
    if sources.authorized:
        sources.session.headers.update(auth_headers or {})
        sources.session.cookies.update(cookies or {})
    try:
        discovered = sources.discover(doi)
    except UnsupportedSourceError as exc:
        return DownloadResult(doi, None, DownloadStatus.ACCESS_DENIED.value, message=str(exc))
    session = requests.Session()
    if cookies:
        session.cookies.update(cookies)
    destination = output / f"{doi_to_filename(doi)}.pdf"
    last_status = DownloadStatus.NOT_FOUND
    last_message = "No accessible full-text location was found."
    for candidate in discovered.candidates:
        if not candidate.is_open_access and not sources.authorized:
            continue
        status, message = download_pdf(
            session, candidate.url, destination, headers=auth_headers,
            timeout=sources.timeout, max_retries=sources.max_retries,
        )
        if status is None:
            downloaded = (DownloadStatus.DOWNLOADED_OA if candidate.is_open_access
                          else DownloadStatus.DOWNLOADED_AUTHORIZED)
            return DownloadResult(doi, discovered.title, downloaded.value,
                                  candidate.source, candidate.url, str(destination), None)
        last_status, last_message = status, message or status.value
        if status in {DownloadStatus.AUTH_REQUIRED, DownloadStatus.PAYWALL,
                      DownloadStatus.CAPTCHA_REQUIRED, DownloadStatus.ACCESS_DENIED}:
            continue
    if not discovered.candidates and discovered.restriction in _RESTRICTION_STATUS:
        last_status = _RESTRICTION_STATUS[discovered.restriction]
        last_message = f"Access stopped: {discovered.restriction.value}."
    elif not discovered.candidates and discovered.restriction is None:
        last_status = DownloadStatus.ACCESS_RESTRICTED
    return DownloadResult(doi, discovered.title, last_status.value, message=last_message)


def run_batch(dois: list[str], output: Path, sources: ScholarlySources, **kwargs) -> list[DownloadResult]:
    """Run conservatively and sequentially; source requests enforce one request per second."""
    output.mkdir(parents=True, exist_ok=True)
    return [download_one(doi, output, sources, **kwargs) for doi in dict.fromkeys(dois)]
