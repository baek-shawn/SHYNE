# 배포 / 다른 PC 이전 TODO

이 문서는 SHYNE을 회사, 집, 노트북 등 다른 PC에서 이어서 개발하거나, 나중에 사내/IDC vLLM
서버와 실제로 연결할 때 필요한 남은 작업을 관리한다. 지금은 Step 1 착수 전 구조 설정 단계라
실제 배포 대상이 없고, 아래는 앞으로 채워나갈 체크리스트다.

## 다른 PC에서 이어서 개발하기

현재 프로젝트는 코드가 없는 구조/문서 단계이므로 절차가 단순하다.

1. Git으로 최신 커밋을 pull 한다.
2. `.agent/HANDOFF.md`를 읽고 현재 상태를 확인한다.
3. Python 3.11+ 와 `uv`(권장, [Agent_CADian](../../Agent_CADian)과 동일한 도구)가 설치되어 있는지 확인한다.
4. `.env.example`을 복사해 `.env`를 만들고, 사용할 LLM Provider 값을 채운다 (Step 3 구현 전에는
   `LLM_PROVIDER=none`으로 둔다).
5. Codex 또는 Claude Code에 "이전 작업 이어서 해"라고 요청한다 — 공통 지침(`CLAUDE.md`)에 따라
   `.agent/HANDOFF.md`, `git status`, 실제 코드를 대조한 뒤 이어간다.

## 아직 정하지 않은 항목

- [ ] 사내/IDC vLLM 서버 접속 방식 (사설망 직접 연결 vs Tailscale/WireGuard vs reverse proxy) —
      Agent_CADian의 서버/클라이언트 분리 모드 경험을 참고할 수 있다.
- [ ] 여러 PC에서 같은 `.env`를 안전하게 공유할 방법 (현재는 PC마다 개별 작성).
- [ ] `config/config.yaml`과 `.env`의 책임 분리 기준 확정 (민감값은 `.env`, 그 외 기본값은 `config.yaml`).
- [ ] 패키지 매니저 최종 확정: 지금은 `pyproject.toml`만 두었고 `uv`/`pip` 중 어느 쪽 워크플로를
      기본 문서화할지 Step 1 구현 시작 시 정한다.

## 나중에 다룰 것 (Step 10 Confidential Mode와 연결)

민감한 고객 데이터를 다루게 되면 `docs/ROADMAP.md` Step 10의 Confidential Mode(외부 LLM/MCP/Web
차단, 사내 vLLM·로컬 파일시스템·로컬 셸만 허용)를 배포 설정에도 반영해야 한다. 지금은 해당
단계 이전이라 실제 배포 정책은 없다.
