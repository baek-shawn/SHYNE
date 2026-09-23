"""Agent Loop 제어 흐름 테스트. 실제 LLM 대신 미리 정해둔 응답을 돌려주는 Fake Provider를 쓴다."""

import copy
import sys

from agent.loop import run_agent_loop
from llm.base import LLMError, LLMResponse, ToolCall
from tools.registry import build_default_registry

PYTHON = f'"{sys.executable}"'


class FakeLLM:
    """responses를 순서대로 돌려준다. 다 쓰고 나면 마지막 응답을 계속 반복한다."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []  # generate()가 호출될 때마다 받은 messages의 복사본

    def generate(self, messages, tools):
        self.calls.append(copy.deepcopy(messages))
        index = min(len(self.calls), len(self.responses)) - 1
        response = self.responses[index]
        if isinstance(response, Exception):
            raise response
        return response


def tool_call(name, arguments, call_id="call_1"):
    return LLMResponse(content=None, tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)])


def final(text):
    return LLMResponse(content=text, tool_calls=[])


def collect_events():
    events = []
    return events, lambda event_type, payload: events.append((event_type, payload))


def test_returns_final_answer_without_tools(tmp_path):
    llm = FakeLLM([final("안녕하세요")])

    answer = run_agent_loop("안녕", llm, build_default_registry(tmp_path))

    assert answer == "안녕하세요"
    assert len(llm.calls) == 1
    assert [message["role"] for message in llm.calls[0]] == ["system", "user"]
    assert llm.calls[0][1]["content"] == "안녕"


def test_tool_result_is_appended_in_openai_message_format(tmp_path):
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    llm = FakeLLM([tool_call("read_file", {"path": "hello.txt"}, call_id="call_abc"), final("읽었습니다")])

    answer = run_agent_loop("hello.txt 읽어줘", llm, build_default_registry(tmp_path))

    assert answer == "읽었습니다"
    second_request = llm.calls[1]
    assert [message["role"] for message in second_request] == ["system", "user", "assistant", "tool"]
    assistant, tool = second_request[2], second_request[3]
    assert assistant["tool_calls"] == [
        {
            "id": "call_abc",
            "type": "function",
            "function": {"name": "read_file", "arguments": '{"path": "hello.txt"}'},
        }
    ]
    assert tool == {"role": "tool", "tool_call_id": "call_abc", "content": "hello"}


def test_multiple_tool_calls_in_one_response(tmp_path):
    response = LLMResponse(
        content="두 파일을 만듭니다.",
        tool_calls=[
            ToolCall(id="call_1", name="write_file", arguments={"path": "a.txt", "content": "a"}),
            ToolCall(id="call_2", name="write_file", arguments={"path": "b.txt", "content": "b"}),
        ],
    )
    llm = FakeLLM([response, final("완료")])

    run_agent_loop("파일 두 개 만들어", llm, build_default_registry(tmp_path))

    assert (tmp_path / "a.txt").exists() and (tmp_path / "b.txt").exists()
    roles = [message["role"] for message in llm.calls[1]]
    assert roles == ["system", "user", "assistant", "tool", "tool"]
    assert [message["tool_call_id"] for message in llm.calls[1][3:]] == ["call_1", "call_2"]


def test_scenario_c_run_error_read_edit_run_success(tmp_path):
    """ROADMAP Test C: run → error → read → edit → run → success 흐름을 실제 Tool로 재현한다."""
    (tmp_path / "test.py").write_text("print('hello world'\n", encoding="utf-8")
    llm = FakeLLM(
        [
            tool_call("run_command", {"command": f"{PYTHON} test.py"}, "call_1"),
            tool_call("read_file", {"path": "test.py"}, "call_2"),
            tool_call(
                "edit_file",
                {"path": "test.py", "old_string": "print('hello world'", "new_string": "print('hello world')"},
                "call_3",
            ),
            tool_call("run_command", {"command": f"{PYTHON} test.py"}, "call_4"),
            final("괄호가 빠진 SyntaxError를 고쳤고, 다시 실행해 hello world 출력을 확인했습니다."),
        ]
    )
    events, on_event = collect_events()

    answer = run_agent_loop("test.py를 실행해보고 오류를 고쳐줘", llm, build_default_registry(tmp_path), on_event=on_event)

    results = [payload for event_type, payload in events if event_type == "tool_result"]
    assert [(payload["name"], payload["ok"]) for payload in results] == [
        ("run_command", False),
        ("read_file", True),
        ("edit_file", True),
        ("run_command", True),
    ]
    # LLM은 첫 실행의 SyntaxError를 Tool 결과로 받아야 한다.
    first_tool_message = llm.calls[1][-1]
    assert first_tool_message["role"] == "tool"
    assert "SyntaxError" in first_tool_message["content"]
    assert (tmp_path / "test.py").read_text(encoding="utf-8") == "print('hello world')\n"
    assert "hello world" in results[-1]["output"]
    assert answer.startswith("괄호가 빠진")


def test_stops_at_max_iterations(tmp_path):
    llm = FakeLLM([tool_call("list_files", {})])  # 끝없이 Tool만 호출하는 LLM
    events, on_event = collect_events()

    answer = run_agent_loop("무한 루프", llm, build_default_registry(tmp_path), max_iterations=5, on_event=on_event)

    assert len(llm.calls) == 5
    assert "최대 반복 횟수(5)" in answer
    assert events[-1] == ("stopped", {"reason": "max_iterations", "message": answer})


def test_stops_after_max_consecutive_errors(tmp_path):
    llm = FakeLLM([tool_call("read_file", {"path": "missing.py"})])
    events, on_event = collect_events()

    answer = run_agent_loop(
        "없는 파일 읽기", llm, build_default_registry(tmp_path), max_consecutive_errors=3, on_event=on_event
    )

    assert len(llm.calls) == 3
    assert "연속 3번 실패" in answer
    assert "파일이 없습니다" in answer
    assert events[-1][0] == "stopped"
    assert events[-1][1]["reason"] == "consecutive_errors"


def test_successful_tool_call_resets_consecutive_errors(tmp_path):
    fail = tool_call("read_file", {"path": "missing.py"})
    succeed = tool_call("list_files", {})
    llm = FakeLLM([fail, fail, succeed, fail, fail, succeed, final("끝")])

    answer = run_agent_loop("오류와 성공 반복", llm, build_default_registry(tmp_path), max_consecutive_errors=3)

    assert answer == "끝"
    assert len(llm.calls) == 7


def test_command_timeout_is_applied_to_run_command(tmp_path):
    (tmp_path / "slow.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    llm = FakeLLM([tool_call("run_command", {"command": f"{PYTHON} slow.py"}), final("시간 초과를 확인했습니다")])
    events, on_event = collect_events()

    run_agent_loop("느린 명령", llm, build_default_registry(tmp_path), command_timeout=1, on_event=on_event)

    results = [payload for event_type, payload in events if event_type == "tool_result"]
    assert len(results) == 1
    assert results[0]["ok"] is False
    assert "1초 안에 끝나지 않아" in results[0]["error"]
    assert "1초 안에 끝나지 않아" in llm.calls[1][-1]["content"]


def test_unknown_tool_and_broken_arguments_are_reported_to_llm(tmp_path):
    broken = LLMResponse(
        content=None,
        tool_calls=[ToolCall(id="call_2", name="read_file", arguments={}, arguments_error="인자가 올바른 JSON이 아닙니다")],
    )
    llm = FakeLLM([tool_call("no_such_tool", {}, "call_1"), broken, final("포기")])

    answer = run_agent_loop("잘못된 호출", llm, build_default_registry(tmp_path))

    assert answer == "포기"
    assert "알 수 없는 Tool" in llm.calls[1][-1]["content"]
    assert "인자가 올바른 JSON이 아닙니다" in llm.calls[2][-1]["content"]


def test_llm_error_stops_the_loop(tmp_path):
    llm = FakeLLM([LLMError("연결할 수 없습니다")])
    events, on_event = collect_events()

    answer = run_agent_loop("안녕", llm, build_default_registry(tmp_path), on_event=on_event)

    assert "LLM 호출에 실패" in answer
    assert "연결할 수 없습니다" in answer
    assert events[-1][1]["reason"] == "llm_error"


def test_empty_final_content_gets_placeholder(tmp_path):
    llm = FakeLLM([LLMResponse(content=None, tool_calls=[])])

    assert run_agent_loop("안녕", llm, build_default_registry(tmp_path)) == "(LLM이 빈 응답을 반환했습니다.)"
