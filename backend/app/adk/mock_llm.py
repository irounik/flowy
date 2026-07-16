"""Mock LLM responses for development and demos."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def mock_llm_complete(
    prompt: str,
    model: str = "gemini-2.5-flash",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Simulate an LLM call with a short delay and structured response."""
    await asyncio.sleep(0.8)
    context = context or {}

    if "invoice" in prompt.lower() or "invoice" in str(context).lower():
        summary = (
            "Mock LLM: Invoice from Acme Corp for $1,250.00 USD, due August 1, 2026. "
            "Recommended action: approve for payment processing."
        )
    elif "research" in prompt.lower() or "search" in str(context).lower():
        summary = (
            "Mock LLM: Research brief — AI agent workflows enable async orchestration of "
            "LLM reasoning, tool calls, and human approvals across long-running processes."
        )
    else:
        summary = (
            f"Mock LLM ({model}): Processed prompt and generated structured output. "
            f"Input context keys: {list(context.keys())[:5]}"
        )

    logger.info("mock llm response", extra={"model": model, "prompt_len": len(prompt)})
    return {
        "model": model,
        "mock": True,
        "summary": summary,
        "tokens": {"input": len(prompt) // 4, "output": len(summary) // 4},
    }
