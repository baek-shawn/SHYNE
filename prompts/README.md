# prompts

`benchmarks/`의 각 테스트 시나리오에 사용할 공통 Prompt를 보관하는 폴더다. MyAgent와
OpenCode/Codex/Claude Code에 동일한 문장을 입력해야 Harness 차이를 비교할 수 있으므로,
비교 실험을 시작하면 아래처럼 시나리오별 Prompt를 파일로 고정한다.

```text
prompts/
├── file_create.md
├── bug_fix.md
├── multi_file.md
├── retry.md
├── permission.md
└── long_context.md
```

시나리오 정의는 [docs/ROADMAP.md](../docs/ROADMAP.md)를 참고한다.
