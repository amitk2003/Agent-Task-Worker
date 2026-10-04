"""Email tools for searching, reading, and sending emails."""

from mock_env.email_system import EmailSystem
from tools.base import BaseTool, ToolResult


class SearchEmailsTool(BaseTool):

    def __init__(self, email_system: EmailSystem):
        self._system = email_system

    @property
    def name(self) -> str:
        return "search_emails"

    @property
    def description(self) -> str:
        return (
            "Search incoming emails in the inbox by keyword, subject, or sender address. "
            "Returns a list of matching emails with ID, sender, subject, and date."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to match against email subject or body.",
                },
                "sender": {
                    "type": "string",
                    "description": "Optional sender email address to filter by.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        sender = kwargs.get("sender", "")
        results = self._system.search_emails(query=query, sender=sender)
        return ToolResult(
            success=True,
            data={"emails": results, "count": len(results)},
            message=f"Found {len(results)} email(s) matching query='{query}' sender='{sender}'.",
        )


class ReadEmailTool(BaseTool):

    def __init__(self, email_system: EmailSystem):
        self._system = email_system

    @property
    def name(self) -> str:
        return "read_email"

    @property
    def description(self) -> str:
        return (
            "Read the full content and attachment details of a specific email by its ID. "
            "Returns sender, recipient, subject, full body, and attachment metadata."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "email_id": {
                    "type": "string",
                    "description": "The unique email ID (e.g., 'email-001').",
                }
            },
            "required": ["email_id"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        email_id = kwargs.get("email_id", "")
        if not email_id:
            return ToolResult(success=False, error="email_id is required.")

        email_data = self._system.read_email(email_id)
        if not email_data:
            return ToolResult(success=False, error=f"Email '{email_id}' not found.")

        return ToolResult(
            success=True,
            data={"email": email_data},
            message=f"Read email '{email_data['subject']}' from {email_data['sender']}.",
        )


class SendEmailTool(BaseTool):

    def __init__(self, email_system: EmailSystem):
        self._system = email_system

    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return (
            "Send an email to a user, vendor, or manager with task updates, "
            "confirmation of submitted invoices, or audit summaries."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address (e.g. 'manager@company.com').",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line.",
                },
                "body": {
                    "type": "string",
                    "description": "Email message body.",
                },
            },
            "required": ["to", "subject", "body"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")

        if not all([to, subject, body]):
            return ToolResult(success=False, error="All fields required: to, subject, body.")

        sent_record = self._system.send_email(to=to, subject=subject, body=body)
        return ToolResult(
            success=True,
            data={"sent": sent_record},
            message=f"Email successfully sent to {to}: '{subject}'.",
        )
