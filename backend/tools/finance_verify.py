"""Tool: Verify invoice submission against stored records in the finance system."""

from mock_env.finance_system import FinanceSystem
from tools.base import BaseTool, ToolResult


class VerifySubmissionTool(BaseTool):

    def __init__(self, finance: FinanceSystem):
        self._finance = finance

    @property
    def name(self) -> str:
        return "verify_submission"

    @property
    def description(self) -> str:
        return (
            "Verify that an invoice has been successfully recorded in the finance system. "
            "Re-reads the recorded entry and checks that invoice number, vendor, amount, "
            "and due date match expected values. Always call this as the final step."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "invoice_no": {
                    "type": "string",
                    "description": "Invoice number to verify (e.g., 'ABC-1023').",
                },
                "expected_vendor": {
                    "type": "string",
                    "description": "Expected vendor name.",
                },
                "expected_amount": {
                    "type": "number",
                    "description": "Expected invoice amount.",
                },
                "expected_due_date": {
                    "type": "string",
                    "description": "Expected due date in YYYY-MM-DD format.",
                },
            },
            "required": ["invoice_no", "expected_vendor", "expected_amount", "expected_due_date"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        invoice_no = kwargs.get("invoice_no", "")
        expected_vendor = kwargs.get("expected_vendor", "")
        expected_amount = kwargs.get("expected_amount", 0)
        expected_due_date = kwargs.get("expected_due_date", "")

        verification_response = self._finance.verify(invoice_no)
        if not verification_response["success"]:
            return ToolResult(
                success=False,
                error=verification_response["error"],
                message=f"Verification failed: {verification_response['error']}",
            )

        record = verification_response["record"]
        checks = {
            "invoice_no_match": record.get("invoice_no") == invoice_no,
            "vendor_match": expected_vendor.lower() in record.get("vendor", "").lower() or record.get("vendor", "").lower() in expected_vendor.lower(),
            "amount_match": float(record.get("amount", 0)) == float(expected_amount),
            "due_date_match": record.get("due_date") == expected_due_date,
        }

        all_passed = all(checks.values())

        if all_passed:
            return ToolResult(
                success=True,
                data={
                    "verified": True,
                    "checks": checks,
                    "record": record,
                },
                message=f"Independent verification PASSED for {invoice_no}. All fields match recorded system state.",
            )
        else:
            return ToolResult(
                success=False,
                data={
                    "verified": False,
                    "checks": checks,
                    "record": record,
                },
                error=f"Verification failed checks: {[k for k, v in checks.items() if not v]}",
                message="Discrepancy detected between expected values and finance record.",
            )
