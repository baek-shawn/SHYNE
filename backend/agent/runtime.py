"""Agent Runtime 조립 지점.

책임: 설정(.env)을 읽어 LLM Provider, Tool Registry, Agent Loop 안전장치 값을 조립한다.
CLI/UI/API 계층은 이 모듈을 통해서만 Agent를 구성하고, 반복 로직 자체는 loop.py에 둔다.

    llm, tools, settings = build_runtime(base_dir)
    answer = run_agent_loop(prompt, llm, tools, **settings)

Step 3에서 `config/config.yaml`과 Anthropic 등 다른 Provider 선택을, Step 4에서 Permission
Manager를 여기에 연결할 예정이다.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from llm.base import LLMProvider
from llm.openai_compatible import OpenAICompatibleProvider
from tools.registry import ToolRegistry, build_default_registry

# SHYNE 저장소 루트. `.env`는 Agent의 작업 디렉터리(base_dir)가 아니라 항상 여기서 읽는다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"


class RuntimeConfigError(Exception):
    """설정이 없거나 잘못돼서 Agent를 구성할 수 없을 때 사용한다."""


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _env_positive_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeConfigError(f"{name}은 정수여야 합니다: {raw!r}")
    if value < 1:
        raise RuntimeConfigError(f"{name}은 1 이상이어야 합니다: {value}")
    return value


def _build_provider() -> LLMProvider:
    provider = _env("LLM_PROVIDER").lower() or "none"

    if provider == "none":
        raise RuntimeConfigError(
            "LLM_PROVIDER가 설정되지 않았습니다. `.env.example`을 `.env`로 복사한 뒤 LLM_PROVIDER,"
            " LLM_BASE_URL, LLM_API_KEY, LLM_MODEL을 채워주세요."
        )
    if provider == "anthropic":
        raise RuntimeConfigError("anthropic Provider는 아직 구현되지 않았습니다 (ROADMAP Step 3 예정).")
    if provider not in ("openai", "vllm"):
        raise RuntimeConfigError(f"알 수 없는 LLM_PROVIDER입니다: {provider} (openai | vllm 중 하나)")

    # openai와 vllm은 같은 OpenAI-compatible API를 쓰므로 접속 정보만 다르다.
    base_url = _env("LLM_BASE_URL") or (OPENAI_DEFAULT_BASE_URL if provider == "openai" else "")
    model = _env("LLM_MODEL")
    if not base_url:
        raise RuntimeConfigError("LLM_BASE_URL이 비어 있습니다. 예: http://localhost:8000/v1")
    if not model:
        raise RuntimeConfigError("LLM_MODEL이 비어 있습니다. 서버에 올라가 있는 모델 이름을 지정하세요.")

    temperature = None
    if _env("LLM_TEMPERATURE"):
        try:
            temperature = float(_env("LLM_TEMPERATURE"))
        except ValueError:
            raise RuntimeConfigError(f"LLM_TEMPERATURE는 숫자여야 합니다: {_env('LLM_TEMPERATURE')!r}")

    return OpenAICompatibleProvider(base_url, _env("LLM_API_KEY"), model, temperature=temperature)


def build_runtime(base_dir: Path) -> tuple[LLMProvider, ToolRegistry, dict]:
    """(LLM Provider, Tool Registry, run_agent_loop에 넘길 안전장치 설정)을 만든다."""
    # 이미 설정된 실제 환경 변수가 .env보다 우선한다 (load_dotenv 기본 동작).
    load_dotenv(PROJECT_ROOT / ".env")

    base_dir = Path(base_dir).resolve()
    if not base_dir.is_dir():
        raise RuntimeConfigError(f"작업 디렉터리가 없습니다: {base_dir}")

    llm = _build_provider()
    tools = build_default_registry(base_dir)
    settings = {
        "max_iterations": _env_positive_int("AGENT_MAX_ITERATIONS", 20),
        "command_timeout": _env_positive_int("AGENT_COMMAND_TIMEOUT", 60),
        "max_consecutive_errors": _env_positive_int("AGENT_MAX_CONSECUTIVE_ERRORS", 3),
    }
    return llm, tools, settings
