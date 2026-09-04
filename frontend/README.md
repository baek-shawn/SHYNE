# frontend

Step 2("Agent 행동을 UI에서 확인")에서 채워질 Debug UI 자리다. 목표는 예쁜 UI가 아니라
Agent가 무엇을 하고 있는지 쉽게 확인하는 것이며, 자세한 내용은 [docs/ROADMAP.md](../docs/ROADMAP.md)의
Step 2를 참고한다.

프레임워크(React 또는 간단한 정적 Web UI)는 아직 정하지 않았다. Step 1(Agent Loop + 최소 Tool)이
안정화된 뒤 이 폴더를 채운다.

- `chat/`: 대화 입력/출력 화면
- `tool-trace/`: Tool 이름·인자·결과·실행 순서를 보여주는 화면
- `diff-viewer/`: 파일 수정 전/후 Diff 화면 (Step 5)
