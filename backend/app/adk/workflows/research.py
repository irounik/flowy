"""Research workflow definition using Google ADK 2.0."""

from typing import Any

from google.adk import Agent, Workflow

from app.adk.prompts.system import RESEARCH_SUMMARY_PROMPT


async def search_node(query: str) -> dict[str, Any]:
    from app.adk.tools.python_tools import web_search

    return await web_search(query)


def llm_summary_node(search_results: dict[str, Any]) -> str:
    query = search_results.get("query", "")
    results_text = "\n".join(
        f"- {r['title']}: {r['snippet']}" for r in search_results.get("results", [])
    )
    return f"Research brief for '{query}':\n{results_text}"


async def slack_node(summary: str) -> dict[str, Any]:
    from app.adk.tools.python_tools import send_slack_notification

    return await send_slack_notification(f"Research complete: {summary[:200]}...")


def build_research_workflow() -> Workflow:
    """Build the ADK graph-based research workflow."""
    summarizer = Agent(
        name="research_summarizer",
        model="gemini-2.5-flash",
        instruction=RESEARCH_SUMMARY_PROMPT,
    )

    return Workflow(
        name="research",
        edges=[
            ("START", search_node, llm_summary_node),
            ("START", llm_summary_node, slack_node),
        ],
        agents=[summarizer],
    )
