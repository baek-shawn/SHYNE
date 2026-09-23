# 프로젝트 변경 이력

이 문서는 실제 코드, 설정, 파일 구조, 문서 구조 또는 프로젝트 설계가 변경된 작업만 요약한다.
질문과 답변, 상태 확인, 읽기 전용 조사, 변경 없는 진단과 검토는 기록하지 않는다.

===================================
시작 시간: 2026-09-04 07:42:38 KST

## 작업 목적

`local_code_agent_development_plan_v2.md` 기획서를 바탕으로 SHYNE 프로젝트의 초기 디렉터리
구조와, 회사/집/노트북 등 여러 PC에서 Git으로 작업을 이어갈 수 있는 문서 체계
(`CLAUDE.md`, `.agent/`, `docs/`)를 [Agent_CADian](../../Agent_CADian) 프로젝트와 같은 방식으로
구성한다. 이번 작업 범위는 구조와 문서뿐이며 실제 Agent 로직 코드는 작성하지 않는다.

## 요약 계획

- 기획서의 "권장 초기 프로젝트 구조"(`backend/agent`, `backend/llm`, `backend/tools`,
  `backend/api`)와 "테스트 자산 관리" 구조(`benchmarks/`, `prompts/`, `results/`)를 실제
  디렉터리로 만든다.
- Python 모듈 파일은 책임을 설명하는 Docstring만 채운 placeholder로 두고, 실행 로직은
  작성하지 않는다.
- `local_code_agent_development_plan_v2.md`를 `docs/ROADMAP.md`로 옮긴다 (Agent_CADian이
  `Idea.MD`를 `docs/ROADMAP.md`로 옮긴 방식과 동일).
- `.agent/README.md`, `.agent/HANDOFF.md`, `docs/HISTORY.md`, `docs/DEPLOYMENT_TODO.md`를
  Agent_CADian과 같은 형식으로 새로 만든다.
- `CLAUDE.md`에 SHYNE 프로젝트 설명과 아키텍처 개요 절을 추가한다 (공통 에이전트 지침 절은
  기존 내용 유지).
- 여러 PC 간 동기화를 위해 Git 저장소를 초기화한다 (커밋은 사용자가 직접 진행).

## 변경 사항

- 디렉터리 생성: `backend/{agent,llm,tools,api}`, `frontend/`, `config/`, `docs/`, `.agent/`,
  `benchmarks/`, `prompts/`, `results/`, `tests/`.
- `backend/` 하위에 `__init__.py`와 `main.py`, `agent/{runtime,loop,state,prompts}.py`,
  `llm/{base,openai_compatible}.py`, `tools/{registry,file,search,shell}.py`, `api/chat.py`를
  책임 설명 Docstring만 채운 placeholder로 추가했다 (실행 코드 없음).
- `frontend/README.md`, `benchmarks/README.md`, `prompts/README.md`, `results/README.md`,
  `tests/README.md`로 각 폴더의 목적과 향후 구현 시점을 문서화했다.
- `config/config.yaml`, `.env.example`을 값 없는 형식(placeholder)으로 추가했다.
- `pyproject.toml`(의존성 미정), `.gitignore`를 루트에 추가했다.
- `local_code_agent_development_plan_v2.md`를 `docs/ROADMAP.md`로 이동하고 상단에
  `.agent/HANDOFF.md`·`docs/HISTORY.md` 참조 안내를 추가했다.
- `docs/DEPLOYMENT_TODO.md`를 새로 작성해 다른 PC 이전 절차와 미정 항목을 정리했다.
- `.agent/README.md`, `.agent/HANDOFF.md`를 Agent_CADian과 동일한 형식으로 추가했다.
- `CLAUDE.md`에 SHYNE 프로젝트 설명, 아키텍처(디렉터리 책임), 문서 표 절을 추가했다 (공통
  에이전트 작업 지침 절은 변경하지 않음).
- Git 저장소를 초기화했다 (`git init`). 커밋/원격 설정은 하지 않았다.

## 검증

- 코드 실행이 없는 구조/문서 변경이라 자동 테스트는 없다.
- `git status`로 예상한 파일만 신규로 잡히는지 확인했다.
- 새 문서들이 상호 참조하는 상대 경로(`../docs/...`, `../.agent/...`)가 실제 파일 위치와
  일치하는지 확인했다.

===================================
시작 시간: 2026-09-04 07:50:56 KST

## 작업 목적

앞으로 `uv`로 의존성과 실행 환경을 관리하기로 확정하여, [Agent_CADian](../../Agent_CADian)과 같은
방식으로 SHYNE의 uv 환경을 실제로 설치한다.

