"""Small, conservative configuration layer."""

import os
import sys
import tomllib
from copy import deepcopy
from pathlib import Path

DEFAULT_CONFIG = {"general": {"email": "", "max_concurrency": 2,
                  "requests_per_second": 1.0, "max_retries": 3,
                  "timeout": 45, "output_dir": ""}}

CONFIG_TEMPLATE = """\
# Contact email is used in polite API User-Agent strings and by Unpaywall.
[general]
email = ""
max_concurrency = 2
requests_per_second = 1.0
max_retries = 3
timeout = 45
output_dir = ""
"""


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "sci-dl"


def config_path() -> Path:
    return config_dir() / "config.toml"


def load_config(path: Path | None = None) -> dict:
    config = deepcopy(DEFAULT_CONFIG)
    path = path or config_path()
    if not path.exists():
        return config
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"[sci-dl] invalid config, using defaults: {exc}", file=sys.stderr)
        return config
    general = data.get("general", {})
    if isinstance(general, dict):
        for key, default in config["general"].items():
            value = general.get(key, default)
            if isinstance(value, type(default)) or (isinstance(default, float) and isinstance(value, int)):
                config["general"][key] = value
    config["general"]["max_concurrency"] = min(2, max(1, config["general"]["max_concurrency"]))
    config["general"]["max_retries"] = min(3, max(1, config["general"]["max_retries"]))
    config["general"]["requests_per_second"] = min(1.0, max(0.1, float(config["general"]["requests_per_second"])))
    return config


def write_template(path: Path | None = None) -> Path:
    path = path or config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    return path
