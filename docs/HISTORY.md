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
