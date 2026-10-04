"""File tools for reading, saving, and listing files in workspace storage."""

from mock_env.file_manager import FileManager
from tools.base import BaseTool, ToolResult


class ListFilesTool(BaseTool):

    def __init__(self, file_manager: FileManager):
        self._manager = file_manager

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return (
            "List all available files in the storage workspace or subfolder. "
            "Returns file paths, sizes, and last modified dates."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "sub_dir": {
                    "type": "string",
                    "description": "Optional subfolder path (e.g. 'invoices'). Defaults to root.",
                }
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> ToolResult:
        sub_dir = kwargs.get("sub_dir", "")
        files = self._manager.list_files(sub_dir)
        return ToolResult(
            success=True,
            data={"files": files, "count": len(files)},
            message=f"Found {len(files)} file(s) in '{sub_dir or 'root'}'.",
        )


class ReadFileTool(BaseTool):

    def __init__(self, file_manager: FileManager):
        self._manager = file_manager

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read the textual content of a file from storage. "
            "Supports reading CSVs, txt, JSON, or offline invoice documents."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to file (e.g. 'invoices/vendor_payment_terms.csv').",
                }
            },
            "required": ["file_path"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path", "")
        if not file_path:
            return ToolResult(success=False, error="file_path is required.")

        res = self._manager.read_file(file_path)
        if not res["success"]:
            return ToolResult(success=False, error=res["error"])

        return ToolResult(
            success=True,
            data=res,
            message=f"Successfully read {res['size_bytes']} bytes from '{file_path}'.",
        )


class SaveFileTool(BaseTool):

    def __init__(self, file_manager: FileManager):
        self._manager = file_manager

    @property
    def name(self) -> str:
        return "save_file"

    @property
    def description(self) -> str:
        return (
            "Save content to a file in workspace storage. "
            "Use this to write execution audit receipts, export summary CSVs, or save notes."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Target relative file path (e.g. 'reports/audit_receipt.txt').",
                },
                "content": {
                    "type": "string",
                    "description": "The text or JSON string content to save.",
                },
            },
            "required": ["file_path", "content"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path", "")
        content = kwargs.get("content", "")

        if not file_path or not content:
            return ToolResult(success=False, error="Both file_path and content are required.")

        res = self._manager.write_file(file_path, content)
        if not res["success"]:
            return ToolResult(success=False, error=res["error"])

        return ToolResult(
            success=True,
            data=res,
            message=res["message"],
        )
