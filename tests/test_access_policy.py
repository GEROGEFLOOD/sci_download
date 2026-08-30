from types import SimpleNamespace

from scidl.access_policy import AccessDecision, UnsupportedSourceError, evaluate_response, reject_unsupported_url


def response(status=200, text="", content_type="text/html", url="https://example.org/article"):
    return SimpleNamespace(status_code=status, text=text, headers={"Content-Type": content_type}, url=url)


def test_restriction_statuses():
    assert evaluate_response(response(401)) is AccessDecision.AUTH_REQUIRED
    assert evaluate_response(response(403)) is AccessDecision.ACCESS_DENIED
    assert evaluate_response(response(text="purchase article")) is AccessDecision.PAYWALL
    assert evaluate_response(response(text="please complete the CAPTCHA")) is AccessDecision.CAPTCHA_REQUIRED


def test_unauthorized_repository_is_rejected_without_request():
    try:
        reject_unsupported_url("https://sci-hub.example/10.1/test")
    except UnsupportedSourceError:
        pass
    else:
        raise AssertionError("source must be rejected")
