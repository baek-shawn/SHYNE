# tests

Step 1 구현이 시작되면 `pytest` 기반 자동화 테스트를 이 폴더에 추가한다. 그 전까지는
[docs/ROADMAP.md](../docs/ROADMAP.md)의 "초기 테스트 시나리오"(Test A/B/C)를 수동으로 확인한다.

- Test A — 파일 생성: `write_file` Tool로 `test.py`를 만들고 hello world를 출력하는지 확인.
- Test B — 실행: `run_command`로 `test.py`를 실행하고 실제 stdout을 확인.
- Test C — 오류 수정 Agent Loop: `run → error → read → edit → run → success` 흐름이 실제로
  이어지는지 확인. **Test C 성공 = 기본 Agent Harness 1차 구현 완료 기준.**
