"""LLMProvider 추상 인터페이스와 공통 자료구조.

Agent Loop(agent/loop.py)는 이 모듈의 `LLMProvider`/`LLMResponse`/`ToolCall`에만 의존하고
구체 Provider(OpenAI, vLLM, Anthropic 등)를 모른다. 새 Provider를 추가할 때는 `generate()`
하나만 구현하면 된다.

메시지 포맷은 OpenAI Chat Completions 형식을 공통 규격으로 쓴다.

    {"role": "system" | "user" | "assistant", "content": "..."}
    {"role": "assistant", "content": ..., "tool_calls": [...]}   # LLM이 Tool 호출을 요청
    {"role": "tool", "tool_call_id": "...", "content": "..."}     # Tool 실행 결과
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class LLMError(Exception):
    """LLM 호출 실패(네트워크 오류, HTTP 오류, 해석할 수 없는 응답)를 나타낸다."""


@dataclass
class ToolCall:
    """LLM이 요청한 Tool 호출 하나."""

    id: str
    name: str
    arguments: dict
    # LLM이 보낸 arguments가 올바른 JSON 객체가 아니었을 때의 오류 설명.
    # 값이 있으면 Agent Loop는 Tool을 실행하지 않고 이 오류를 LLM에 그대로 돌려준다.
    arguments_error: str | None = None


@dataclass
class LLMResponse:
    """LLM 응답 한 번. tool_calls가 비어 있으면 content가 최종 답변이다."""

    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(Protocol):
    def generate(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        """messages와 Tool 스키마를 보내고 LLM 응답을 받는다. 실패하면 LLMError를 던진다."""
        ...
