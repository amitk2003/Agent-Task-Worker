"""
Local File Manager — sandboxed file operations for the AI Task Worker.

Allows the agent to:
1. List available files in workspace/storage.
2. Read text, JSON, and CSV documents (e.g. offline invoices or vendor lists).
3. Save structured audit logs, receipts, or exported summaries to disk.
All operations are sandboxed within backend/storage to ensure security.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class FileManager:
    """
    Sandboxed file manager handling safe read, write, and directory listing.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_path = Path(base_dir).resolve()
        else:
            self.base_path = Path(__file__).parent.parent / "storage"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._seed_default_files()

    def _seed_default_files(self):
        """Seed default enterprise files for demonstration."""
        invoices_dir = self.base_path / "invoices"
        invoices_dir.mkdir(exist_ok=True)

        vendor_terms = invoices_dir / "vendor_payment_terms.csv"
        if not vendor_terms.exists():
            vendor_terms.write_text(
                "vendor_name,terms,preferred_payment,contact\n"
                "ABC Ltd,Net 15,Direct Deposit,billing@abcltd.com\n"
                "XYZ Corp,Net 30,Wire Transfer,invoicing@xyzcorp.com\n"
                "Acme Industries,Net 45,Cheque,orders@acmeindustries.com\n",
                encoding="utf-8",
            )

        offline_doc = invoices_dir / "ABC-1023_offline_backup.txt"
        if not offline_doc.exists():
            offline_doc.write_text(
                "INVOICE BACKUP COPY\n"
                "Invoice ID: ABC-1023\n"
                "Vendor: ABC Ltd\n"
                "Amount: INR 45000\n"
                "Due Date: 2026-10-15\n"
                "Description: Cloud Hosting Q4 & Support Package\n",
                encoding="utf-8",
            )

    def _safe_resolve(self, relative_path: str) -> Path:
        """Resolve a path safely within the sandbox."""
        resolved = (self.base_path / relative_path).resolve()
        if not str(resolved).startswith(str(self.base_path)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return resolved

    def list_files(self, sub_dir: str = "") -> List[Dict]:
        """List files in the sandboxed storage directory."""
        target_dir = self._safe_resolve(sub_dir)
        if not target_dir.exists():
            return []

        results = []
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.base_path)
                stat = full_path.stat()
                results.append({
                    "path": str(rel_path).replace("\\", "/"),
                    "name": file,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        return results

    def read_file(self, file_path: str) -> Dict:
        """Read content of a file within sandbox."""
        target_path = self._safe_resolve(file_path)
        if not target_path.exists() or not target_path.is_file():
            return {"success": False, "error": f"File '{file_path}' not found."}

        try:
            content = target_path.read_text(encoding="utf-8")
            return {
                "success": True,
                "path": file_path,
                "content": content,
                "size_bytes": len(content),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, file_path: str, content: str) -> Dict:
        """Write content to a file within sandbox."""
        target_path = self._safe_resolve(file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            target_path.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "path": file_path,
                "size_bytes": len(content),
                "created_at": datetime.utcnow().isoformat(),
                "message": f"Successfully saved file to {file_path}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
