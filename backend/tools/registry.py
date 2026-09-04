"""Tool Registry (placeholder).

책임: 도구 이름 -> 실행 함수, 그리고 LLM에 전달할 도구 설명/JSON 스키마를
한 곳에서 관리한다. Agent Loop는 이 Registry를 통해서만 도구를 호출한다.

Step 1 대상 도구: list_files, read_file, search_files, edit_file, write_file, run_command.
Step 4(Tool Permission)에서 AUTO/CONFIRM/BLOCK 등급을 이 Registry에 연결할 예정이다.
"""
