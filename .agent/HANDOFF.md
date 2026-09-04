# 현재 작업 인계

마지막 갱신: 2026-09-04 07:50:56 KST

## 현재 목표와 상태

`docs/ROADMAP.md`의 Step 1(가장 작은 Coding Agent: Agent Loop + `list_files` / `read_file` /
`search_files` / `edit_file` / `write_file` / `run_command`)을 구현하기 직전 단계다. 이번
세션에서는 요청에 따라 **코드는 작성하지 않고** 디렉터리 구조와 문서 체계만 갖췄다. 실제 Agent
Loop, LLM Provider, Tool 로직은 아직 하나도 구현되지 않았다.

## 완료한 작업

- `backend/{agent,llm,tools,api}` 등 기획서의 "권장 초기 프로젝트 구조"를 실제 폴더로 생성하고,
  각 Python 파일을 책임 설명 Docstring만 있는 placeholder로 채웠다.
- `frontend/`, `config/`, `benchmarks/`, `prompts/`, `results/`, `tests/`를 목적을 설명하는
  README와 함께 생성했다 (Step 2 이후 및 비교 실험용, 아직 내용 없음).
- `local_code_agent_development_plan_v2.md`를 `docs/ROADMAP.md`로 이동했다.
- `docs/HISTORY.md`, `docs/DEPLOYMENT_TODO.md`, `.agent/README.md`, `.agent/HANDOFF.md`(이 문서)를
  [Agent_CADian](../../Agent_CADian)과 같은 형식으로 새로 작성했다.
- `CLAUDE.md`에 SHYNE 프로젝트 설명과 아키텍처 절을 추가했다.
- `pyproject.toml`(의존성 미정), `.env.example`, `config/config.yaml`, `.gitignore`를 값 없는
  형식으로 추가하고, 여러 PC 동기화를 위해 `git init`을 실행했다 (커밋은 하지 않음, 이후
  커밋/staging은 사용자가 직접 진행).
- 패키지 매니저를 `uv`로 확정하고 실제 환경을 설치했다: `pyproject.toml`을 Agent_CADian 루트와
  같은 `[tool.uv] package = false` 방식으로 바꾸고, `dev` dependency group(pytest)과
  `[tool.pytest.ini_options]`(`pythonpath=["backend"]`, `testpaths=["tests"]`)를 추가했다.
  `.python-version`(3.11) 추가 후 `uv sync`로 `.venv`(Python 3.11.15)와 `uv.lock`을 생성했다.

## 남은 작업

1. **Step 1 구현**: `backend/llm/base.py`의 LLMProvider 인터페이스, `backend/llm/openai_compatible.py`,
   `backend/tools/{file,search,shell}.py`의 6개 Tool, `backend/agent/loop.py`의 Agent Loop
   (max_iterations=20 / command_timeout=60s / max_consecutive_errors=3)을 실제로 구현한다.
2. `tests/`에 Step 1 성공 조건인 Test C(run → error → read → edit → run → success)를 재현하는
   자동/수동 테스트를 추가한다.
3. Step 1이 성공하면 `docs/ROADMAP.md` Step 2(Debug UI)로 진행한다.
4. 사용자가 커밋 시점을 정하면 이번 구조 설정 커밋을 진행한다 (에이전트가 임의로 커밋하지 않음).

## 확인된 문제 또는 차단 요인

없음. Step 1 착수 전 구조 설정만 완료된 상태다.

## 관련 파일

- `docs/ROADMAP.md` (기존 `local_code_agent_development_plan_v2.md`)
- `docs/DEPLOYMENT_TODO.md`
- `backend/agent/loop.py`, `backend/llm/base.py`, `backend/tools/registry.py` (Step 1에서 채울 자리)
- `CLAUDE.md`

## 마지막 검증

- `uv sync` 성공 (Python 3.11.15 venv 생성).
- `uv run pytest --collect-only -q` — 테스트 파일이 아직 없어 "no tests collected"만 확인
  (오류 아님).
- Agent Loop/Tool 실행 코드가 아직 없어 그 외 검증 대상은 없다.
- Git staging/commit은 사용자가 직접 진행하므로 이 세션에서는 건드리지 않았다.
