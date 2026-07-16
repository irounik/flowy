"""Invoice approval workflow definition using Google ADK 2.0."""

from typing import Any

from google.adk import Agent, Workflow
from google.adk.events import RequestInput

from app.adk.prompts.system import INVOICE_EXTRACTION_PROMPT


def invoice_extraction_node(invoice_text: str) -> dict[str, Any]:
    """Extract invoice data from raw text."""
    from app.adk.tools.python_tools import extract_invoice_data

    return extract_invoice_data(invoice_text)


def summary_node(invoice_data: dict[str, Any]) -> str:
    from app.adk.tools.python_tools import summarize_invoice

    return summarize_invoice(invoice_data)


def human_approval_node(summary: str):
    """Pause workflow for human approval."""
    yield RequestInput(
        interrupt_id="invoice_approval",
        message=f"Please review and approve this invoice:\n\n{summary}",
        payload={"summary": summary},
        response_schema={"decision": "string", "comments": "string"},
    )


def email_node(approval_response: dict[str, Any]) -> dict[str, Any]:
    """Send approval notification email."""
    import asyncio

    from app.adk.tools.python_tools import send_email

    summary = approval_response.get("summary", "Invoice approved")
    return asyncio.get_event_loop().run_until_complete(
        send_email(
            to="approver@example.com",
            subject="Invoice Approved",
            body=f"Invoice approved.\n\n{summary}",
        )
    )


def build_invoice_approval_workflow() -> Workflow:
    """Build the ADK graph-based invoice approval workflow."""
    extraction_agent = Agent(
        name="invoice_extractor",
        model="gemini-2.5-flash",
        instruction=INVOICE_EXTRACTION_PROMPT,
    )

    return Workflow(
        name="invoice_approval",
        edges=[
            ("START", invoice_extraction_node, summary_node),
            ("START", summary_node, human_approval_node),
            ("START", human_approval_node, email_node),
        ],
        agents=[extraction_agent],
    )
