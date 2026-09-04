"""Agent Loop (placeholder).

책임: `local_code_agent_development_plan_v2.md` Step 1의 핵심 루프를 구현한다.

    while not finished:
        response = llm(messages, tools)
        if response.tool_call:
            result = execute_tool(response.tool_call)
            messages.append(result)
        else:
            return response

안전장치 (Step 1부터 반드시 포함):
- max_iterations = 20
- command_timeout = 60 seconds
- max_consecutive_errors = 3

아직 구현하지 않음: Planner, Sub Agent, Git 연동, Context 요약.
"""
