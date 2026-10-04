"""
Mock Internal Finance System — simulates the company's billing app.

INTENTIONAL FAILURE BEHAVIOUR:
  The first call to submit() triggers a "Session expired" error.
  This forces the agent to demonstrate error recovery:
    1. Detect the failure
    2. Re-authenticate (open_session)
    3. Re-fill the form
    4. Submit again (succeeds)

This is the single most important demo feature — it proves
the agent handles unexpected states autonomously.

To disable the intentional failure (e.g., for testing),
call reset() and set self._session_expired_triggered = True.
"""

import uuid
from datetime import datetime


class FinanceSystem:
    """
    Simulated internal finance system with form fill, submit, and verify.
    """

    def __init__(self):
        self._session_active: bool = False
        self._submitted_records: dict[str, dict] = {}
        self._form_data: dict = {}
        self._submit_attempts: int = 0
        self._session_expired_triggered: bool = False

    def open_session(self) -> dict:
        """Open / re-authenticate with the finance system."""
        self._session_active = True
        return {
            "authenticated": True,
            "message": "Successfully authenticated with Finance System.",
            "user": "ai-worker@company.com",
        }

    def fill_form(
        self,
        invoice_no: str,
        vendor: str,
        amount: float,
        due_date: str,
    ) -> dict:
        """Fill the invoice entry form with the provided data."""
        if not self._session_active:
            return {
                "success": False,
                "error": "Session not active. Please authenticate first.",
            }

        self._form_data = {
            "invoice_no": invoice_no,
            "vendor": vendor,
            "amount": amount,
            "due_date": due_date,
        }

        return {
            "success": True,
            "message": "Form filled successfully.",
            "form_data": self._form_data.copy(),
        }

    def submit(self) -> dict:
        """
        Submit the filled form.

        INTENTIONAL: First submission triggers session expiry
        to demonstrate the agent's error recovery.
        """
        if not self._session_active:
            return {
                "success": False,
                "error": "Session not active. Please authenticate first.",
            }

        if not self._form_data:
            return {
                "success": False,
                "error": "No form data. Please fill the form first.",
            }

        self._submit_attempts += 1

        # ── Intentional failure on first submit ──────────────
        if not self._session_expired_triggered:
            self._session_expired_triggered = True
            self._session_active = False
            return {
                "success": False,
                "error": "Session expired. Please re-authenticate and try again.",
            }

        # ── Second attempt succeeds ──────────────────────────
        record_id = str(uuid.uuid4())[:8]
        record = {
            "record_id": record_id,
            **self._form_data,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "recorded",
        }
        self._submitted_records[self._form_data["invoice_no"]] = record
        self._form_data = {}

        return {
            "success": True,
            "message": f"Invoice submitted successfully. Record ID: {record_id}",
            "record": record,
        }

    def verify(self, invoice_no: str) -> dict:
        """Verify a submitted record by re-reading it from the system."""
        if not self._session_active:
            return {
                "success": False,
                "error": "Session not active. Please authenticate first.",
            }

        record = self._submitted_records.get(invoice_no)
        if not record:
            return {
                "success": False,
                "error": f"No record found for invoice {invoice_no}.",
            }

        return {
            "success": True,
            "message": "Record found.",
            "record": record,
        }

    def reset(self) -> None:
        """Reset all state (for running a fresh task)."""
        self._session_active = False
        self._submitted_records.clear()
        self._form_data.clear()
        self._submit_attempts = 0
        self._session_expired_triggered = False
