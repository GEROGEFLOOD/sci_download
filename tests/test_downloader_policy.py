import logging

from scidl.downloader import is_valid_pdf
from scidl.security import redact


def test_pdf_validation():
    assert is_valid_pdf(b"%PDF-1.7\n" + b"x" * 40, "application/pdf")
    assert not is_valid_pdf(b"<html>login required</html>", "application/pdf")


def test_credentials_are_redacted(caplog):
    with caplog.at_level(logging.INFO):
        logging.info(redact("Authorization: secret Cookie=session-value token=abc123"))
    assert "secret" not in caplog.text
    assert "session-value" not in caplog.text
    assert "abc123" not in caplog.text
