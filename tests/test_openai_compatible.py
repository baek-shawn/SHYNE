"""OpenAICompatibleProvider 테스트. 실제 서버 대신 httpx.MockTransport로 요청/응답을 검증한다."""

import json

import httpx
import pytest

from llm.base import LLMError
from llm.openai_compatible import OpenAICompatibleProvider

TOOLS = [{"type": "function", "function": {"name": "read_file", "description": "d", "parameters": {"type": "object"}}}]


def make_provider(handler, **kwargs):
    return OpenAICompatibleProvider(
        "http://llm.test/v1/", "test-key", "test-model", transport=httpx.MockTransport(handler), **kwargs
    )


def completion(message):
    return httpx.Response(200, json={"choices": [{"index": 0, "message": message}]})


def test_request_payload_and_final_answer():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return completion({"role": "assistant", "content": "안녕하세요"})

    provider = make_provider(handler, temperature=0.2)
    messages = [{"role": "user", "content": "안녕"}]

    response = provider.generate(messages, TOOLS)

    assert seen["url"] == "http://llm.test/v1/chat/completions"
    assert seen["authorization"] == "Bearer test-key"
    assert seen["body"] == {
        "model": "test-model",
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.2,
    }
    assert response.content == "안녕하세요"
    assert response.tool_calls == []


def test_tools_and_temperature_are_omitted_when_not_set():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return completion({"role": "assistant", "content": "ok"})

    make_provider(handler).generate([{"role": "user", "content": "hi"}], [])

    assert set(seen["body"]) == {"model", "messages"}


def test_tool_calls_are_parsed():
    def handler(request):
        return completion(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"path": "test.py"}'},
                    },
                    {"type": "function", "function": {"name": "list_files", "arguments": ""}},
                ],
            }
        )

    response = make_provider(handler).generate([], TOOLS)

    assert response.content is None
    first, second = response.tool_calls
    assert (first.id, first.name, first.arguments, first.arguments_error) == (
        "call_1",
        "read_file",
        {"path": "test.py"},
        None,
    )
    assert second.name == "list_files"
    assert second.arguments == {}
    assert second.id.startswith("call_")  # 서버가 id를 주지 않으면 직접 만든다


def test_broken_tool_arguments_are_flagged_instead_of_raising():
    def handler(request):
        return completion(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "function": {"name": "read_file", "arguments": '{"path": "test.py"'}},
                    {"id": "call_2", "function": {"name": "read_file", "arguments": '["test.py"]'}},
                ],
            }
        )

    broken_json, not_an_object = make_provider(handler).generate([], TOOLS).tool_calls

    assert broken_json.arguments == {}
    assert "올바른 JSON이 아닙니다" in broken_json.arguments_error
    assert "JSON 객체" in not_an_object.arguments_error


def test_http_error_becomes_llm_error():
    def handler(request):
        return httpx.Response(400, json={"error": {"message": '"auto" tool choice requires --enable-auto-tool-choice'}})

    with pytest.raises(LLMError) as excinfo:
        make_provider(handler).generate([], TOOLS)

    assert "HTTP 400" in str(excinfo.value)
    assert "--enable-auto-tool-choice" in str(excinfo.value)


def test_connection_failure_becomes_llm_error():
    def handler(request):
        raise httpx.ConnectError("connection refused")

    with pytest.raises(LLMError) as excinfo:
        make_provider(handler).generate([], TOOLS)

    assert "연결하지 못했습니다" in str(excinfo.value)


def test_unexpected_response_shape_becomes_llm_error():
    def handler(request):
        return httpx.Response(200, json={"unexpected": True})

    with pytest.raises(LLMError):
        make_provider(handler).generate([], TOOLS)
