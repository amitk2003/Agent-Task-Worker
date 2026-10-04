"""Tool: Search the invoice portal for invoices by company name."""

from mock_env.invoice_portal import InvoicePortal
from tools.base import BaseTool, ToolResult


class SearchInvoicesTool(BaseTool):

    def __init__(self, portal: InvoicePortal):
        self._portal = portal

    @property
    def name(self) -> str:
        return "search_invoices"

    @property
    def description(self) -> str:
        return (
            "Search the invoice portal for invoices from a specific company. "
            "Returns a list of matching invoices with ID, amount, due date, and status. "
            "Supports partial company name matching."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Company name to search for (supports partial match).",
                }
            },
            "required": ["company_name"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        company_name = kwargs.get("company_name", "")
        if not company_name:
            return ToolResult(success=False, error="company_name is required.")

        results = self._portal.search(company_name)

        if not results:
            return ToolResult(
                success=True,
                data={"invoices": [], "count": 0},
                message=f"No invoices found for '{company_name}'.",
            )

        return ToolResult(
            success=True,
            data={"invoices": results, "count": len(results)},
            message=f"Found {len(results)} invoice(s) for '{company_name}'.",
        )
