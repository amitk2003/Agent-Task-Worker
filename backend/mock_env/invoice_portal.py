"""
Mock Invoice Portal — simulates a company invoice management system.

In production, this would be replaced by Playwright browser automation
or API calls to a real invoice system. The tool layer doesn't change —
only the data source behind it.

Data includes invoices from multiple companies to demonstrate
that the same agent handles different company names without
code changes (generalization).
"""

INVOICES = [
    {
        "invoice_id": "ABC-1023",
        "company": "ABC Ltd",
        "amount": 45000,
        "currency": "INR",
        "due_date": "2026-10-15",
        "issue_date": "2026-10-02",
        "status": "pending",
        "items": [
            {"description": "Cloud hosting Q4", "amount": 30000},
            {"description": "Support package", "amount": 15000},
        ],
    },
    {
        "invoice_id": "ABC-1019",
        "company": "ABC Ltd",
        "amount": 32000,
        "currency": "INR",
        "due_date": "2026-09-20",
        "issue_date": "2026-09-05",
        "status": "paid",
        "items": [
            {"description": "Cloud hosting Q3", "amount": 32000},
        ],
    },
    {
        "invoice_id": "XYZ-0547",
        "company": "XYZ Corp",
        "amount": 128000,
        "currency": "INR",
        "due_date": "2026-10-30",
        "issue_date": "2026-10-01",
        "status": "pending",
        "items": [
            {"description": "Software license annual", "amount": 100000},
            {"description": "Implementation fee", "amount": 28000},
        ],
    },
    {
        "invoice_id": "XYZ-0540",
        "company": "XYZ Corp",
        "amount": 75000,
        "currency": "INR",
        "due_date": "2026-09-15",
        "issue_date": "2026-08-25",
        "status": "paid",
        "items": [
            {"description": "Consulting services", "amount": 75000},
        ],
    },
    {
        "invoice_id": "ACM-2201",
        "company": "Acme Industries",
        "amount": 95500,
        "currency": "INR",
        "due_date": "2026-11-01",
        "issue_date": "2026-10-03",
        "status": "pending",
        "items": [
            {"description": "Raw materials batch #44", "amount": 65500},
            {"description": "Shipping & handling", "amount": 30000},
        ],
    },
]


class InvoicePortal:
    """
    Simulated invoice portal with search and retrieval.

    Methods mirror what a real portal API or Playwright
    automation would provide.
    """

    def __init__(self):
        self._invoices = [inv.copy() for inv in INVOICES]

    def search(self, query: str) -> list[dict]:
        """
        Search invoices by company name.
        Case-insensitive partial match — just like a real search box.
        """
        query_lower = query.lower()
        results = []
        for inv in self._invoices:
            if query_lower in inv["company"].lower():
                results.append({
                    "invoice_id": inv["invoice_id"],
                    "company": inv["company"],
                    "amount": inv["amount"],
                    "currency": inv["currency"],
                    "due_date": inv["due_date"],
                    "status": inv["status"],
                })
        return results

    def get_details(self, invoice_id: str) -> dict | None:
        """Get full details of a specific invoice by ID."""
        for inv in self._invoices:
            if inv["invoice_id"] == invoice_id:
                return inv.copy()
        return None

    def get_latest(self, company: str) -> dict | None:
        """Get the most recent invoice for a company (by due date)."""
        matches = self.search(company)
        if not matches:
            return None
        matches.sort(key=lambda x: x["due_date"], reverse=True)
        return matches[0]