## 요약 계획

- `pyproject.toml`을 Agent_CADian 루트와 같은 "virtual project"(`[tool.uv] package = false`,
  build-system 없음) 방식으로 바꾼다.
- 테스트용 `dev` dependency group(pytest)과 `[tool.pytest.ini_options]`를 추가한다.
- `.python-version`(3.11)을 추가한다.
- `uv sync`로 `.venv`와 `uv.lock`을 생성한다.

## 변경 사항

- `pyproject.toml`: `[build-system]`/hatchling 제거, `[tool.uv] package = false` 추가,
  `[dependency-groups] dev = ["pytest>=8.3.0"]` 추가, `[tool.pytest.ini_options]`
  (`pythonpath = ["backend"]`, `testpaths = ["tests"]`) 추가.
- `.python-version` 추가 (3.11).
- `uv sync` 실행으로 `.venv`, `uv.lock` 생성 (둘 다 `.gitignore`/커밋 대상 기준에 따라 `.venv`는
  추적하지 않고, `uv.lock`은 커밋 대상이다).

## 검증

- `uv sync` 성공 (Python 3.11.15 venv 생성, pytest 등 6개 패키지 설치).
- `uv run pytest --collect-only -q` 실행 — 아직 테스트 파일이 없어 "no tests collected"만 확인
  (오류 아님, Step 1 구현 후 실제 테스트 추가 예정).

===================================
시작 시간: 2026-09-21 08:06:48 KST

## 작업 목적

Step 구현마다 "무엇을 만들지"(`docs/ROADMAP.md`)와는 별개로 "지금 이 Step을 어떻게 구현할지"를
사용자가 먼저 읽고 이해한 뒤 구현을 승인하는 절차가 필요해져, 이를 `dev_step.md` 규칙으로
`CLAUDE.md`에 추가한다.

## 요약 계획

- `CLAUDE.md`에 "Step 개발 프로세스(dev_step.md)" 절을 추가한다: Step 시작 전 루트에
  `dev_step.md` 작성 → 사용자 승인 후 구현 → Step 완료 확인 시 `HISTORY`/`HANDOFF` 갱신 후
  `dev_step.md` 삭제 → 다음 Step 문서로 교체.
- `.agent/README.md`의 문서 역할 목록과 작업 시작 절차에 `dev_step.md`를 반영한다.
- 루트 `README.md`의 문서 표에도 `dev_step.md`를 추가한다.

## 변경 사항

- `CLAUDE.md`: "에이전트 공통 작업 지침" 아래에 "### Step 개발 프로세스 (`dev_step.md`)" 절 추가.
- `.agent/README.md`: "문서 역할"에 `dev_step.md` 설명 추가, "작업 시작 절차"에 `dev_step.md`
  존재 확인 단계 추가.
- `README.md`: 문서 표에 `dev_step.md` 행 추가.
- 새 규칙을 바로 적용해 Step 1용 루트 `dev_step.md`를 작성했다 (`dev_step.md` 자체는
  HANDOFF.md와 같은 성격의 "현재 상태" 문서라 이후 갱신/삭제는 별도 HISTORY 항목을 남기지 않는다).

## 검증

- 문서 변경뿐이라 코드 검증 대상은 없다.
- `CLAUDE.md`, `.agent/README.md`, `README.md` 세 문서가 서로 모순되지 않는지 육안으로 확인했다.

===================================
시작 시간: 2026-09-21 17:18:21 KST

## 작업 목적

사용자가 루트 `dev_step.md`(Step 1 설계)를 바탕으로 구현을 요청해, `docs/ROADMAP.md` Step 1
"가장 작은 Coding Agent"(Agent Loop + Tool 6종 + 최소 CLI)를 실제 코드로 구현한다.

## 요약 계획

- `dev_step.md`의 구현 순서대로 진행: 인터페이스(`llm/base.py`, `tools/registry.py`) → Tool 6종과
  단위 테스트 → System Prompt → Agent Loop와 Fake LLM 테스트 → OpenAI-compatible Provider →
  `runtime.py`/`main.py` 연결.
- 실제 LLM 접속 정보(`.env`)가 없으므로 자동 테스트와 가짜 OpenAI-compatible 서버로 검증하고,
  실제 LLM을 쓰는 Test A/B/C는 사용자 수동 테스트로 남긴다.

## 변경 사항

- `backend/llm/base.py`: `LLMProvider`(Protocol), `LLMResponse`, `ToolCall`(`arguments_error` 포함),
  `LLMError` 정의.
