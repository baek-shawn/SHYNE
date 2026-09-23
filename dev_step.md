# dev_step: Step 1 — 가장 작은 Coding Agent

> 이 문서는 지금 진행 중인 Step **하나**의 구현 방법을 상세히 적은 문서다. "무엇을" 만들지는
> [`docs/ROADMAP.md`](docs/ROADMAP.md)를 따르고, 이 문서는 그중 Step 1을 "어떻게" 구현할지만
> 다룬다. Step 1이 끝나면 이 파일은 삭제되고 Step 2용 `dev_step.md`로 교체된다
> (`CLAUDE.md`의 "Step 개발 프로세스" 절 참고).

## 구현 상태 (2026-09-21)

코드 구현과 자동 테스트(`uv run pytest`, 48개)는 끝났다. 남은 것은 사용자가 실제 LLM을 연결해
Test A/B/C를 수동 확인하는 것이다 (아래 "테스트 방법"). 구현하면서 처음 설계와 달라진 부분은
각 절에 **[구현 반영]** 으로 표시했다.

## 목표

다음 흐름이 실제로 동작하게 만든다 (`docs/ROADMAP.md` Step 1 / Test C와 동일).

```text
run(test.py) → SyntaxError 등 오류 확인 → read → edit → run → 성공 확인 → 사용자에게 결과 보고
```

범위에 포함:

- LLM Provider 추상화 (OpenAI-compatible API 1종 구현)
- Tool 6종: `list_files`, `read_file`, `search_files`, `write_file`, `edit_file`, `run_command`
- 단일 Agent Loop + 안전장치(`max_iterations=20`, `command_timeout=60s`, `max_consecutive_errors=3`)
- 결과를 눈으로 확인할 수 있는 최소 CLI 실행 방법 (Step 2 Web UI는 범위 밖)

범위에서 제외 (다음 Step 이후): Git 연동, Tool Permission(AUTO/CONFIRM/BLOCK), Context 요약,
Task State, Planner, Sub Agent, Web UI.

## 건드릴 파일과 파일별 작업

이미 `CLAUDE.md`의 "아키텍처" 절에 있는 placeholder 파일들을 채운다. 새 파일은 만들지 않는다.

| 파일 | 작업 |
|---|---|
| `backend/llm/base.py` | `LLMProvider` 인터페이스, `Message`/`ToolCall`/`LLMResponse` 자료구조 정의 |
| `backend/llm/openai_compatible.py` | `LLMProvider`를 OpenAI-compatible Chat Completions(tool calling)로 구현 |
| `backend/tools/file.py` | `list_files`, `read_file`, `write_file`, `edit_file` 구현 |
| `backend/tools/search.py` | `search_files` 구현 (파일명/내용 검색) |
| `backend/tools/shell.py` | `run_command` 구현 (`command_timeout` 적용) |
| `backend/tools/registry.py` | 위 6개 Tool을 이름→함수, 이름→JSON 스키마로 등록하는 `ToolRegistry` |
| `backend/agent/loop.py` | 핵심 Agent Loop(`run_agent_loop`) + 안전장치 |
| `backend/agent/runtime.py` | `.env` 설정을 읽어 `LLMProvider` + `ToolRegistry` + 안전장치 값을 조립하는 `build_runtime()` |
| `backend/agent/prompts.py` | Step 1용 System Prompt 상수 |
| `backend/main.py` | 최소 CLI 진입점: 사용자 prompt 한 개를 받아 Agent Loop를 실행하고 Tool 호출/결과를 stdout에 그대로 출력 |
| `tests/test_tools.py` (신규) | 6개 Tool 단위 테스트 |
| `tests/test_agent_loop.py` (신규) | Fake LLM Provider로 Agent Loop 제어 흐름(반복/timeout/연속 오류) 테스트 |
| `tests/test_openai_compatible.py` (신규) | **[구현 반영]** `httpx.MockTransport`로 Provider의 요청 payload와 응답/오류 해석 테스트 |

**[구현 반영]** 그 밖에 바뀐 설정 파일: `pyproject.toml`(의존성 `httpx`, `python-dotenv` 추가),
`.env.example`(주석 갱신, 선택 항목 `LLM_TEMPERATURE` 추가), `.gitignore`(수동 테스트용
`playground/` 제외).

