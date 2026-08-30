"""Command-line interface for open-access and user-authorized downloads."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from scidl import __version__
from scidl.config import config_path, load_config, write_template
from scidl.parser import looks_like_url
from scidl.runner import run_batch
from scidl.security import load_cookie_file, load_header_file, redact
from scidl.sources import ScholarlySources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sci-download",
        description="Download openly accessible or user-authorized scientific literature.",
    )
    parser.add_argument("doi", nargs="?", help="DOI or a legacy DOI-list file")
    parser.add_argument("--doi-file", help="UTF-8 file containing one DOI per line")
    parser.add_argument("-o", "--output", "--output-dir", default=None, help="output directory")
    parser.add_argument("--email", help="contact email for scholarly APIs")
    parser.add_argument("--oa-only", action="store_true", default=True,
                        help="use only open-access locations (default)")
    parser.add_argument("--authorized-access", action="store_true",
                        help="use credentials explicitly supplied by the user")
    parser.add_argument("--cookie-file", help="Netscape-format cookie file")
    parser.add_argument("--header-file", help="JSON object containing request headers")
    parser.add_argument("--version", action="version", version=f"sci-download {__version__}")
    parser.add_argument("--init-config", action="store_true")
    parser.add_argument("--show-config", action="store_true")
    return parser


def _read_lines(path: str) -> list[str]:
    return [line.strip() for line in Path(path).read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def _dois(args) -> list[str]:
    dois = _read_lines(args.doi_file) if args.doi_file else []
    if args.doi:
        if Path(args.doi).is_file() and not looks_like_url(args.doi):
            dois.extend(_read_lines(args.doi))
        else:
            dois.append(args.doi)
    return dois


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.init_config:
        print(write_template())
        return 0
    config = load_config()
    if args.show_config:
        print(f"Config: {config_path()}")
        print(json.dumps(config, indent=2))
        return 0
    dois = _dois(args)
    if not dois:
        build_parser().error("provide a DOI or --doi-file")

    if (args.cookie_file or args.header_file) and not args.authorized_access:
        build_parser().error("--cookie-file/--header-file require --authorized-access")
    try:
        headers = load_header_file(args.header_file) if args.authorized_access else {}
        cookies = load_cookie_file(args.cookie_file) if args.authorized_access else {}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Credential file error: {redact(exc)}", file=sys.stderr)
        return 2

    general = config["general"]
    output = Path(args.output or general["output_dir"] or "papers")
    sources = ScholarlySources(
        email=args.email or general["email"],
        requests_per_second=general["requests_per_second"],
        timeout=general["timeout"], max_retries=general["max_retries"],
        authorized=args.authorized_access,
    )
    results = run_batch(dois, output, sources, auth_headers=headers, cookies=cookies)
    for result in results:
        print(json.dumps(asdict(result), ensure_ascii=False))
    failures = {"NETWORK_ERROR", "INVALID_PDF"}
    return 1 if any(result.status in failures for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
