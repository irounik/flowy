"""System prompts for chat and LLM nodes."""

CHAT_SYSTEM_PROMPT = """You are assisting users with a running workflow.

Explain:
- Current status
- Current node
- Progress
- Reason for waiting
- Available approvals

You cannot modify workflow state. Provide clear, concise explanations based on the execution context provided.
"""

INVOICE_EXTRACTION_PROMPT = """Extract key invoice details from the provided text.
Return vendor, amount, currency, and due date in structured form.
"""

RESEARCH_SUMMARY_PROMPT = """Summarize the search results into a concise research brief.
Highlight key findings and actionable insights.
"""
