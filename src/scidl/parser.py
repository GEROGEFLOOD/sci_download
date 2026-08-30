"""任务列表解析：DOI / 标识符 / 完整 URL 混合输入 → DownloadTask。

迁移自旧版 parallel_downloader_gui.py 的纯函数，行为保持一致：
- 每行一个任务，空行与 # 注释跳过
- 支持 `source|filename` 或 CSV `source,filename` 指定文件名
- 完整 URL 直通；非 URL 用 base_url + template 拼接
"""

import csv
import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional


@dataclass
class DownloadTask:
    source: str
    url: str
    filename: Optional[str] = None


def looks_like_url(value: str) -> bool:
    return bool(re.match(r"^https?://", value.strip(), re.I))


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.strip()
    if not base_url:
        raise ValueError("Base URL is required when a task line is not a full URL.")
    if not looks_like_url(base_url):
        raise ValueError("Base URL must start with http:// or https://.")
    return base_url.rstrip("/")


def build_url(base_url: str, template: str, identifier: str) -> str:
    """标识符 → URL。模板可用 {base}、{id}(编码后)、{raw}(原文)。"""
    template = template.strip() or "{base}/{id}"
    encoded = urllib.parse.quote(identifier.strip(), safe="/")
    return template.format(base=normalize_base_url(base_url), id=encoded, raw=identifier.strip())


def safe_filename(name: str) -> str:
    name = urllib.parse.unquote(name)
    name = name.replace("/", "_").replace("\\", "_")
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "download"


def doi_to_filename(doi: str) -> str:
    """DOI → 文件名（不含扩展名）。/ 转 _，括号保留（文件名合法字符）。"""
    return safe_filename(doi.strip())


def split_task_line(line: str) -> tuple[str, Optional[str]]:
    line = line.strip()
    if "," in line:
        parts = next(csv.reader([line]))
        if len(parts) >= 2 and parts[1].strip():
            return parts[0].strip(), parts[1].strip()
    if "|" in line:
        left, right = line.split("|", 1)
        if right.strip():
            return left.strip(), right.strip()
        return left.strip(), None
    return line, None


def parse_doi_lines(lines: list[str]) -> list[DownloadTask]:
    """DOI 列表模式：不拼接 URL，source 即标识符（下载源链自行编码）。"""
    tasks: list[DownloadTask] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        source, filename = split_task_line(line)
        if not source:
            continue
        tasks.append(
            DownloadTask(
                source=source,
                url=source,
                filename=safe_filename(filename) if filename else None,
            )
        )
    return tasks


def parse_tasks(lines: list[str], base_url: str, template: str) -> list[DownloadTask]:
    tasks: list[DownloadTask] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        source, filename = split_task_line(line)
        if not source:
            continue
        url = source if looks_like_url(source) else build_url(base_url, template, source)
        tasks.append(
            DownloadTask(
                source=source,
                url=url,
                filename=safe_filename(filename) if filename else None,
            )
        )
    return tasks
