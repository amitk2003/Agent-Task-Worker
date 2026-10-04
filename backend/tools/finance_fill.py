"""Tool: Fill the invoice entry form in the finance system."""

from mock_env.finance_system import FinanceSystem
from tools.base import BaseTool, ToolResult


class FillInvoiceFormTool(BaseTool):

    def __init__(self, finance: FinanceSystem):
        self._finance = finance

    @property
    def name(self) -> str:
        return "fill_invoice_form"

    @property
    def description(self) -> str:
        return (
            "Fill the invoice entry form in the finance system with the given data. "
            "The finance system must be authenticated before calling this. "
            "After filling, the form is ready for submission."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "invoice_no": {
                    "type": "string",
                    "description": "The invoice number (e.g., 'ABC-1023').",
                },
                "vendor": {
                    "type": "string",
                    "description": "The vendor/company name.",
                },
                "amount": {
                    "type": "number",
                    "description": "The invoice amount.",
                },
                "due_date": {
                    "type": "string",
                    "description": "The due date in YYYY-MM-DD format.",
                },
            },
            "required": ["invoice_no", "vendor", "amount", "due_date"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        invoice_no = kwargs.get("invoice_no", "")
        vendor = kwargs.get("vendor", "")
        amount = kwargs.get("amount", 0)
        due_date = kwargs.get("due_date", "")

        if not all([invoice_no, vendor, amount, due_date]):
            return ToolResult(
                success=False,
                error="All fields required: invoice_no, vendor, amount, due_date.",
            )

        result = self._finance.fill_form(invoice_no, vendor, amount, due_date)

        if not result["success"]:
            return ToolResult(success=False, error=result["error"])

        return ToolResult(
            success=True,
            data=result,
            message=result["message"],
            # High-stakes action → request user approval before submit
            requires_approval=True,
            approval_message=(
                f"About to submit invoice {invoice_no} for {vendor}, "
                f"amount: INR {amount:,.0f}, due: {due_date}.\n"
                f"Do you want to proceed?"
            ),
        )
