"""Policy-aware PDF download primitives."""

import os
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

from scidl.access_policy import AccessDecision, evaluate_response, reject_unsupported_url
from scidl.models import DownloadStatus

MIN_PDF_SIZE = 32


def is_valid_pdf(data: bytes, content_type: str | None = None) -> bool:
    """Validate magic bytes; Content-Type is advisory because servers may mislabel PDFs."""
    return len(data) >= MIN_PDF_SIZE and data.lstrip()[:4] == b"%PDF"


def is_pdf_head(data: bytes) -> bool:
    return data.lstrip()[:4] == b"%PDF"


def _retry_after_seconds(value: str | None, default: float) -> float:
    if not value:
        return default
    try:
        return max(0.0, min(120.0, float(value)))
    except ValueError:
        try:
            return max(0.0, min(120.0, parsedate_to_datetime(value).timestamp() - time.time()))
        except (TypeError, ValueError):
            return default


def decision_to_status(decision: AccessDecision) -> DownloadStatus:
    return {
        AccessDecision.AUTH_REQUIRED: DownloadStatus.AUTH_REQUIRED,
        AccessDecision.PAYWALL: DownloadStatus.PAYWALL,
        AccessDecision.CAPTCHA_REQUIRED: DownloadStatus.CAPTCHA_REQUIRED,
        AccessDecision.ACCESS_DENIED: DownloadStatus.ACCESS_DENIED,
        AccessDecision.UNKNOWN: DownloadStatus.INVALID_PDF,
        AccessDecision.ALLOW: DownloadStatus.INVALID_PDF,
    }[decision]


def download_pdf(session: requests.Session, url: str, destination: Path, *,
                 headers: dict[str, str] | None = None, timeout: int = 45,
                 max_retries: int = 3) -> tuple[DownloadStatus | None, str | None]:
    """Download a PDF or return a terminal status; never bypass restrictions."""
    reject_unsupported_url(url)
    part = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        except requests.RequestException as exc:
            if attempt + 1 == max_retries:
                return DownloadStatus.NETWORK_ERROR, str(exc)
            time.sleep(2**attempt)
            continue
        if response.status_code == 429 or response.status_code >= 500:
            if attempt + 1 < max_retries:
                time.sleep(_retry_after_seconds(response.headers.get("Retry-After"), 2**attempt))
                continue
            return DownloadStatus.NETWORK_ERROR, f"HTTP {response.status_code}"
        decision = evaluate_response(response)
        data = response.content
        if not is_valid_pdf(data, response.headers.get("Content-Type")):
            return decision_to_status(decision), f"response is not a valid PDF ({decision.value})"
        destination.parent.mkdir(parents=True, exist_ok=True)
        part.write_bytes(data)
        os.replace(part, destination)
        return None, None
    return DownloadStatus.NETWORK_ERROR, "request failed"
