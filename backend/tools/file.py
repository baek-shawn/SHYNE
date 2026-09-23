"""파일 도구: list_files, read_file, write_file, edit_file.

모든 경로는 `base_dir`(Agent가 작업하는 프로젝트 루트) 기준으로 해석하고, `base_dir` 밖으로
나가는 경로는 거부한다. Step 4(Tool Permission)가 생기기 전까지의 최소 안전장치다.
"""

from __future__ import annotations

import locale
import os
from pathlib import Path

from tools.registry import ToolResult

# 재귀 탐색/검색에서 내려가지 않는 디렉터리 (search.py도 함께 사용).
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
}

MAX_LIST_ENTRIES = 500
MAX_READ_CHARS = 30_000


class ToolInputError(Exception):
    """LLM이 보낸 Tool 인자가 잘못됐을 때 사용한다. 메시지는 그대로 LLM에 전달된다."""


def resolve_path(base_dir: Path, raw_path: object) -> Path:
    """raw_path를 base_dir 기준 절대 경로로 바꾼다. base_dir 밖이면 ToolInputError."""
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ToolInputError("path는 비어 있지 않은 문자열이어야 합니다.")
    root = Path(base_dir).resolve()
    # resolve()가 `..`와 심볼릭 링크를 모두 풀어주므로, 그 결과가 root 하위인지만 보면 된다.
    resolved = (root / raw_path).resolve()
    if not resolved.is_relative_to(root):
        raise ToolInputError(f"작업 디렉터리 밖의 경로에는 접근할 수 없습니다: {raw_path}")
    return resolved


def relative_display(base_dir: Path, path: Path) -> str:
    """LLM에 보여줄 경로 표기: base_dir 기준 상대 경로, 구분자는 항상 `/`."""
    relative = path.relative_to(Path(base_dir).resolve()).as_posix()
    return relative or "."


def decode_bytes(data: bytes) -> tuple[str, str]:
    """바이트를 텍스트로 바꾸고 (텍스트, 사용한 인코딩)을 돌려준다.

    UTF-8을 먼저 시도하고, 실패하면 OS 기본 인코딩(한국어 Windows라면 cp949)으로 시도한다.
    """
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8-sig"
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    fallback = locale.getpreferredencoding(False)
    try:
        return data.decode(fallback), fallback
    except (UnicodeDecodeError, LookupError):
        raise ToolInputError("파일 인코딩을 해석할 수 없습니다 (UTF-8 텍스트 파일이 아닙니다).")


def _load_text_file(base_dir: Path, path: Path) -> tuple[str, str]:
    """텍스트 파일을 읽어 (원본 줄바꿈이 유지된 텍스트, 인코딩)을 돌려준다."""
    display = relative_display(base_dir, path)
    if not path.exists():
        raise ToolInputError(f"파일이 없습니다: {display}")
    if path.is_dir():
        raise ToolInputError(f"파일이 아니라 디렉터리입니다: {display} (list_files를 사용하세요)")
    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        raise ToolInputError(f"바이너리 파일은 읽을 수 없습니다: {display}")
    return decode_bytes(data)


def _optional_int(arguments: dict, key: str) -> int | None:
    value = arguments.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolInputError(f"{key}는 정수여야 합니다.")


def list_files(arguments: dict, *, base_dir: Path) -> ToolResult:
    try:
        target = resolve_path(base_dir, arguments.get("path", "."))
    except ToolInputError as exc:
        return ToolResult(False, "", str(exc))

    display = relative_display(base_dir, target)
    if not target.exists():
        return ToolResult(False, "", f"경로가 없습니다: {display}")
    if not target.is_dir():
        return ToolResult(False, "", f"디렉터리가 아닙니다: {display}")

    entries: list[str] = []
    if arguments.get("recursive"):
        for current, dirnames, filenames in os.walk(target):
            dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS)
            current_path = Path(current)
            entries.extend(relative_display(base_dir, current_path / name) + "/" for name in dirnames)
            entries.extend(relative_display(base_dir, current_path / name) for name in sorted(filenames))
        entries.sort()
    else:
        children = sorted(target.iterdir(), key=lambda child: (child.is_file(), child.name.lower()))
        for child in children:
            suffix = "/" if child.is_dir() else ""
            entries.append(relative_display(base_dir, child) + suffix)

    if not entries:
        return ToolResult(True, "(빈 디렉터리)")

    lines = entries[:MAX_LIST_ENTRIES]
    if len(entries) > MAX_LIST_ENTRIES:
        lines.append(f"[... 항목이 많아 {MAX_LIST_ENTRIES}개까지만 표시했습니다. 전체 {len(entries)}개]")
    return ToolResult(True, "\n".join(lines))