## 인터페이스 설계

### `backend/llm/base.py`

```text
@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict

@dataclass
class LLMResponse:
    content: str | None       # tool_calls가 없을 때만 최종 답변으로 사용
    tool_calls: list[ToolCall]

class LLMProvider(Protocol):
    def generate(self, messages: list[dict], tools: list[dict]) -> LLMResponse: ...
```

- `messages`는 OpenAI Chat Completions 메시지 형식(`role`/`content`, tool 결과는
  `role="tool"` + `tool_call_id`)을 그대로 따른다 — 나중에 다른 Provider를 추가해도 Agent Loop가
  메시지 포맷을 바꿀 필요가 없게 한다.
- `tools`는 `ToolRegistry.get_schemas()`가 만든 JSON 스키마 리스트를 그대로 전달한다.
- **[구현 반영]** `LLMError` 예외를 추가했다. Provider는 네트워크/HTTP/응답 형식 오류를 모두
  `LLMError`로 바꿔 던지고, Agent Loop는 이것만 잡아서 중단 메시지로 돌려준다.
- **[구현 반영]** `ToolCall`에 `arguments_error: str | None` 필드를 추가했다. LLM이 깨진 JSON을
  인자로 보내면(로컬 LLM에서 흔함) Provider가 예외를 던지는 대신 이 필드에 오류를 담고, Agent
  Loop는 Tool을 실행하지 않고 그 오류를 Tool 결과로 LLM에 돌려줘 스스로 다시 호출하게 한다.

### `backend/llm/openai_compatible.py`

```text
class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, base_url: str, api_key: str, model: str): ...
    def generate(self, messages, tools) -> LLMResponse:
        # OpenAI-compatible /chat/completions 호출 (tool_choice="auto")
        # 응답의 tool_calls를 ToolCall 리스트로, 아니면 content를 LLMResponse.content로 변환
```

- `.env`의 `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`을 그대로 사용한다 (`.env.example` 이미
  존재).
- 첫 대상은 사내/IDC vLLM이지만, vLLM이 OpenAI 호환 tool calling을 지원하지 않을 수 있으므로
  개발/테스트 초기에는 OpenAI 실제 API 또는 아래 `tests/`의 Fake Provider로 먼저 Agent Loop
  로직을 검증하고, vLLM 연결은 마지막에 확인한다.

### `backend/tools/registry.py`

```text
@dataclass
class ToolResult:
    ok: bool
    output: str
    error: str | None = None

class ToolRegistry:
    def register(self, name: str, description: str, parameters: dict, fn: Callable[..., ToolResult]): ...
    def get_schemas(self) -> list[dict]: ...        # LLM에 전달할 OpenAI tool 스키마 형식
    def execute(self, name: str, arguments: dict) -> ToolResult: ...
```

- 6개 Tool 함수는 모두 `(arguments: dict, *, base_dir: Path) -> ToolResult` 시그니처로 통일한다.
- `base_dir`은 Agent가 작업할 프로젝트 루트다. **모든 파일 경로는 `base_dir` 하위로만 접근
  가능하도록 제한한다** (상위 디렉터리 탈출 방지) — Step 4 Permission이 없는 지금 단계에서 최소
  안전장치다.
- `run_command`만 `command_timeout`을 추가 인자로 받는다: `run_command(arguments, *, base_dir, timeout)`.
- **[구현 반영]** 실제 시그니처는 다음과 같다.
  - `ToolRegistry(base_dir)`: Registry가 `base_dir`을 들고 있다가 모든 Tool에 넘겨준다.
  - `execute(name, arguments, *, command_timeout=None)`: 함수 시그니처에 `timeout`이 있는
    Tool(`run_command`)에만 `command_timeout`을 전달한다. 없는 Tool 이름, 필수 인자 누락, Tool
    내부 예외는 모두 예외가 아니라 `ToolResult(ok=False)`로 돌려준다 (LLM이 읽고 고칠 수 있게).
  - `ToolResult.as_text()`: LLM에 돌려줄 문자열. 실패하면 `[오류] ...`를 앞에 붙인다.
  - `build_default_registry(base_dir)`: Tool 6종의 설명/JSON 스키마를 등록한 Registry를 만든다.
    새 Tool은 여기에 추가한다.
