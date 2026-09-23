# CLAUDE.md

이 파일은 Claude Code와 Codex가 이 저장소에서 작업할 때 공유하는 프로젝트 지침이다.

## 에이전트 공통 작업 지침

### Markdown 작성 언어

- 새로 만들거나 수정하는 Markdown 문서의 제목, 설명, 계획, 작업 기록은 한국어를 기본으로 작성한다.
- 코드 식별자, API 이름, 명령어, 환경 변수, 파일명, 라이브러리 고유명처럼 정확한 표기가 필요한 경우에만 영어를 사용한다.
- 자연스러운 한국어 표현이 가능한 내용을 습관적으로 영어로 작성하지 않는다.
- 기존 문서를 수정할 때도 주변 문맥과 용어를 존중하면서 위 원칙을 적용한다.

### 작업 시작과 문서 선택

- 실제 코드나 프로젝트 설계를 조사·계획·변경하기 전에 `.agent/README.md`와 `.agent/HANDOFF.md`를 읽고 `git status`와 최근 커밋을 확인한다.
- `docs/HISTORY.md`는 최신 기록을 먼저 확인하고, 오래된 세부 내용은 현재 작업에 필요할 때만 찾아 읽는다.
- 제품 방향이나 장기 설계를 다룰 때만 `docs/ROADMAP.md`를 읽는다.
- 배포 또는 다른 PC(집/노트북)로의 이전을 다룰 때만 `docs/DEPLOYMENT_TODO.md`를 읽는다.
- 현재 코드와 Git 상태가 작업 인계 문서와 다르면 코드와 Git을 기준으로 판단하고, 작업 완료 시 인계 문서를 바로잡는다.
- 현재 작업과 관계없는 긴 Markdown 문서를 무조건 전부 읽지 않는다.

### 작업 인계와 변경 이력

- 실제 코드, 설정, 파일 구조, 문서 구조 또는 프로젝트 설계가 변경되면 작업 완료 전에 `docs/HISTORY.md`에 요약을 추가하고 `.agent/HANDOFF.md`를 최신 상태로 갱신한다.
- 작업을 끝내지 못하고 다른 환경이나 다음 세션으로 넘길 때도 `.agent/HANDOFF.md`에 완료 내용, 현재 문제와 다음 작업을 갱신한다.
- 단순 질문과 답변, 상태 확인, 설명 요청, 읽기 전용 조사, 변경 없는 진단과 검토는 두 문서 모두 갱신하지 않는다.
- 기록 형식, 갱신 기준과 금지 정보는 `.agent/README.md`를 따른다.
- 사용자가 명시적으로 요청하지 않았다면 에이전트가 임의로 commit 또는 push하지 않는다.

### Step 개발 프로세스 (`dev_step.md`)

`docs/ROADMAP.md`는 Step별로 "무엇을" 만들지 정의한다. `dev_step.md`는 지금 진행 중인 Step
하나를 "어떻게" 구현할지 정의하는, 루트에 두는 단일 최신 문서다(HANDOFF.md와 같은 성격 — 계속
누적하지 않고 항상 현재 Step 하나만 담는다).

1. 새 Step 구현에 들어가기 전에 루트에 `dev_step.md`를 만들거나 갱신한다. 대상 Step, 목표,
   건드릴 파일 목록과 파일별 작업, 인터페이스/함수 설계, 구현 순서, 테스트 방법, 완료 조건을
   상세히 적는다. 이 문서 작성 단계에서는 실제 코드를 작성하지 않는다.
2. 사용자가 `dev_step.md`를 읽고 이해한 뒤 명시적으로 구현을 요청하면 그 내용에 따라 코드를
   작성한다. 사용자 승인 전에 먼저 구현을 시작하지 않는다.
3. 사용자가 해당 Step의 테스트를 마치고 완료를 확인하면: 먼저 위 "작업 인계와 변경 이력" 규칙대로
   `docs/HISTORY.md`에 요약을 추가하고 `.agent/HANDOFF.md`를 갱신한 뒤, `dev_step.md`를 삭제하고
   다음 Step에 대한 새 `dev_step.md`를 같은 방식으로 작성한다.
