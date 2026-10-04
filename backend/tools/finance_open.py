"""Tool: Open / authenticate with the internal finance system."""

from mock_env.finance_system import FinanceSystem
from tools.base import BaseTool, ToolResult


class OpenFinanceSystemTool(BaseTool):

    def __init__(self, finance: FinanceSystem):
        self._finance = finance

    @property
    def name(self) -> str:
        return "open_finance_system"

    @property
    def description(self) -> str:
        return (
            "Open and authenticate with the internal finance system. "
            "Must be called before filling forms or submitting invoices. "
            "Also use this to re-authenticate if a session expires."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> ToolResult:
        result = self._finance.open_session()
        return ToolResult(
            success=result["authenticated"],
            data=result,
            message=result["message"],
        )