- **[구현 반영]** `run_command`는 종료 코드가 0이 아니면 `ok=False`다 (연속 오류 횟수에 포함).
  출력은 `exit_code` / `[stdout]` / `[stderr]` 형식이고, timeout 시 자식 프로세스까지 종료한다.
- **[구현 반영]** `read_file`은 줄 번호 없이 파일 내용 그대로를 돌려준다(`edit_file`의
  `old_string`이 정확히 일치하도록). `edit_file`은 기존 파일의 CRLF 줄바꿈과 인코딩을 보존한다.

### `backend/agent/loop.py`

```text
def run_agent_loop(
    user_message: str,
    llm: LLMProvider,
    tools: ToolRegistry,
    *,
    max_iterations: int = 20,
    command_timeout: int = 60,
    max_consecutive_errors: int = 3,
    on_event: Callable[[str, dict], None] | None = None,
) -> str:
    ...
```

의사코드 (기획서 Step 1의 루프를 그대로 따름):

```text
messages = [system_prompt(), {"role": "user", "content": user_message}]
consecutive_errors = 0

for iteration in range(max_iterations):
    response = llm.generate(messages, tools.get_schemas())

    if not response.tool_calls:
        return response.content   # 최종 답변, 루프 종료

    for tool_call in response.tool_calls:
        result = tools.execute(tool_call.name, tool_call.arguments)  # run_command는 timeout 전달
        messages.append(assistant_tool_call_message(tool_call))
        messages.append(tool_result_message(tool_call, result))
        on_event("tool_call", {...})   # CLI가 Tool 이름/인자/결과를 stdout에 찍는 훅

        consecutive_errors = 0 if result.ok else consecutive_errors + 1
        if consecutive_errors >= max_consecutive_errors:
            return "연속 오류로 중단: <마지막 오류 요약>"

return "최대 반복 횟수(max_iterations)에 도달해 중단했습니다."
```

- `on_event` 콜백으로 CLI(`backend/main.py`)가 Tool 이름/인자/결과를 그대로 출력한다. Step 2에서
  같은 콜백을 API/이벤트 스트림으로 바꿔 UI에 연결할 수 있게 하기 위한 최소 확장 지점이다.
- `command_timeout`은 `run_command` 실행에만 적용된다 — 다른 Tool은 즉시 반환되므로 별도
  타임아웃이 필요 없다.
- **[구현 반영]** 위 의사코드와 다른 점:
  - OpenAI 메시지 규격에 맞춰, LLM 응답 하나당 assistant 메시지는 **한 번만**(모든
    `tool_calls`를 담아) 추가하고 그 뒤에 Tool 호출마다 `role="tool"` 메시지를 하나씩 붙인다.
  - `on_event` 이벤트는 `iteration`(LLM 호출 직전) / `assistant`(Tool 호출과 함께 온 텍스트) /
    `tool_call`(실행 직전) / `tool_result`(실행 직후) / `stopped`(안전장치·LLM 오류로 중단)
    다섯 가지다. 오래 걸리는 명령도 실행 전에 무엇을 하는지 보이도록 호출과 결과를 나눴다.
  - System Prompt는 `agent/prompts.py`의 `build_system_prompt(base_dir)`가 만든다. 작업
    디렉터리, OS, 셸 종류(Windows는 cmd.exe)를 채워 넣어 LLM이 환경에 맞는 명령을 쓰게 한다.
  - `llm.generate()`가 `LLMError`를 던지면 "LLM 호출에 실패해 중단했습니다"를 반환한다.

### `backend/agent/runtime.py`

```text
def build_runtime(base_dir: Path) -> tuple[LLMProvider, ToolRegistry, dict]:
    # .env 로드 (LLM_PROVIDER, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL,
    #            AGENT_MAX_ITERATIONS, AGENT_COMMAND_TIMEOUT, AGENT_MAX_CONSECUTIVE_ERRORS)
    # LLMProvider 인스턴스 생성, ToolRegistry에 6개 Tool 등록 후 반환
```

