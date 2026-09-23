"""검색 도구: search_files.

`mode="content"`(기본)는 파일 내용을, `mode="filename"`은 파일 경로를 정규식으로 검색한다.
"""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path

from tools.file import IGNORED_DIRS, ToolInputError, decode_bytes, relative_display, resolve_path
from tools.registry import ToolResult

MAX_MATCHES = 100
MAX_FILE_BYTES = 1_000_000
MAX_LINE_CHARS = 300


def _compile_pattern(pattern: str) -> re.Pattern[str]:
    # ripgrep의 smart-case와 같은 규칙: 패턴에 대문자가 없으면 대소문자를 구분하지 않는다.
    flags = 0 if any(char.isupper() for char in pattern) else re.IGNORECASE
    try:
        return re.compile(pattern, flags)
    except re.error:
        # LLM이 `print(` 같은 일반 문자열을 그대로 보내는 경우가 많아, 정규식으로 해석할 수
        # 없으면 문자 그대로 검색한다.
        return re.compile(re.escape(pattern), flags)


def _iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS)
        for name in sorted(filenames):
            yield Path(current) / name


def search_files(arguments: dict, *, base_dir: Path) -> ToolResult:
    pattern = arguments.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        return ToolResult(False, "", "pattern은 비어 있지 않은 문자열이어야 합니다.")

    mode = arguments.get("mode") or "content"
    if mode not in ("content", "filename"):
        return ToolResult(False, "", 'mode는 "content" 또는 "filename"이어야 합니다.')

    try:
        root = resolve_path(base_dir, arguments.get("path", "."))
    except ToolInputError as exc:
        return ToolResult(False, "", str(exc))
    if not root.exists():
        return ToolResult(False, "", f"경로가 없습니다: {relative_display(base_dir, root)}")

    file_glob = arguments.get("file_glob")
    regex = _compile_pattern(pattern)
    matches: list[str] = []
    truncated = False

    for path in _iter_files(root):
        if file_glob and not fnmatch.fnmatch(path.name, file_glob):
            continue
        display = relative_display(base_dir, path)

        if mode == "filename":
            if regex.search(display):
                matches.append(display)
        else:
            matches.extend(_search_content(path, display, regex))

        if len(matches) >= MAX_MATCHES:
            truncated = True
            break

    if not matches:
        return ToolResult(True, "일치하는 결과가 없습니다.")

    lines = matches[:MAX_MATCHES]
    if truncated:
        lines.append(f"[... 결과가 많아 {MAX_MATCHES}개까지만 표시했습니다. 검색 범위를 좁혀보세요.]")
    return ToolResult(True, "\n".join(lines))


def _search_content(path: Path, display: str, regex: re.Pattern[str]) -> list[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return []
        data = path.read_bytes()
    except OSError:
        return []
    if b"\x00" in data[:8192]:
        return []
    try:
        text, _encoding = decode_bytes(data)
    except ToolInputError:
        return []

    results = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if regex.search(line):
            results.append(f"{display}:{line_number}: {line.strip()[:MAX_LINE_CHARS]}")
    return results
