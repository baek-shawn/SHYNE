# 현재 작업 인계

마지막 갱신: 2026-09-21 17:30:00 KST

## 현재 목표와 상태

`docs/ROADMAP.md`의 Step 1(가장 작은 Coding Agent: Agent Loop + Tool 6종 + 최소 CLI)의 **코드
구현과 자동 테스트는 끝났고, 사용자의 수동 테스트(Test A/B/C)와 완료 확인을 기다리는 상태**다.
실제 LLM 접속 정보(`.env`)가 없어 실제 LLM을 연결한 검증은 아직 한 번도 하지 못했다. Step 1
완료 여부는 사용자가 Test A/B/C를 직접 돌려보고 판단한다 — 그 전까지 루트 `dev_step.md`를
삭제하거나 Step 2 문서로 교체하지 않는다.

## 완료한 작업

- `dev_step.md` 설계대로 Step 1 전체 구현: `backend/llm/{base,openai_compatible}.py`,
  `backend/tools/{registry,file,search,shell}.py`, `backend/agent/{prompts,loop,runtime}.py`,
  `backend/main.py`(최소 CLI: `--dir`, `--full`).
- 자동 테스트 3개 파일 추가: `tests/test_tools.py`, `tests/test_agent_loop.py`,
  `tests/test_openai_compatible.py` (총 48개).
- 의존성 `httpx`, `python-dotenv` 추가(`pyproject.toml`, `uv.lock`). `.env.example` 주석 갱신과
  `LLM_TEMPERATURE` 추가, `.gitignore`에 수동 테스트용 `playground/` 추가.
- 설계와 달라진 부분을 `dev_step.md`에 "[구현 반영]"으로 표시했고, `README.md`, `CLAUDE.md`,
  `tests/README.md`를 구현에 맞게 갱신했다.
- 수동 테스트용으로 `playground/broken.py`(`for` 문 콜론 누락)를 만들어 뒀다. `playground/`는
  Git 제외 대상이라 다른 PC에는 전달되지 않는다 — 필요하면 그 PC에서 다시 만든다.

## 남은 작업

1. **사용자 수동 테스트**: `.env.example`을 `.env`로 복사해 LLM 접속 정보를 채운 뒤
   `tests/README.md`의 Test A → B → C를 `uv run python backend/main.py --dir playground "..."`로
   실행한다. Test C에서 Tool Trace가 `run → error → read → edit → run → success`인지 확인.
2. 수동 테스트에서 나온 문제(Tool 설명/System Prompt 조정, 모델별 tool calling 문제 등)를 고친다.
3. 사용자가 Step 1 완료를 확인하면: `docs/HISTORY.md`/이 문서 갱신 → 루트 `dev_step.md` 삭제 →
   Step 2용 `dev_step.md` 새로 작성 (`CLAUDE.md`의 "Step 개발 프로세스").
4. 커밋은 사용자가 시점을 정해 직접 진행한다 (에이전트가 임의로 커밋하지 않음). 이전 세션의
   문서 변경과 이번 Step 1 구현이 모두 미커밋 상태다.

## 확인된 문제 또는 차단 요인

- **옵션 없는 `uv run pytest`가 구현 작업 환경에서 실패했다**: 48개 중 40개가 `tmp_path` 준비
  단계에서 `PermissionError`. OS 임시 폴더에 예전에 생긴 `pytest-of-<사용자명>` 디렉터리에 접근
  권한이 없는 것이 원인이고(ACL 조회도 거부됨) SHYNE 코드와 무관하다. 에이전트 실행 환경의
  제한일 수도, 그 폴더의 실제 권한 문제일 수도 있어 **사용자 터미널에서 재현되는지 확인이
  필요하다**. 재현되면 (a) 관리자 권한으로 그 폴더를 지우거나 (b)
  `uv run pytest --basetemp=.pytest_tmp`처럼 접근 가능한 폴더를 지정한다. 공용 설정
  (`pyproject.toml`의 `addopts`)에 우회책을 넣을지는 사용자가 결정한다.
- 실제 LLM 미검증. 특히 vLLM은 서버를 `--enable-auto-tool-choice --tool-call-parser <parser>`로
  띄워야 tool calling이 동작한다 (없으면 HTTP 400이 CLI에 그대로 표시된다).
- tool calling을 지원하지 않는 모델/서버를 위한 fallback(응답 텍스트에서 Tool 호출을 해석하는
  방식 등)은 `dev_step.md` 범위 밖이라 구현하지 않았다. `CLAUDE.md` 아키텍처 절의 "LLM이 Tool을
  직접 호출하지 않아도 동작" 원칙을 Step 1에 어디까지 적용할지는 수동 테스트 결과를 보고 정한다.
- `docs/HISTORY.md`의 직전 기록(2026-09-21 "08:06:48 KST")은 실제로는 UTC 시각으로 보인다
  (파일 수정 시각 기준 KST 17시대). 기존 기록은 임의로 고치지 않았다.

## 관련 파일

- `dev_step.md` (루트, Step 1 설계 + "[구현 반영]" — Step 1 완료 확인 시 삭제 대상)
- `backend/agent/loop.py`, `backend/agent/runtime.py`, `backend/main.py`
- `backend/tools/registry.py` (새 Tool 등록 위치: `build_default_registry()`)
- `backend/llm/openai_compatible.py`
- `tests/README.md` (자동/수동 테스트 방법)
- `.env.example`

## 마지막 검증

- `uv run pytest --basetemp=<접근 가능한 임시 폴더>` — 48 passed.
- `uv run pytest`(옵션 없음) — 8 passed, 40 errors (위 "확인된 문제"의 임시 폴더 권한 문제).
- 가짜 OpenAI-compatible 서버로 `backend/main.py` CLI 전체 경로 실행 — Test C 흐름 동작, 대상
  파일이 실제로 수정돼 정상 실행됨. 설정 누락(종료 코드 2), 서버 연결 불가(종료 코드 1) 확인.
- 실제 LLM을 연결한 Test A/B/C — 미수행.
