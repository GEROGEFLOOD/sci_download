"""Classify access restrictions without attempting to circumvent them."""

from enum import Enum
from urllib.parse import urlparse


class AccessDecision(str, Enum):
    ALLOW = "allow"
    AUTH_REQUIRED = "auth_required"
    PAYWALL = "paywall"
    CAPTCHA_REQUIRED = "captcha_required"
    ACCESS_DENIED = "access_denied"
    UNKNOWN = "unknown"


_CAPTCHA_MARKERS = (
    "captcha", "turnstile", "cf-chl-", "verify you are human",
    "checking your browser", "just a moment",
)
_PAYWALL_MARKERS = (
    "purchase article", "buy this article", "subscribe to read",
    "rent this article", "access options", "payment required",
)
_AUTH_MARKERS = (
    "institutional login", "institution login", "log in through your institution",
    "sign in to access", "login required", "authentication required",
)


def evaluate_response(response) -> AccessDecision:
    """Return a restriction decision using status, redirect URL and a small body sample."""
    status = int(getattr(response, "status_code", 0) or 0)
    if status == 401:
        return AccessDecision.AUTH_REQUIRED
    if status == 402:
        return AccessDecision.PAYWALL

    url = str(getattr(response, "url", "") or "")
    path = urlparse(url).path.lower()
    if any(part in path for part in ("/login", "/signin", "/authenticate", "/sso/")):
        return AccessDecision.AUTH_REQUIRED

    content_type = str(getattr(response, "headers", {}).get("Content-Type", "")).lower()
    if "html" in content_type:
        text = str(getattr(response, "text", "") or "")[:262_144].lower()
        if any(marker in text for marker in _CAPTCHA_MARKERS):
            return AccessDecision.CAPTCHA_REQUIRED
        if any(marker in text for marker in _PAYWALL_MARKERS):
            return AccessDecision.PAYWALL
        if any(marker in text for marker in _AUTH_MARKERS):
            return AccessDecision.AUTH_REQUIRED
    if status >= 400:
        return AccessDecision.ACCESS_DENIED
    if "html" not in content_type:
        return AccessDecision.ALLOW
    return AccessDecision.UNKNOWN


class UnsupportedSourceError(ValueError):
    pass


def reject_unsupported_url(url: str) -> None:
    """Reject known unauthorized repository hosts without contacting them."""
    compact = url.lower().replace("-", "").replace("_", "").replace(".", "")
    blocked = ("scihub", "libgen", "annasarchive")
    if any(name in compact for name in blocked):
        raise UnsupportedSourceError(
            "This source is disabled for legal and compliance reasons."
        )
