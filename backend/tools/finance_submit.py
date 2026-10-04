"""Tool: Submit the filled invoice form in the finance system."""

from mock_env.finance_system import FinanceSystem
from tools.base import BaseTool, ToolResult


class SubmitInvoiceTool(BaseTool):

    def __init__(self, finance: FinanceSystem):
        self._finance = finance

    @property
    def name(self) -> str:
        return "submit_invoice"

    @property
    def description(self) -> str:
        return (
            "Submit the filled invoice form in the finance system. "
            "The form must be filled before calling this. "
            "If submission fails due to session expiry, re-authenticate "
            "using open_finance_system, re-fill the form, and try again."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> ToolResult:
        result = self._finance.submit()

        if not result["success"]:
            return ToolResult(
                success=False,
                error=result["error"],
                data=result,
            )

        return ToolResult(
            success=True,
            data=result,
            message=result["message"],
        )
