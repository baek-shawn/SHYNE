"""Step 1 Tool 6종과 ToolRegistry 단위 테스트. LLM 없이 함수 단위로만 검증한다."""

import sys
import time

from tools.file import edit_file, list_files, read_file, write_file
from tools.registry import ToolRegistry, ToolResult, build_default_registry
from tools.search import search_files
from tools.shell import run_command

PYTHON = f'"{sys.executable}"'


# ---------------------------------------------------------------- list_files


def test_list_files_shows_directories_first(tmp_path):
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("a", encoding="utf-8")

    result = list_files({}, base_dir=tmp_path)

    assert result.ok
    assert result.output.splitlines() == ["src/", "b.txt"]


def test_list_files_recursive_skips_ignored_dirs(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("a", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x", encoding="utf-8")

    result = list_files({"path": ".", "recursive": True}, base_dir=tmp_path)

    assert result.ok
    assert result.output.splitlines() == ["src/", "src/a.py"]


def test_list_files_empty_and_missing(tmp_path):
    assert list_files({}, base_dir=tmp_path).output == "(빈 디렉터리)"

    missing = list_files({"path": "nope"}, base_dir=tmp_path)
    assert not missing.ok
    assert "경로가 없습니다" in missing.error


def test_paths_outside_base_dir_are_rejected(tmp_path):
    base_dir = tmp_path / "project"
    base_dir.mkdir()
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")

    for result in (
        list_files({"path": ".."}, base_dir=base_dir),
        read_file({"path": "../secret.txt"}, base_dir=base_dir),
        read_file({"path": str(tmp_path / "secret.txt")}, base_dir=base_dir),
        write_file({"path": "../new.txt", "content": "x"}, base_dir=base_dir),
        edit_file({"path": "../secret.txt", "old_string": "secret", "new_string": "x"}, base_dir=base_dir),
        search_files({"pattern": "secret", "path": ".."}, base_dir=base_dir),
    ):
        assert not result.ok
        assert "작업 디렉터리 밖" in result.error

    assert not (tmp_path / "new.txt").exists()
    assert (tmp_path / "secret.txt").read_text(encoding="utf-8") == "secret"


# ----------------------------------------------------------------- read_file


def test_read_file_returns_content(tmp_path):
    (tmp_path / "hello.py").write_text("print('안녕')\n", encoding="utf-8")

    result = read_file({"path": "hello.py"}, base_dir=tmp_path)

    assert result.ok
    assert result.output == "print('안녕')\n"


def test_read_file_line_range(tmp_path):
    (tmp_path / "lines.txt").write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")

    result = read_file({"path": "lines.txt", "start_line": 2, "end_line": "3"}, base_dir=tmp_path)

    assert result.ok
    assert result.output == "two\nthree\n"


def test_read_file_errors(tmp_path):
    (tmp_path / "dir").mkdir()
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02")

    assert "파일이 없습니다" in read_file({"path": "missing.py"}, base_dir=tmp_path).error
    assert "디렉터리입니다" in read_file({"path": "dir"}, base_dir=tmp_path).error
    assert "바이너리" in read_file({"path": "binary.bin"}, base_dir=tmp_path).error


def test_read_file_normalizes_crlf(tmp_path):
    (tmp_path / "crlf.txt").write_bytes(b"a\r\nb\r\n")

    assert read_file({"path": "crlf.txt"}, base_dir=tmp_path).output == "a\nb\n"


# ---------------------------------------------------------------- write_file


def test_write_file_creates_parent_directories(tmp_path):
    result = write_file({"path": "pkg/sub/mod.py", "content": "x = 1\n"}, base_dir=tmp_path)

    assert result.ok
    assert "생성했습니다" in result.output
    assert (tmp_path / "pkg" / "sub" / "mod.py").read_bytes() == b"x = 1\n"


def test_write_file_overwrites(tmp_path):
    (tmp_path / "a.txt").write_text("old", encoding="utf-8")

    result = write_file({"path": "a.txt", "content": "new"}, base_dir=tmp_path)

    assert result.ok
    assert "덮어썼습니다" in result.output
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "new"


def test_write_file_requires_string_content(tmp_path):
    result = write_file({"path": "a.txt", "content": None}, base_dir=tmp_path)

    assert not result.ok
    assert not (tmp_path / "a.txt").exists()


# ----------------------------------------------------------------- edit_file


def test_edit_file_replaces_single_occurrence(tmp_path):
    (tmp_path / "test.py").write_text("print('hello'\n", encoding="utf-8")

    result = edit_file(
        {"path": "test.py", "old_string": "print('hello'", "new_string": "print('hello')"},
        base_dir=tmp_path,
    )

    assert result.ok
    assert (tmp_path / "test.py").read_text(encoding="utf-8") == "print('hello')\n"


def test_edit_file_not_found_leaves_file_untouched(tmp_path):
    (tmp_path / "test.py").write_text("x = 1\n", encoding="utf-8")

    result = edit_file({"path": "test.py", "old_string": "y = 2", "new_string": "y = 3"}, base_dir=tmp_path)

    assert not result.ok
    assert "찾지 못했습니다" in result.error
    assert (tmp_path / "test.py").read_text(encoding="utf-8") == "x = 1\n"


def test_edit_file_ambiguous_match_requires_replace_all(tmp_path):
    (tmp_path / "test.py").write_text("a = 1\na = 1\n", encoding="utf-8")

    ambiguous = edit_file({"path": "test.py", "old_string": "a = 1", "new_string": "a = 2"}, base_dir=tmp_path)
    assert not ambiguous.ok
    assert "2번" in ambiguous.error
    assert (tmp_path / "test.py").read_text(encoding="utf-8") == "a = 1\na = 1\n"

    replaced = edit_file(
        {"path": "test.py", "old_string": "a = 1", "new_string": "a = 2", "replace_all": True},
        base_dir=tmp_path,
    )
    assert replaced.ok
    assert (tmp_path / "test.py").read_text(encoding="utf-8") == "a = 2\na = 2\n"


def test_edit_file_preserves_crlf_line_endings(tmp_path):
    (tmp_path / "crlf.py").write_bytes(b"a = 1\r\nb = 2\r\n")

    result = edit_file(
        {"path": "crlf.py", "old_string": "a = 1\nb = 2", "new_string": "a = 1\nb = 3"},
        base_dir=tmp_path,
    )

    assert result.ok
    assert (tmp_path / "crlf.py").read_bytes() == b"a = 1\r\nb = 3\r\n"


def test_edit_file_rejects_empty_or_identical_strings(tmp_path):
    (tmp_path / "test.py").write_text("x = 1\n", encoding="utf-8")

    assert not edit_file({"path": "test.py", "old_string": "", "new_string": "x"}, base_dir=tmp_path).ok
    assert not edit_file({"path": "test.py", "old_string": "x", "new_string": "x"}, base_dir=tmp_path).ok
    assert not edit_file({"path": "missing.py", "old_string": "x", "new_string": "y"}, base_dir=tmp_path).ok


# -------------------------------------------------------------- search_files


def _make_search_project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def main():\n    return compute_total(1)\n", encoding="utf-8")
    (tmp_path / "src" / "notes.md").write_text("compute_total 설명\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib.py").write_text("compute_total = None\n", encoding="utf-8")


def test_search_files_content(tmp_path):
    _make_search_project(tmp_path)

    result = search_files({"pattern": "compute_total"}, base_dir=tmp_path)

    assert result.ok
    assert result.output.splitlines() == [
        "src/app.py:2: return compute_total(1)",
        "src/notes.md:1: compute_total 설명",
    ]


def test_search_files_glob_and_filename_mode(tmp_path):
    _make_search_project(tmp_path)

    only_python = search_files({"pattern": "compute_total", "file_glob": "*.py"}, base_dir=tmp_path)
    assert only_python.output.splitlines() == ["src/app.py:2: return compute_total(1)"]

    by_name = search_files({"pattern": "APP", "mode": "filename"}, base_dir=tmp_path)
    assert by_name.output == "일치하는 결과가 없습니다."  # 대문자가 있으면 대소문자를 구분한다

    by_name = search_files({"pattern": r"app\.py$", "mode": "filename"}, base_dir=tmp_path)
    assert by_name.output.splitlines() == ["src/app.py"]


def test_search_files_no_match_is_not_an_error(tmp_path):
    _make_search_project(tmp_path)

    result = search_files({"pattern": "does_not_exist"}, base_dir=tmp_path)

    assert result.ok
    assert result.output == "일치하는 결과가 없습니다."


def test_search_files_invalid_regex_falls_back_to_literal(tmp_path):
    (tmp_path / "a.py").write_text("print(\n", encoding="utf-8")

    result = search_files({"pattern": "print("}, base_dir=tmp_path)

    assert result.ok
    assert result.output == "a.py:1: print("


# --------------------------------------------------------------- run_command


def test_run_command_success_runs_in_base_dir(tmp_path):
    (tmp_path / "hello.py").write_text("print('hello world')\n", encoding="utf-8")

    result = run_command({"command": f"{PYTHON} hello.py"}, base_dir=tmp_path, timeout=30)

    assert result.ok
    assert "exit_code: 0" in result.output
    assert "hello world" in result.output


def test_run_command_failure_reports_exit_code_and_stderr(tmp_path):
    (tmp_path / "broken.py").write_text("print('hello'\n", encoding="utf-8")

    result = run_command({"command": f"{PYTHON} broken.py"}, base_dir=tmp_path, timeout=30)

    assert not result.ok
    assert "exit_code: 1" in result.output
    assert "SyntaxError" in result.output
    assert "종료 코드 1" in result.error


def test_run_command_handles_non_ascii_output(tmp_path):
    (tmp_path / "unicode.py").write_text("print('완료 ✅')\n", encoding="utf-8")

    result = run_command({"command": f"{PYTHON} unicode.py"}, base_dir=tmp_path, timeout=30)

    assert result.ok
    assert "완료 ✅" in result.output


def test_run_command_timeout_kills_the_command(tmp_path):
    (tmp_path / "slow.py").write_text("import time\nprint('start', flush=True)\ntime.sleep(30)\n", encoding="utf-8")

    started = time.monotonic()
    result = run_command({"command": f"{PYTHON} slow.py"}, base_dir=tmp_path, timeout=1)
    elapsed = time.monotonic() - started

    assert not result.ok
    assert "1초 안에 끝나지 않아" in result.error
    assert "start" in result.output  # 종료 전까지의 출력은 보존한다
    assert elapsed < 15


def test_run_command_requires_command(tmp_path):
    assert not run_command({"command": "  "}, base_dir=tmp_path).ok


# ------------------------------------------------------------------ registry


def test_default_registry_exposes_six_tools_as_openai_schemas(tmp_path):
    registry = build_default_registry(tmp_path)

    schemas = registry.get_schemas()

    assert [schema["function"]["name"] for schema in schemas] == [
        "list_files",
        "read_file",
        "search_files",
        "write_file",
        "edit_file",
        "run_command",
    ]
    for schema in schemas:
        assert schema["type"] == "function"
        assert schema["function"]["description"]
        assert schema["function"]["parameters"]["type"] == "object"


def test_registry_execute_reports_bad_calls_as_results(tmp_path):
    registry = build_default_registry(tmp_path)

    unknown = registry.execute("delete_everything", {})
    assert not unknown.ok
    assert "알 수 없는 Tool" in unknown.error

    missing = registry.execute("write_file", {"path": "a.txt"})
    assert not missing.ok
    assert "content" in missing.error

    not_a_dict = registry.execute("read_file", "a.txt")
    assert not not_a_dict.ok


def test_registry_execute_catches_tool_exceptions(tmp_path):
    def broken_tool(arguments, *, base_dir):
        raise RuntimeError("boom")

    registry = ToolRegistry(tmp_path)
    registry.register("broken", "항상 실패", {"type": "object", "properties": {}, "required": []}, broken_tool)

    result = registry.execute("broken", {})

    assert not result.ok
    assert "RuntimeError: boom" in result.error


def test_registry_passes_command_timeout_only_to_tools_that_accept_it(tmp_path):
    received = {}

    def with_timeout(arguments, *, base_dir, timeout=60):
        received["timeout"] = timeout
        return ToolResult(True, "ok")

    def without_timeout(arguments, *, base_dir):
        received["base_dir"] = base_dir
        return ToolResult(True, "ok")

    schema = {"type": "object", "properties": {}, "required": []}
    registry = ToolRegistry(tmp_path)
    registry.register("with_timeout", "t", schema, with_timeout)
    registry.register("without_timeout", "t", schema, without_timeout)

    assert registry.execute("with_timeout", {}, command_timeout=7).ok
    assert registry.execute("without_timeout", {}, command_timeout=7).ok
    assert received == {"timeout": 7, "base_dir": tmp_path.resolve()}


def test_tool_result_as_text():
    assert ToolResult(True, "내용").as_text() == "내용"
    assert ToolResult(False, "", "실패").as_text() == "[오류] 실패"
    assert ToolResult(False, "exit_code: 1", "실패").as_text() == "[오류] 실패\nexit_code: 1"
