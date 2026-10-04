"""Browser automation tools for navigation, page inspection, and visual screenshot capture."""

from mock_env.browser_engine import BrowserEngine
from tools.base import BaseTool, ToolResult


class BrowserNavigateTool(BaseTool):

    def __init__(self, browser_engine: BrowserEngine):
        self._engine = browser_engine

    @property
    def name(self) -> str:
        return "browser_navigate"

    @property
    def description(self) -> str:
        return (
            "Navigate to a web page or web portal URL. Extracts readable text content "
            "and automatically captures a visual screenshot for verification."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to open (e.g. 'http://localhost:8000/api/portal/invoices').",
                }
            },
            "required": ["url"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        if not url:
            return ToolResult(success=False, error="URL is required.")

        res = await self._engine.navigate(url)
        if not res["success"]:
            return ToolResult(success=False, error=res.get("error", "Navigation failed"))

        return ToolResult(
            success=True,
            data=res,
            message=f"Loaded '{res.get('title', url)}' ({res.get('engine', 'browser')}). Captured visual screenshot.",
        )


class BrowserScreenshotTool(BaseTool):

    def __init__(self, browser_engine: BrowserEngine):
        self._engine = browser_engine

    @property
    def name(self) -> str:
        return "browser_screenshot"

    @property
    def description(self) -> str:
        return (
            "Capture a visual screenshot of the current page as visual proof/evidence of completion."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Label for the screenshot (e.g. 'invoice_submitted_proof').",
                }
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> ToolResult:
        label = kwargs.get("label", "evidence")
        res = await self._engine.capture_screenshot(label=label)
        if not res["success"]:
            return ToolResult(success=False, error=res.get("error", "Screenshot capture failed"))

        return ToolResult(
            success=True,
            data=res,
            message=f"Captured screenshot evidence: {res['screenshot_path']}",
        )