def read_file(arguments: dict, *, base_dir: Path) -> ToolResult:
    try:
        path = resolve_path(base_dir, arguments.get("path"))
        raw_text, _encoding = _load_text_file(base_dir, path)
        start_line = _optional_int(arguments, "start_line")
        end_line = _optional_int(arguments, "end_line")
    except ToolInputError as exc:
        return ToolResult(False, "", str(exc))

    # LLM에는 항상 `\n` 줄바꿈으로 보여준다 (edit_file도 같은 기준으로 비교한다).
    text = raw_text.replace("\r\n", "\n")
    lines = text.splitlines(keepends=True)
    total_lines = len(lines)

    if start_line is not None or end_line is not None:
        start = start_line if start_line is not None else 1
        end = end_line if end_line is not None else total_lines
        if start < 1 or end < start:
            return ToolResult(False, "", "start_line은 1 이상, end_line은 start_line 이상이어야 합니다.")
        if start > total_lines:
            return ToolResult(False, "", f"start_line({start})이 파일 전체 줄 수({total_lines})보다 큽니다.")
        text = "".join(lines[start - 1 : end])

    if not text:
        return ToolResult(True, "(빈 파일)")

    if len(text) > MAX_READ_CHARS:
        text = (
            text[:MAX_READ_CHARS]
            + f"\n[... 내용이 길어 {MAX_READ_CHARS}자에서 잘랐습니다. 전체 {total_lines}줄이며,"
            " start_line/end_line으로 나눠서 읽으세요.]"
        )
    return ToolResult(True, text)


def write_file(arguments: dict, *, base_dir: Path) -> ToolResult:
    try:
        path = resolve_path(base_dir, arguments.get("path"))
    except ToolInputError as exc:
        return ToolResult(False, "", str(exc))

    content = arguments.get("content")
    if not isinstance(content, str):
        return ToolResult(False, "", "content는 문자열이어야 합니다.")

    display = relative_display(base_dir, path)
    if path.is_dir():
        return ToolResult(False, "", f"같은 이름의 디렉터리가 이미 있습니다: {display}")

    existed = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline=""으로 LLM이 보낸 줄바꿈을 그대로 기록한다 (Windows의 자동 \r\n 변환 방지).
    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(content)

    action = "덮어썼습니다" if existed else "생성했습니다"
    line_count = len(content.splitlines())
    return ToolResult(True, f"파일을 {action}: {display} ({line_count}줄)")


def edit_file(arguments: dict, *, base_dir: Path) -> ToolResult:
    try:
        path = resolve_path(base_dir, arguments.get("path"))
        raw_text, encoding = _load_text_file(base_dir, path)
    except ToolInputError as exc:
        return ToolResult(False, "", str(exc))

    old_string = arguments.get("old_string")
    new_string = arguments.get("new_string")
    if not isinstance(old_string, str) or not isinstance(new_string, str):
        return ToolResult(False, "", "old_string과 new_string은 문자열이어야 합니다.")
    if not old_string:
        return ToolResult(False, "", "old_string이 비어 있습니다. 새 파일은 write_file로 만드세요.")
    if old_string == new_string:
        return ToolResult(False, "", "old_string과 new_string이 같아서 바꿀 내용이 없습니다.")

    # read_file이 보여준 것과 같은 `\n` 기준으로 비교하고, 저장할 때 원래 줄바꿈으로 되돌린다.
    uses_crlf = "\r\n" in raw_text
    text = raw_text.replace("\r\n", "\n")
    old_string = old_string.replace("\r\n", "\n")
    new_string = new_string.replace("\r\n", "\n")

    display = relative_display(base_dir, path)
    count = text.count(old_string)
    if count == 0:
        return ToolResult(
            False,
            "",
            f"{display}에서 old_string을 찾지 못했습니다. read_file로 실제 내용을 확인하고"
            " 공백/들여쓰기까지 정확히 일치시키세요.",
        )

    replace_all = bool(arguments.get("replace_all"))
    if count > 1 and not replace_all:
        return ToolResult(
            False,
            "",
            f"old_string이 {display}에서 {count}번 나옵니다. 주변 줄을 더 포함해 한 곳만"
            " 가리키게 하거나 replace_all을 true로 지정하세요.",
        )

    new_text = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
    if uses_crlf:
        new_text = new_text.replace("\n", "\r\n")
    with path.open("w", encoding=encoding, newline="") as file:
        file.write(new_text)

    replaced = count if replace_all else 1
    return ToolResult(True, f"파일을 수정했습니다: {display} ({replaced}곳 교체)")
