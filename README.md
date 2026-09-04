# SHYNE

**S**hawn + **Hy**ein — "문제를 밝혀주는 Agent" shine을 연상한 이름. 로컬 LLM(사내/IDC vLLM)
또는 외부 API LLM(OpenAI, Anthropic)을 선택적으로 연결해 쓸 수 있는 Codex / Claude Code 스타일의
**Local / Private Coding Agent**를 자체 구현하는 프로젝트입니다.

## 현재 상태

Step 1(Agent Loop + 최소 Tool 6종: `list_files`, `read_file`, `search_files`, `write_file`,
`edit_file`, `run_command`) 구현 직전 단계입니다. 지금은 디렉터리 구조와 문서 체계만 갖춰져
있고 실행 가능한 코드는 아직 없습니다. 실시간 진행 상태는 [`.agent/HANDOFF.md`](.agent/HANDOFF.md)를 확인하세요.

## 프로젝트 구조

```text
SHYNE/
├─ backend/               # Agent Runtime, LLM Provider, Tool, API (Step 1부터 구현)
│  ├─ agent/               # Agent Loop, Task State, System Prompt
│  ├─ llm/                 # LLM Provider 추상화 (vLLM/OpenAI-compatible)
│  ├─ tools/                # list_files/read_file/search_files/write_file/edit_file/run_command
│  └─ api/                  # Step 2 UI가 호출할 FastAPI 라우터
├─ frontend/               # Step 2 Debug UI 자리 (chat / tool-trace / diff-viewer)
├─ config/                 # config.yaml (Provider·안전장치 기본값)
├─ benchmarks/ prompts/ results/  # OpenCode/Codex/Claude Code 비교 실험 자산
├─ tests/
├─ docs/                   # 로드맵, 변경 이력, 배포/PC 이전 TODO
├─ .agent/                 # PC와 세션 사이의 최신 작업 인계 정보
├─ CLAUDE.md               # Codex와 Claude Code의 공통 프로젝트 지침
├─ AGENTS.md               # Codex가 CLAUDE.md를 읽도록 연결하는 진입 지침
└─ pyproject.toml
```

## 프로젝트 문서와 작업 인계

코드와 함께 개발 맥락도 Git으로 공유할 수 있도록 문서 역할을 분리합니다
([Agent_CADian](../Agent_CADian) 프로젝트와 같은 방식).

| 파일 | 내용 | 갱신 시점 |
|---|---|---|
| `AGENTS.md` | Codex가 `CLAUDE.md`를 읽도록 연결하는 진입 지침 | 공통 지침 연결 방식이 바뀔 때 |
| `CLAUDE.md` | Codex와 Claude Code가 공유하는 개발·문서·검증 규칙과 현재 아키텍처 | 안정적인 프로젝트 규칙이 바뀔 때 |
| `.agent/README.md` | 작업 인계 문서의 작성법, Git 동기화 절차와 금지 정보 | 인계 운영 방식이 바뀔 때 |
| `.agent/HANDOFF.md` | 지금까지 완료한 내용, 현재 문제, 다음 작업과 마지막 검증 | 실제 변경 작업을 마치거나 중단할 때마다 최신 상태로 덮어쓰기 |
| `docs/ROADMAP.md` | SHYNE의 장기 방향, Step 1~13 구현 로드맵, 비교 실험 방법론 | 장기 방향이나 우선순위가 바뀔 때 |
| `docs/DEPLOYMENT_TODO.md` | 다른 PC(집/노트북) 이전, vLLM 연결 등 배포 관련 남은 작업 | 해당 작업의 상태가 바뀔 때 |
| `docs/HISTORY.md` | 실제 코드·설정·파일 구조·프로젝트 설계의 완료된 변경 이력 | 실제 변경이 발생했을 때 끝에 누적 |

### 다른 PC에서 작업 이어가기

```text
회사 PC에서 작업
  -> HISTORY 누적 + HANDOFF 갱신
  -> 사용자가 commit/push
  -> 다른 PC에서 pull
  -> Codex 또는 Claude Code가 HANDOFF와 실제 코드 확인
  -> 작업 재개
```

여러 PC에서 같은 브랜치를 동시에 수정하면 인계 문서도 충돌할 수 있으므로, 장비를 옮기기 전에
기존 PC의 작업을 commit/push하고 새 PC에서 pull한 뒤 시작하는 방식을 권장합니다. `.agent/`에는
API 키, 토큰, `.env` 내용, 회사 내부 비밀, 사용자별 절대 경로를 기록하지 않습니다. 자세한 절차는
[`docs/DEPLOYMENT_TODO.md`](docs/DEPLOYMENT_TODO.md)를 참고하세요.

## 실행

아직 실행 가능한 코드가 없습니다. Step 1 구현이 시작되면 이 절을 채웁니다.
