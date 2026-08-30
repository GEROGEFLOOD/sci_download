# sci_download

A command-line tool for discovering and downloading scientific literature that is openly
accessible or available through access rights provided by the user.

## Features

- DOI metadata resolution through Crossref and OpenAlex
- Open Access discovery through PMC, Europe PMC, Unpaywall, and OpenAlex
- Support for arXiv and other preprint or institutional-repository locations returned by
  trusted scholarly indexes
- Publisher-hosted Open Access PDFs
- Explicit user-authorized publisher access
- Structured results for access restrictions and download failures
- PDF magic-byte validation so HTML login pages are never saved as PDFs
- Conservative request rate, bounded exponential backoff, and `Retry-After` support

## Installation

```bash
python -m pip install .
```

## Usage

Download one DOI (Open Access is the default):

```bash
sci-download 10.1234/example --email researcher@example.org
```

Download a list:

```bash
sci-download --doi-file dois.txt --output ./papers --email researcher@example.org
```

The historical command remains available:

```bash
sci-dl dois.txt --output ./papers
```

### User-authorized access

Credentials are loaded only when `--authorized-access` is explicitly supplied:

```bash
sci-download 10.1234/example --authorized-access --cookie-file my_cookies.txt
sci-download 10.1234/example --authorized-access --header-file headers.json
```

Only use credentials or cookies for services you are authorized to access. Credential files
are not saved by the application, and Cookie, Authorization, and token values are redacted
from error output. The application does not inspect browser profiles or extract credentials
from other applications.

## Result statuses

Each DOI produces one JSON object with one of these statuses:

- `DOWNLOADED_OA`
- `DOWNLOADED_AUTHORIZED`
- `NOT_FOUND`
- `PAYWALL`
- `AUTH_REQUIRED`
- `CAPTCHA_REQUIRED`
- `ACCESS_DENIED`
- `ACCESS_RESTRICTED`
- `INVALID_PDF`
- `NETWORK_ERROR`

## Request behavior

Defaults are deliberately conservative:

- maximum concurrency: 2 (current batch implementation is sequential)
- requests per second: 1
- maximum retries: 3
- exponential backoff and `Retry-After` support
- clear `sci-dl` User-Agent with optional contact email

## Legal and responsible use

This project does not provide or facilitate access to Sci-Hub, LibGen, Anna's Archive, or
other unauthorized repositories.

The software does not bypass paywalls, CAPTCHA systems, authentication requirements,
Cloudflare challenges, or other access controls.

Users are responsible for ensuring they have permission to access and download content.

If authentication, payment, CAPTCHA, or another access restriction is encountered, the
downloader stops and reports the restriction instead of attempting to bypass it.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```
