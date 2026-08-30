"""Credential loading and log redaction."""

import json
import re
from http.cookiejar import MozillaCookieJar
from pathlib import Path


_SENSITIVE = re.compile(
    r"(?i)(authorization|cookie|set-cookie|token|api[_-]?key)(\s*[:=]\s*)([^\s,;]+)"
)


def redact(text: object) -> str:
    return _SENSITIVE.sub(lambda m: f"{m.group(1)}{m.group(2)}***", str(text))


def load_header_file(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    valid = isinstance(data, dict) and all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    )
    if not valid:
        raise ValueError("header file must contain a JSON object of string values")
    return data


def load_cookie_file(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    jar = MozillaCookieJar(path)
    jar.load(ignore_discard=True, ignore_expires=True)
    return {cookie.name: cookie.value for cookie in jar}
