"""LLMProvider 추상 인터페이스 (placeholder).

설계 메모 (Step 1 / Step 3):
- 모든 Provider가 구현해야 할 단일 메서드: `generate(messages, tools) -> LLM 응답
  (tool_call 또는 최종 텍스트)`.
- Agent Loop(agent/loop.py)는 이 인터페이스에만 의존하고 구체 Provider를 모른다.
- 첫 구현체는 llm/openai_compatible.py이며, vLLM/Ollama/LM Studio/OpenAI 호환 API를
  동일한 인터페이스로 다룬다.

아직 클래스/메서드 코드는 작성하지 않았다.
"""
