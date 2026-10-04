"""
Mock Email System — simulates enterprise email inbox and outbox.

Enables the AI Worker to:
1. Search and read incoming emails (e.g. vendor invoice notifications).
2. Send outgoing notification emails (e.g. alerting managers upon successful task completion).
3. Provide an inspectable outbox for verification and evaluation.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional


INITIAL_INBOX = [
    {
        "id": "email-001",
        "sender": "billing@abcltd.com",
        "to": "finance-ops@company.com",
        "subject": "Invoice ABC-1023 for Q4 Cloud Services",
        "body": "Hi Finance Team,\n\nPlease find attached the latest invoice ABC-1023 for ABC Ltd.\nAmount: INR 45,000\nDue Date: 2026-10-15\n\nPlease process into your internal finance system.\n\nBest,\nAccounts Dept, ABC Ltd",
        "date": "2026-10-02T09:30:00Z",
        "has_attachment": True,
        "attachment_name": "ABC-1023_Invoice.pdf",
    },
    {
        "id": "email-002",
        "sender": "invoicing@xyzcorp.com",
        "to": "finance-ops@company.com",
        "subject": "New Invoice XYZ-0547 - Software Licenses",
        "body": "Hello,\n\nWe have issued invoice XYZ-0547 for XYZ Corp.\nTotal Amount: INR 128,000\nPayment Due: 2026-10-30\n\nKindly acknowledge and process.\n\nXYZ Billing",
        "date": "2026-10-01T14:15:00Z",
        "has_attachment": True,
        "attachment_name": "XYZ-0547.pdf",
    },
    {
        "id": "email-003",
        "sender": "orders@acmeindustries.com",
        "to": "procurement@company.com",
        "subject": "Monthly Statement & Invoice ACM-2201",
        "body": "Dear Partner,\n\nYour invoice ACM-2201 for raw materials batch #44 is ready.\nAmount: INR 95,500\nDue Date: 2026-11-01\n\nThanks,\nAcme Industries",
        "date": "2026-10-03T11:00:00Z",
        "has_attachment": True,
        "attachment_name": "ACM-2201_Invoice.pdf",
    },
]


class EmailSystem:
    """
    Simulated email client providing inbox searching, reading,
    and outbox delivery tracking.
    """

    def __init__(self):
        self._inbox: List[Dict] = [e.copy() for e in INITIAL_INBOX]
        self._outbox: List[Dict] = []

    def search_emails(self, query: str = "", sender: str = "") -> List[Dict]:
        """
        Search inbox by subject/body keywords or sender address.
        Case-insensitive search.
        """
        results = []
        q_lower = query.lower() if query else ""
        s_lower = sender.lower() if sender else ""

        for mail in self._inbox:
            matches_q = not query or (q_lower in mail["subject"].lower() or q_lower in mail["body"].lower())
            matches_s = not sender or (s_lower in mail["sender"].lower())
            if matches_q and matches_s:
                results.append({
                    "id": mail["id"],
                    "sender": mail["sender"],
                    "subject": mail["subject"],
                    "date": mail["date"],
                    "has_attachment": mail["has_attachment"],
                    "attachment_name": mail.get("attachment_name"),
                })
        return results

    def read_email(self, email_id: str) -> Optional[Dict]:
        """Read full details and content of a specific email by ID."""
        for mail in self._inbox:
            if mail["id"] == email_id:
                return mail.copy()
        return None

    def send_email(self, to: str, subject: str, body: str) -> Dict:
        """
        Send an email and record it in the outbox.
        Returns the sent email confirmation record.
        """
        mail_record = {
            "id": f"sent-{str(uuid.uuid4())[:8]}",
            "from": "ai-taskworker@company.com",
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "delivered",
        }
        self._outbox.append(mail_record)
        return mail_record

    def get_inbox(self) -> List[Dict]:
        """Return all inbox emails."""
        return self._inbox

    def get_outbox(self) -> List[Dict]:
        """Return all sent emails in outbox."""
        return self._outbox

    def reset(self):
        """Reset outbox to initial clean state."""
        self._outbox.clear()