- `backend/llm/openai_compatible.py`: `httpx`로 `POST {base_url}/chat/completions` 호출
  (`tool_choice="auto"`). 깨진 Tool 인자 JSON은 예외 대신 `arguments_error`로 표시하고,
  네트워크/HTTP/응답 형식 오류는 `LLMError`로 변환.
- `backend/tools/registry.py`: `ToolResult`(`as_text()`), `ToolRegistry(base_dir)`
  (`register`/`get_schemas`/`execute(name, arguments, *, command_timeout)`),
  Tool 6종의 설명·JSON 스키마를 등록하는 `build_default_registry()`. 없는 Tool, 필수 인자 누락,
  Tool 내부 예외는 모두 `ToolResult(ok=False)`로 반환.
- `backend/tools/file.py`: `list_files`/`read_file`/`write_file`/`edit_file`. 모든 경로를
  `base_dir` 하위로 제한(`resolve_path`), UTF-8 실패 시 OS 기본 인코딩(cp949 등)으로 재시도,
  `edit_file`은 CRLF 줄바꿈과 원래 인코딩 보존 및 `old_string` 유일성 검사.
- `backend/tools/search.py`: `search_files`(내용/파일명 정규식 검색, smart-case, `file_glob`,
  `.git`/`.venv` 등 제외, 잘못된 정규식은 문자열 검색으로 대체).
- `backend/tools/shell.py`: `run_command`. timeout 시 자식 프로세스까지 종료(Windows `taskkill /T`,
  그 외 프로세스 그룹 kill), stdin 차단, 출력 길이 제한, 종료 코드 0이 아니면 `ok=False`.
- `backend/agent/prompts.py`: 실행 환경(작업 디렉터리/OS/셸)을 채우는 `build_system_prompt()`.
- `backend/agent/loop.py`: `run_agent_loop()`와 안전장치(`max_iterations`, `command_timeout`,
  `max_consecutive_errors`), `on_event` 이벤트 5종(`iteration`/`assistant`/`tool_call`/
  `tool_result`/`stopped`).
- `backend/agent/runtime.py`: 저장소 루트 `.env`를 읽어 Provider·Registry·안전장치를 조립하는
  `build_runtime()`, 설정 문제는 `RuntimeConfigError`.
- `backend/main.py`: 최소 CLI (`--dir`, `--full`, 종료 코드 0/1/2). Tool Trace를 stdout에 출력.
- `tests/test_tools.py`, `tests/test_agent_loop.py`, `tests/test_openai_compatible.py` 신규 추가.
- `pyproject.toml`/`uv.lock`: `httpx`, `python-dotenv` 의존성 추가. `.env.example`: 주석을 현재
  동작에 맞게 갱신하고 선택 항목 `LLM_TEMPERATURE` 추가. `.gitignore`: 수동 테스트용
  `playground/` 제외.
- 문서: `README.md`(현재 상태, 실행 방법), `CLAUDE.md`(현재 상태 문장), `tests/README.md`,
  `dev_step.md`(설계와 달라진 부분을 "[구현 반영]"으로 표시)를 구현에 맞게 갱신.

## 검증

- `uv run pytest --basetemp=<접근 가능한 임시 폴더>`: 48개 통과 (Tool 30, Agent Loop 11,
  Provider 7). Agent Loop 테스트에는 실제 Tool로 Test C 흐름
  (`run → error → read → edit → run → success`)을 재현하는 항목이 포함된다.
- 옵션 없는 `uv run pytest`는 구현 작업을 한 환경에서 40개가 `tmp_path` 준비 단계의
  `PermissionError`로 실패했다. 원인은 OS 임시 폴더의 기존 `pytest-of-<사용자명>` 디렉터리에
  접근 권한이 없는 것이며(ACL 조회도 거부됨), SHYNE 코드와는 무관하다. 사용자 터미널에서도
  재현되는지는 아직 확인하지 못했다.
- 가짜 OpenAI-compatible HTTP 서버를 임시로 띄워 `backend/main.py` CLI를 끝까지 실행:
  CLI → `build_runtime` → Provider → Agent Loop → Tool 경로로 Test C 흐름이 동작하고 오류가 있던
  파일이 실제로 수정돼 정상 실행되는 것을 확인했다. `LLM_PROVIDER` 미설정(종료 코드 2), LLM
  서버 연결 불가(종료 코드 1) 메시지도 확인했다.
- 실제 LLM(vLLM/OpenAI)을 연결한 Test A/B/C는 접속 정보가 없어 수행하지 못했다 (사용자 수동
  테스트 대상).
