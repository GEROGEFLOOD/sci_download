"""Public result models used by the downloader and CLI."""

from dataclasses import dataclass
from enum import Enum


class DownloadStatus(str, Enum):
    DOWNLOADED_OA = "DOWNLOADED_OA"
    DOWNLOADED_AUTHORIZED = "DOWNLOADED_AUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    PAYWALL = "PAYWALL"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    ACCESS_DENIED = "ACCESS_DENIED"
    ACCESS_RESTRICTED = "ACCESS_RESTRICTED"
    INVALID_PDF = "INVALID_PDF"
    NETWORK_ERROR = "NETWORK_ERROR"


@dataclass
class DownloadResult:
    doi: str
    title: str | None
    status: str
    source: str | None = None
    url: str | None = None
    file_path: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class PdfCandidate:
    source: str
    url: str
    is_open_access: bool = True
