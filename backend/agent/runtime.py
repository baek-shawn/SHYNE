"""Agent Runtime 조립 지점 (placeholder).

책임: LLM Provider, Tool Registry, Context Manager, Permission Manager를 하나의
Agent Runtime으로 조립한다. UI/API 계층은 이 모듈을 통해서만 Agent를 호출한다.

설계 메모 (Step 1):
- runtime.py는 loop.py의 Agent Loop 함수에 필요한 의존성(LLMProvider 인스턴스,
  ToolRegistry 인스턴스, max_iterations/command_timeout/max_consecutive_errors 설정)을
  구성해서 넘겨주는 역할만 한다. Agent Loop 자체의 반복 로직은 loop.py에 둔다.
"""
