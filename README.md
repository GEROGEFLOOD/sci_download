# sci_download

A command-line tool for downloading scientific literature that is openly accessible or
available through access rights provided by the user.

## Sources

The downloader resolves a DOI through:

1. Crossref metadata
2. Europe PMC / PMC
3. Unpaywall
4. OpenAlex
5. Publisher-provided Open Access PDFs

Open Access is used by default.

## Install

```bash
python -m pip install .
```

## Usage

Download one DOI:

```bash
sci-download 10.1234/example --email researcher@example.org
```

Download a DOI list:

```bash
sci-download --doi-file dois.txt --output ./papers
```

The `sci-dl` command name is also supported.

## Authorized access

Users may explicitly provide credentials for services they are authorized to access:

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

Only use credentials or cookies for services you are authorized to access.

## Responsible use

This project does not provide or facilitate access to Sci-Hub, LibGen, Anna's Archive, or
other unauthorized repositories.

It does not bypass paywalls, CAPTCHA systems, authentication requirements, Cloudflare
challenges, or other access controls. When a restriction is detected, the downloader stops
and reports it.
