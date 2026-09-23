"""Agent Loop.

책임: `docs/ROADMAP.md` Step 1의 핵심 루프를 구현한다.

    while not finished:
        response = llm(messages, tools)
        if response.tool_call:
            result = execute_tool(response.tool_call)
            messages.append(result)
        else:
            return response

안전장치:
- max_iterations: LLM 호출 횟수 상한 (무한 루프 방지)
- command_timeout: run_command 한 번의 실행 시간 상한(초)
- max_consecutive_errors: Tool 호출이 연속으로 실패할 수 있는 횟수 (성공하면 0으로 초기화)

아직 구현하지 않음: Planner, Sub Agent, Git 연동, Context 요약.
"""

from __future__ import annotations

import json
from typing import Callable

from agent.prompts import build_system_prompt
from llm.base import LLMError, LLMProvider, LLMResponse
from tools.registry import ToolRegistry, ToolResult

# on_event(event_type, payload)로 전달되는 이벤트 종류:
#   "iteration"   {"iteration", "max_iterations"}          LLM 호출 직전
#   "assistant"   {"content"}                              LLM이 Tool 호출과 함께 남긴 텍스트
#   "tool_call"   {"id", "name", "arguments"}              Tool 실행 직전
#   "tool_result" {"id", "name", "ok", "output", "error"}  Tool 실행 직후
#   "stopped"     {"reason", "message"}                    안전장치나 LLM 오류로 중단
EventHandler = Callable[[str, dict], None]


def _assistant_message(response: LLMResponse) -> dict:
    """LLM의 Tool 호출 요청을 대화 기록에 남길 assistant 메시지로 바꾼다."""
    return {
        "role": "assistant",
        "content": response.content,
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.name,
                    "arguments": json.dumps(tool_call.arguments, ensure_ascii=False),
                },
            }
            for tool_call in response.tool_calls
        ],
    }


def run_agent_loop(
    user_message: str,
    llm: LLMProvider,
    tools: ToolRegistry,
    *,
    max_iterations: int = 20,
    command_timeout: int = 60,
    max_consecutive_errors: int = 3,
    on_event: EventHandler | None = None,
) -> str:
    """사용자 요청 하나를 처리하고 최종 답변(또는 중단 사유)을 문자열로 돌려준다."""

    def emit(event_type: str, payload: dict) -> None:
        if on_event is not None:
            on_event(event_type, payload)

    def stop(reason: str, message: str) -> str:
        emit("stopped", {"reason": reason, "message": message})
        return message

    messages: list[dict] = [
        {"role": "system", "content": build_system_prompt(tools.base_dir)},
        {"role": "user", "content": user_message},
    ]
    consecutive_errors = 0

    for iteration in range(1, max_iterations + 1):
        emit("iteration", {"iteration": iteration, "max_iterations": max_iterations})

        try:
            response = llm.generate(messages, tools.get_schemas())
        except LLMError as exc:
            return stop("llm_error", f"LLM 호출에 실패해 중단했습니다: {exc}")

        if not response.tool_calls:
            return response.content or "(LLM이 빈 응답을 반환했습니다.)"

        messages.append(_assistant_message(response))
        if response.content:
            emit("assistant", {"content": response.content})

        for tool_call in response.tool_calls:
            emit("tool_call", {"id": tool_call.id, "name": tool_call.name, "arguments": tool_call.arguments})

            if tool_call.arguments_error:
                result = ToolResult(False, "", tool_call.arguments_error)
            else:
                result = tools.execute(tool_call.name, tool_call.arguments, command_timeout=command_timeout)

            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result.as_text()})
            emit(
                "tool_result",
                {
                    "id": tool_call.id,
                    "name": tool_call.name,
                    "ok": result.ok,
                    "output": result.output,
                    "error": result.error,
                },
            )

            consecutive_errors = 0 if result.ok else consecutive_errors + 1
            if consecutive_errors >= max_consecutive_errors:
                return stop(
                    "consecutive_errors",
                    f"Tool 호출이 연속 {consecutive_errors}번 실패해 중단했습니다. 마지막 오류: {result.error}",
                )

    return stop("max_iterations", f"최대 반복 횟수({max_iterations})에 도달해 중단했습니다.")
