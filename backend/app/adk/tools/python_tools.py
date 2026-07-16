"""Python tool implementations for workflow nodes."""

import json
import logging
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def calculator(expression: str) -> dict[str, Any]:
    """Safely evaluate basic math expressions."""
    allowed = set("0123456789+-*/(). ")
    if not all(char in allowed for char in expression):
        raise ValueError("Expression contains invalid characters")
    result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307
    return {"expression": expression, "result": result}


def weather_lookup(location: str) -> dict[str, Any]:
    """Stub weather tool for MVP demonstrations."""
    return {
        "location": location,
        "temperature_c": 22,
        "conditions": "partly cloudy",
        "source": "stub",
    }


async def web_search(query: str) -> dict[str, Any]:
    """Stub search tool — replace with real search API in production."""
    return {
        "query": query,
        "results": [
            {"title": f"Result for: {query}", "snippet": "Sample search result for MVP demo."},
            {"title": "Related topic", "snippet": "Additional context from simulated search."},
        ],
    }


async def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send email via SMTP when configured, otherwise log and return stub response."""
    if not settings.smtp_host:
        logger.info("email stub sent", extra={"to": to, "subject": subject})
        return {"status": "stubbed", "to": to, "subject": subject, "body": body}

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_user:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)

    return {"status": "sent", "to": to, "subject": subject}


async def send_slack_notification(message: str, channel: str = "#general") -> dict[str, Any]:
    """Send Slack notification via webhook when configured."""
    if not settings.slack_webhook_url:
        logger.info("slack stub sent", extra={"channel": channel, "message": message})
        return {"status": "stubbed", "channel": channel, "message": message}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.slack_webhook_url,
            json={"text": message, "channel": channel},
        )
        response.raise_for_status()

    return {"status": "sent", "channel": channel, "message": message}


def extract_invoice_data(invoice_text: str) -> dict[str, Any]:
    """Extract structured invoice fields from raw text (MVP stub)."""
    return {
        "vendor": "Acme Corp",
        "amount": 1250.00,
        "currency": "USD",
        "due_date": "2026-08-01",
        "raw_text": invoice_text[:500],
    }


def summarize_invoice(invoice_data: dict[str, Any]) -> str:
    """Generate a human-readable invoice summary."""
    return (
        f"Invoice from {invoice_data.get('vendor', 'Unknown')} "
        f"for {invoice_data.get('amount', 0)} {invoice_data.get('currency', 'USD')}, "
        f"due {invoice_data.get('due_date', 'N/A')}."
    )


def format_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)
