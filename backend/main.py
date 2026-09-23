"""SHYNE 백엔드 진입점 — Step 1 최소 CLI.

사용자 prompt 하나를 받아 Agent Loop를 실행하고, Tool 호출과 결과(Tool Trace)를 그대로
stdout에 출력한다.

    uv run python backend/main.py "test.py를 실행하고 결과를 알려줘."
    uv run python backend/main.py --dir playground "test.py 파일을 만들고 hello world를 출력해."

Step 2에서 FastAPI 앱을 생성하고 api/chat.py의 라우터를 등록할 예정이다. 그때는 아래
`print_event` 대신 같은 on_event 콜백을 API 이벤트 스트림에 연결한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent.loop import run_agent_loop
from agent.runtime import RuntimeConfigError, build_runtime

DISPLAY_LIMIT = 2_000


def _shorten(text: str, full: bool) -> str:
    if full or len(text) <= DISPLAY_LIMIT:
        return text
    return f"{text[:DISPLAY_LIMIT]}\n[... 화면 출력만 생략했습니다. 전체를 보려면 --full 옵션을 쓰세요 ...]"


def _indent(text: str) -> str:
    return "\n".join(f"    {line}" for line in text.splitlines())


def make_event_printer(full: bool):
    def print_event(event_type: str, payload: dict) -> None:
        if event_type == "iteration":
            print(f"\n--- 반복 {payload['iteration']}/{payload['max_iterations']}: LLM 호출 ---", flush=True)
        elif event_type == "assistant":
            print(f"[LLM] {payload['content']}", flush=True)
        elif event_type == "tool_call":
            arguments = json.dumps(payload["arguments"], ensure_ascii=False)
            print(f"[Tool 호출] {payload['name']} {_shorten(arguments, full)}", flush=True)
        elif event_type == "tool_result":
            status = "성공" if payload["ok"] else f"실패 - {payload['error']}"
            print(f"[Tool 결과] {status}", flush=True)
            if payload["output"]:
                print(_indent(_shorten(payload["output"], full)), flush=True)

    return print_event


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SHYNE Coding Agent (Step 1 최소 CLI)")
    parser.add_argument("prompt", help="Agent에게 시킬 작업 (자연어)")
    parser.add_argument("--dir", default=".", help="Agent가 작업할 디렉터리 (기본값: 현재 디렉터리)")
    parser.add_argument("--full", action="store_true", help="Tool 인자/결과를 생략 없이 전부 출력")
    args = parser.parse_args(argv)

    # 출력이 파이프로 연결된 Windows 환경(cp949)에서 표현할 수 없는 문자가 나와도 죽지 않게 한다.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    try:
        llm, tools, settings = build_runtime(Path(args.dir))
    except RuntimeConfigError as exc:
        print(f"[SHYNE] 설정 오류: {exc}", file=sys.stderr)
        return 2

    print(f"[SHYNE] 작업 디렉터리: {tools.base_dir}")
    print(f"[SHYNE] 모델: {getattr(llm, 'model', '(알 수 없음)')}")
    print(
        "[SHYNE] 안전장치: "
        f"max_iterations={settings['max_iterations']}, "
        f"command_timeout={settings['command_timeout']}s, "
        f"max_consecutive_errors={settings['max_consecutive_errors']}"
    )
    print(f"[SHYNE] 요청: {args.prompt}")

    stopped = False
    event_printer = make_event_printer(args.full)

    def on_event(event_type: str, payload: dict) -> None:
        nonlocal stopped
        if event_type == "stopped":
            stopped = True
        event_printer(event_type, payload)

    try:
        answer = run_agent_loop(args.prompt, llm, tools, on_event=on_event, **settings)
    except KeyboardInterrupt:
        print("\n[SHYNE] 사용자가 중단했습니다.", file=sys.stderr)
        return 130

    print(f"\n=== {'중단' if stopped else '최종 답변'} ===")
    print(answer)
    return 1 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
