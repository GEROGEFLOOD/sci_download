# sci_download

`sci_download` is a Python command-line tool for discovering and downloading scientific
literature that is openly accessible or available through access rights explicitly provided
by the user.

Open-access discovery is the default. The downloader stops when it detects an access
restriction and returns a structured status instead of trying to circumvent the restriction.

## Discovery pipeline

For each DOI, the current v0.3.0 pipeline uses this order:

```text
DOI
  -> Crossref metadata
  -> Europe PMC / PMC
  -> Unpaywall
  -> OpenAlex
  -> explicit publisher Open Access PDF
  -> optional user-authorized access
```

Crossref provides bibliographic metadata. Europe PMC, PMC, Unpaywall, and OpenAlex provide
candidate full-text locations. A publisher PDF is downloaded by default only when the
publisher page explicitly indicates Open Access availability.

## Installation

Python 3.11 or later is required.

```bash
python -m pip install .
```

This installs both `sci-download` and the compatible `sci-dl` command name.

## Usage

Download one DOI:

```bash
sci-download 10.1234/example
```

Provide a contact email for scholarly APIs:

```bash
sci-download 10.1234/example --email researcher@example.org
```

Download DOI values from a UTF-8 text file:

```bash
sci-download --doi-file dois.txt --output ./papers
```

A DOI-list file can also be supplied as the positional argument:

```bash
sci-dl dois.txt --output-dir ./papers
```

Open-access-only behavior is the default. The explicit form is:

```bash
sci-download 10.1234/example --oa-only
```

Other current options:

```text
--version
--init-config
--show-config
```

Run `sci-download --help` for the complete argument list.

## User-authorized access

The application can use authentication material only when the user explicitly enables
authorized access and supplies that material:

```bash
sci-download 10.1234/example \
  --authorized-access \
  --cookie-file my_cookies.txt
```

```bash
sci-download 10.1234/example \
  --authorized-access \
  --header-file headers.json
```

Cookie files use Netscape cookie-file format. Header files are JSON objects containing string
keys and values. `--cookie-file` and `--header-file` are rejected unless
`--authorized-access` is also present.

Only use credentials or cookies for services you are authorized to access. The application
does not inspect browser profiles, extract credentials from other applications, or save
supplied credentials by default. Cookie, Authorization, token, and API-key values are
redacted from application error output.

## Result format

The command writes one JSON object per DOI. Each object contains:

```text
doi, title, status, source, url, file_path, message
```

Possible statuses are:

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

Downloaded files are validated using PDF magic bytes. An HTML login, payment, or challenge
page is not saved with a `.pdf` extension.

## Responsible request behavior

The default configuration uses:

- one request per second
- no more than three retries
- bounded exponential backoff
- `Retry-After` handling
- a clear `sci-dl` User-Agent with an optional contact email
- sequential batch processing

Configuration can be created and inspected with:

```bash
sci-download --init-config
sci-download --show-config
```

## Legal and responsible use

This project does not provide or facilitate access to Sci-Hub, LibGen, Anna's Archive, or
other unauthorized repositories.

It does not bypass paywalls, CAPTCHA systems, authentication requirements, Cloudflare
challenges, or other technical access controls.

When an access restriction is detected, the downloader stops and reports the restriction.

Users are responsible for ensuring they have permission to access and download content and
for complying with applicable licenses, terms of service, institutional policies, and laws.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```