### `backend/main.py` (최소 CLI, Step 2 UI 아님)

```text
사용법: uv run python backend/main.py "test.py를 실행해보고 오류를 찾아서 수정한 다음 다시 실행해서 정상 동작하는지 확인해."

동작:
1. build_runtime(현재 디렉터리)로 LLMProvider/ToolRegistry 조립
2. run_agent_loop(...) 실행, on_event로 각 Tool 호출/결과를 그대로 stdout에 출력
3. 최종 응답을 stdout에 출력
```

**[구현 반영]** 옵션 두 개를 추가했다.

- `--dir <폴더>`: Agent의 작업 디렉터리(`base_dir`). 기본값은 현재 디렉터리다. 저장소 루트에
  테스트 파일이 생기지 않도록 수동 테스트는 `--dir playground`로 실행한다 (`playground/`는
  `.gitignore`에 등록, 폴더는 미리 있어야 한다).
- `--full`: Tool 인자/결과를 화면에서 생략하지 않는다 (기본은 2,000자까지만 표시. LLM에는 항상
  전체가 전달된다).
- 종료 코드: 최종 답변 0, 안전장치/LLM 오류로 중단 1, 설정 오류 2.
- `.env`는 작업 디렉터리가 아니라 항상 SHYNE 저장소 루트에서 읽는다.

## 구현 순서

1. `backend/llm/base.py` 자료구조 → `backend/tools/registry.py`의 `ToolResult`/`ToolRegistry`
   (Tool 함수보다 먼저 인터페이스부터 고정).
2. `backend/tools/file.py`, `search.py`, `shell.py` 구현 + `tests/test_tools.py`로 개별 검증
   (아직 LLM/Agent Loop 없이 함수 단위로 먼저 확인).
3. `backend/agent/prompts.py`의 System Prompt 작성.
4. `backend/agent/loop.py` 구현 + `tests/test_agent_loop.py`에서 Fake LLM Provider로 반복/오류
   제어 흐름만 먼저 검증 (실제 LLM 없이도 Loop 로직을 확신할 수 있게).
5. `backend/llm/openai_compatible.py` 구현.
6. `backend/agent/runtime.py`, `backend/main.py` 연결.
7. `docs/ROADMAP.md`의 Test A → Test B → Test C 순서로 CLI 수동 테스트.

## 테스트 방법

- `uv run pytest` — `tests/test_tools.py`(6개 Tool 단위 테스트), `tests/test_agent_loop.py`
  (Fake LLM Provider로 `max_iterations`/`command_timeout`/`max_consecutive_errors` 각각 별도 검증).
- **[구현 반영]** `tests/test_openai_compatible.py`(Provider 요청/응답 해석)도 함께 돈다.
- 수동 테스트 (`docs/ROADMAP.md` "초기 테스트 시나리오"). 먼저 `.env.example`을 `.env`로 복사해
  `LLM_PROVIDER`/`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`을 채운다. **[구현 반영]** 저장소 루트가
  어질러지지 않게 `--dir playground`로 실행한다.
  - Test A: `uv run python backend/main.py --dir playground "test.py 파일을 만들고 hello world를 출력해."`
  - Test B: `uv run python backend/main.py --dir playground "test.py를 실행하고 결과를 알려줘."`
  - Test C: 오류가 있는 Python 파일(`playground/broken.py`)을 두고
    `uv run python backend/main.py --dir playground "broken.py를 실행해보고 오류를 찾은 다음 수정하고, 다시 실행해서 정상 동작하는지 확인해."`
    실행 — Tool Trace에 `run → error → read → edit → run → success` 순서가 실제로 찍히는지 확인.

## 완료 조건

- `uv run pytest` 통과.
- Test A, B, C 모두 수동 확인 완료 (특히 Test C가 기획서 기준 "기본 Agent Harness 1차 구현 완료"
  판정 기준).
- 사용자가 위 결과를 보고 이 Step이 끝났다고 확인하면, `CLAUDE.md` 규칙대로
  `docs/HISTORY.md`/`.agent/HANDOFF.md`를 갱신하고 이 파일을 삭제한 뒤 Step 2용 `dev_step.md`를
  새로 작성한다.
