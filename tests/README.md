# tests

`pytest` 기반 자동화 테스트. 실제 LLM 없이 돌아가며 `uv run pytest`로 실행한다.

| 파일 | 검증 대상 |
|---|---|
| `test_tools.py` | Tool 6종(`list_files`/`read_file`/`search_files`/`write_file`/`edit_file`/`run_command`)과 `ToolRegistry`. 작업 디렉터리 밖 경로 차단, CRLF 보존, `run_command` timeout 포함 |
| `test_agent_loop.py` | Fake LLM Provider로 Agent Loop 제어 흐름: 메시지 포맷, `max_iterations`, `command_timeout`, `max_consecutive_errors`, LLM 오류 처리, 그리고 Test C 흐름(실제 Tool 사용) |
| `test_openai_compatible.py` | `httpx.MockTransport`로 OpenAI-compatible 요청 payload와 응답/오류 해석 |

실제 LLM이 필요한 부분은 [docs/ROADMAP.md](../docs/ROADMAP.md)의 "초기 테스트 시나리오"를 CLI로
수동 확인한다. `.env`를 채운 뒤 저장소 루트에서 실행한다. `--dir`로 지정한 폴더는 미리 있어야
하므로 `playground/`가 없으면 먼저 만든다 (`playground/`는 Git에서 제외된다).

- Test A — 파일 생성: `uv run python backend/main.py --dir playground "test.py 파일을 만들고 hello world를 출력해."`
  → `write_file` 호출과 파일 생성 확인.
- Test B — 실행: `uv run python backend/main.py --dir playground "test.py를 실행하고 결과를 알려줘."`
  → `run_command` 호출과 실제 stdout 확인.
- Test C — 오류 수정 Agent Loop: `playground/test.py`에 일부러 오류를 넣은 뒤
  `uv run python backend/main.py --dir playground "test.py를 실행해보고 오류를 찾은 다음 수정하고, 다시 실행해서 정상 동작하는지 확인해."`
  → Tool Trace가 `run → error → read → edit → run → success` 순서인지 확인.
  **Test C 성공 = 기본 Agent Harness 1차 구현 완료 기준.**
