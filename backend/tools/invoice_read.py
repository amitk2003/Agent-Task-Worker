"""Tool: Read full details of a specific invoice."""

from mock_env.invoice_portal import InvoicePortal
from tools.base import BaseTool, ToolResult


class ReadInvoiceTool(BaseTool):

    def __init__(self, portal: InvoicePortal):
        self._portal = portal

    @property
    def name(self) -> str:
        return "read_invoice_details"

    @property
    def description(self) -> str:
        return (
            "Read the full details of a specific invoice by its ID. "
            "Returns complete invoice data including line items, amounts, and dates."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "The invoice ID (e.g., 'ABC-1023').",
                }
            },
            "required": ["invoice_id"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        invoice_id = kwargs.get("invoice_id", "")
        if not invoice_id:
            return ToolResult(success=False, error="invoice_id is required.")

        details = self._portal.get_details(invoice_id)

        if not details:
            return ToolResult(
                success=False,
                error=f"Invoice '{invoice_id}' not found.",
            )

        return ToolResult(
            success=True,
            data={"invoice": details},
            message=f"Retrieved details for invoice {invoice_id}.",
        )
