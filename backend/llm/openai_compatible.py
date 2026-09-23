"""OpenAI-compatible LLM Provider 구현체.

책임: base.py의 LLMProvider 인터페이스를 OpenAI-compatible Chat Completions / Tool Calling
API(`POST {base_url}/chat/completions`)로 구현한다. vLLM, Ollama, LM Studio, OpenAI를 같은
코드로 다룬다.

vLLM은 서버를 `--enable-auto-tool-choice --tool-call-parser <모델에 맞는 parser>` 옵션으로
띄워야 tool calling이 동작한다. 옵션이 없으면 서버가 HTTP 400을 돌려주고, 그 내용은 LLMError
메시지로 그대로 전달된다.
"""

from __future__ import annotations

import json
import uuid

import httpx

from llm.base import LLMError, LLMResponse, ToolCall

# 로컬 LLM은 긴 프롬프트에서 첫 토큰까지 오래 걸릴 수 있어 읽기 제한 시간을 넉넉하게 둔다.
DEFAULT_REQUEST_TIMEOUT = 300.0


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        temperature: float | None = None,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        transport: httpx.BaseTransport | None = None,  # 테스트에서 가짜 서버를 끼워 넣는 용도
    ):
        self.model = model
        self.temperature = temperature
        self._url = base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.Client(
            headers=headers,
            timeout=httpx.Timeout(request_timeout, connect=10.0),
            transport=transport,
        )

    def generate(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        payload: dict = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if self.temperature is not None:
            payload["temperature"] = self.temperature

        try:
            response = self._client.post(self._url, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMError(f"LLM 서버 응답 시간이 초과됐습니다 ({self._url})") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM 서버에 연결하지 못했습니다 ({self._url}): {exc}") from exc

        if response.status_code >= 400:
            raise LLMError(f"LLM 서버가 HTTP {response.status_code}를 돌려줬습니다: {response.text[:500]}")

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMError(f"LLM 응답이 JSON이 아닙니다: {response.text[:200]}") from exc
        return _parse_response(data)


def _parse_response(data: object) -> LLMResponse:
    try:
        message = data["choices"][0]["message"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"LLM 응답 형식을 해석할 수 없습니다: {str(data)[:200]}") from exc

    content = message.get("content")
    raw_tool_calls = message.get("tool_calls") or []
    return LLMResponse(
        content=content if isinstance(content, str) else None,
        tool_calls=[_parse_tool_call(raw) for raw in raw_tool_calls],
    )


def _parse_tool_call(raw: dict) -> ToolCall:
    function = raw.get("function") or {}
    # 일부 서버는 id를 비워서 보낸다. tool 결과 메시지와 짝을 맞추려면 고유한 id가 필요하다.
    call_id = raw.get("id") or f"call_{uuid.uuid4().hex[:12]}"
    name = function.get("name") or ""
    raw_arguments = function.get("arguments")

    if isinstance(raw_arguments, dict):  # 표준은 JSON 문자열이지만 객체로 보내는 서버도 있다.
        return ToolCall(call_id, name, raw_arguments)
    if raw_arguments is None or raw_arguments == "":
        return ToolCall(call_id, name, {})

    try:
        arguments = json.loads(raw_arguments)
    except (TypeError, ValueError) as exc:
        return ToolCall(
            call_id,
            name,
            {},
            arguments_error=f"Tool 인자가 올바른 JSON이 아닙니다 ({exc}). JSON 객체 형식으로 다시 호출하세요.",
        )
    if not isinstance(arguments, dict):
        return ToolCall(call_id, name, {}, arguments_error="Tool 인자는 JSON 객체여야 합니다.")
    return ToolCall(call_id, name, arguments)
