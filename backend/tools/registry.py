"""Tool Registry.

책임: 도구 이름 -> 실행 함수, 그리고 LLM에 전달할 도구 설명/JSON 스키마를 한 곳에서 관리한다.
Agent Loop는 이 Registry를 통해서만 도구를 호출한다.

모든 Tool 함수는 `(arguments: dict, *, base_dir: Path) -> ToolResult` 시그니처를 따른다.
`run_command`처럼 `timeout` 키워드 인자를 추가로 받는 Tool에는 `execute()`의
`command_timeout` 값이 전달된다.

Step 4(Tool Permission)에서 AUTO/CONFIRM/BLOCK 등급을 이 Registry의 `execute()`에 연결할 예정이다.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class ToolResult:
    ok: bool
    output: str
    error: str | None = None

    def as_text(self) -> str:
        """LLM에 돌려줄 Tool 결과 문자열. 실패했으면 오류 설명을 맨 앞에 붙인다."""
        if self.ok:
            return self.output
        if self.output:
            return f"[오류] {self.error}\n{self.output}"
        return f"[오류] {self.error}"


@dataclass
class _RegisteredTool:
    name: str
    description: str
    parameters: dict
    fn: Callable[..., ToolResult]
    accepts_timeout: bool


class ToolRegistry:
    def __init__(self, base_dir: Path):
        # Agent가 작업할 프로젝트 루트. 모든 Tool은 이 디렉터리 하위만 접근한다.
        self.base_dir = Path(base_dir).resolve()
        self._tools: dict[str, _RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        fn: Callable[..., ToolResult],
    ) -> None:
        accepts_timeout = "timeout" in inspect.signature(fn).parameters
        self._tools[name] = _RegisteredTool(name, description, parameters, fn, accepts_timeout)

    def names(self) -> list[str]:
        return list(self._tools)

    def get_schemas(self) -> list[dict]:
        """LLM에 전달할 OpenAI tool 스키마 리스트."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: dict,
        *,
        command_timeout: int | None = None,
    ) -> ToolResult:
        """Tool을 실행한다. 어떤 실패든 예외 대신 ToolResult(ok=False)로 돌려준다.

        LLM이 없는 Tool 이름이나 잘못된 인자를 보내는 일은 흔하므로, 그 오류 내용을 LLM이 읽고
        스스로 고칠 수 있게 메시지로 돌려주는 것이 목적이다.
        """
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(self._tools)
            return ToolResult(False, "", f"알 수 없는 Tool입니다: {name}. 사용 가능한 Tool: {available}")

        if not isinstance(arguments, dict):
            return ToolResult(False, "", "Tool 인자는 JSON 객체여야 합니다.")

        missing = [key for key in tool.parameters.get("required", []) if key not in arguments]
        if missing:
            return ToolResult(False, "", f"필수 인자가 없습니다: {', '.join(missing)}")

        kwargs: dict = {"base_dir": self.base_dir}
        if tool.accepts_timeout and command_timeout is not None:
            kwargs["timeout"] = command_timeout

        try:
            return tool.fn(arguments, **kwargs)
        except Exception as exc:  # Tool 내부 버그가 Agent Loop 전체를 죽이지 않게 한다.
            return ToolResult(False, "", f"Tool 실행 중 예외가 발생했습니다: {type(exc).__name__}: {exc}")


def build_default_registry(base_dir: Path) -> ToolRegistry:
    """Step 1의 기본 Tool 6종을 등록한 Registry를 만든다. 새 Tool은 여기에 추가한다."""
    # tools.file 등이 이 모듈의 ToolResult를 import하므로, 순환 import를 피하려고 함수 안에서 불러온다.
    from tools.file import edit_file, list_files, read_file, write_file
    from tools.search import search_files
    from tools.shell import run_command

    registry = ToolRegistry(base_dir)

    registry.register(
        "list_files",
        "디렉터리 안의 파일과 하위 디렉터리 목록을 보여준다. 디렉터리는 이름 끝에 `/`가 붙는다.",
        {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "작업 디렉터리 기준 상대 경로. 생략하면 작업 디렉터리(`.`).",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "true면 하위 디렉터리까지 모두 나열한다 (.git, .venv 등은 제외). 기본값 false.",
                },
            },
            "required": [],
        },
        list_files,
    )

    registry.register(
        "read_file",
        "텍스트 파일의 내용을 읽는다. 파일을 수정하기 전에는 반드시 먼저 읽어서 실제 내용을 확인한다.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "읽을 파일의 상대 경로."},
                "start_line": {
                    "type": "integer",
                    "description": "읽기 시작할 줄 번호(1부터). 큰 파일을 나눠 읽을 때만 사용한다.",
                },
                "end_line": {
                    "type": "integer",
                    "description": "마지막으로 읽을 줄 번호(포함). 큰 파일을 나눠 읽을 때만 사용한다.",
                },
            },
            "required": ["path"],
        },
        read_file,
    )

    registry.register(
        "search_files",
        "작업 디렉터리에서 정규식으로 파일 내용 또는 파일 이름을 검색한다."
        ' 내용 검색 결과는 "경로:줄번호: 내용" 형식이다.',
        {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "검색할 정규식 또는 문자열."},
                "path": {
                    "type": "string",
                    "description": "검색을 시작할 디렉터리 또는 파일의 상대 경로. 생략하면 작업 디렉터리 전체.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["content", "filename"],
                    "description": "content는 파일 내용, filename은 파일 경로에서 찾는다. 기본값 content.",
                },
                "file_glob": {
                    "type": "string",
                    "description": "검색할 파일 이름 패턴. 예: `*.py`",
                },
            },
            "required": ["pattern"],
        },
        search_files,
    )

    registry.register(
        "write_file",
        "파일 전체 내용을 새로 쓴다. 파일이 없으면 만들고(상위 디렉터리 포함) 있으면 덮어쓴다."
        " 기존 파일의 일부만 고칠 때는 edit_file을 사용한다.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "쓸 파일의 상대 경로."},
                "content": {"type": "string", "description": "파일에 기록할 전체 내용."},
            },
            "required": ["path", "content"],
        },
        write_file,
    )

    registry.register(
        "edit_file",
        "기존 파일에서 old_string을 찾아 new_string으로 바꾼다. old_string은 파일 내용과"
        " 공백/들여쓰기까지 정확히 일치해야 하고, 기본적으로 파일 안에서 한 번만 나와야 한다.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "수정할 파일의 상대 경로."},
                "old_string": {"type": "string", "description": "바꿀 대상인 기존 내용 (정확히 일치해야 함)."},
                "new_string": {"type": "string", "description": "대신 넣을 새 내용."},
                "replace_all": {
                    "type": "boolean",
                    "description": "true면 old_string이 나오는 모든 곳을 바꾼다. 기본값 false.",
                },
            },
            "required": ["path", "old_string", "new_string"],
        },
        edit_file,
    )

    registry.register(
        "run_command",
        "작업 디렉터리에서 셸 명령을 실행하고 exit_code, stdout, stderr를 돌려준다."
        " 프로그램 실행, 테스트 실행, 수정 결과 검증에 사용한다. 제한 시간을 넘기면 강제 종료된다.",
        {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "실행할 셸 명령. 예: `python test.py`"},
            },
            "required": ["command"],
        },
        run_command,
    )

    return registry