4. 끝난 Step의 상세 구현 기록은 `docs/HISTORY.md`와 커밋 이력에 남기고, `dev_step.md` 자체에는
   과거 Step 내용을 남기지 않는다.

## 이 프로젝트는

SHYNE은 로컬 LLM(사내/IDC vLLM)이나 외부 API LLM(OpenAI, Anthropic)을 선택적으로 연결해 쓸 수 있는
**Codex / Claude Code 스타일의 Coding Agent**를 자체 구현하는 프로젝트입니다. 채팅 UI가 목적이
아니라, 자연어 요청을 이해하고 파일을 탐색·수정하고 명령을 실행한 뒤 결과를 다시 확인하는
**Agent Loop**가 핵심입니다. 상세 배경과 단계별 로드맵(Step 1~13), OpenCode/Codex/Claude Code와의
비교 실험 방법론은 [`docs/ROADMAP.md`](docs/ROADMAP.md)에 있습니다.

Step 1(Agent Loop + 최소 Tool 6종 + 최소 CLI)의 코드가 구현돼 있습니다. 어느 Step까지 완료
확인됐는지 등 현재 진행 상태는 항상 [`.agent/HANDOFF.md`](.agent/HANDOFF.md)를 기준으로
판단하세요.

## 아키텍처 (권장 구조, `docs/ROADMAP.md` 기준)

```text
backend/
├── main.py           # 진입점 (Step 1 최소 CLI, Step 2에서 FastAPI 앱 구성)
├── agent/             # Agent Runtime: Loop, Task State, System Prompt
│   ├── runtime.py      # LLM Provider + Tool Registry + 설정을 조립
│   ├── loop.py         # 핵심 Agent Loop (max_iterations/timeout/consecutive_errors 안전장치)
│   ├── state.py        # Task 진행 상태 (Step 8)
│   └── prompts.py      # System Prompt, 프로젝트별 지침(Step 7) 병합
├── llm/                # LLM Provider 추상화 (Agent Loop는 구체 Provider를 모름)
│   ├── base.py          # LLMProvider 인터페이스: generate(messages, tools)
│   └── openai_compatible.py  # vLLM/Ollama/LM Studio/OpenAI 호환 구현체
├── tools/              # list_files/read_file/search_files/write_file/edit_file/run_command
│   ├── registry.py      # 도구 이름 -> 함수, LLM용 설명/JSON 스키마 (Step 4 Permission 연결 지점)
│   ├── file.py
│   ├── search.py
│   └── shell.py         # run_command, command_timeout 적용 대상
└── api/                # UI(Step 2)가 Agent Runtime을 호출하는 FastAPI 라우터
    └── chat.py

frontend/    # Step 2 Debug UI (chat / tool-trace / diff-viewer), 아직 프레임워크 미정
config/      # config.yaml (Provider 종류, Agent Loop 안전장치 기본값 — Step 3에서 실제 사용 시작)
docs/        # ROADMAP(장기 계획) / HISTORY(변경 이력) / DEPLOYMENT_TODO(PC 이전)
.agent/      # HANDOFF(현재 상태) — 여러 PC 간 Git 기반 작업 인계
benchmarks/  # OpenCode/Codex/Claude Code 비교용 테스트 프로젝트 자산
prompts/     # 비교 실험에 쓰는 공통 Prompt
results/     # 비교 실험 결과 기록
```

새 Tool을 추가할 때는 `tools/registry.py`에 등록하고, LLM이 Tool을 직접 호출하지 않아도(키워드
fallback 등) 항상 동작하도록 만드세요 — `docs/ROADMAP.md`의 원칙 4번(수정 후 반드시 실행/테스트
검증)과 원칙 6번(Local LLM과 외부 API LLM을 Provider 계층에서 분리)을 지키는 것이 이 구조의
핵심입니다.