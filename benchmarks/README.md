# benchmarks

MyAgent와 OpenCode/Codex/Claude Code를 같은 조건으로 비교하기 위한 테스트용 프로젝트 자산을
보관하는 폴더다. 비교 원칙과 각 테스트 시나리오는
[docs/ROADMAP.md](../docs/ROADMAP.md)의 "OpenCode / Codex / Claude Code 비교 실험 단계"를 따른다.

Step 1(기본 Agent Loop)이 안정화되고 비교 실험을 실제로 시작할 때 아래 하위 폴더를 채운다.

```text
benchmarks/
├── 01_file_create/
├── 02_bug_fix/
├── 03_multi_file/
├── 04_retry/
├── 05_permission/
└── 06_long_context/
```

각 폴더에는 해당 테스트를 재현하는 데 필요한 최소 프로젝트 파일(오류가 있는 스크립트 등)을 둔다.
