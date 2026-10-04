"""
Tool Registry — central catalog of all available tools.

The controller uses this to look up tools by name.
The planner uses get_schemas() to tell the LLM what tools exist.

Design note: Registration is explicit (not auto-discovered) so
you always know exactly which tools are active by reading the
_create_registry() function in api/routes.py.
"""

from tools.base import BaseTool


class ToolRegistry:
    """
    Registry of available tools.

    Usage:
        registry = ToolRegistry()
        registry.register(SearchInvoicesTool(portal))
        tool = registry.get("search_invoices")
        schemas = registry.get_schemas()  # → list of OpenAI tool schemas
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool. Overwrites if name already exists."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Look up a tool by name. Returns None if not found."""
        return self._tools.get(name)

    def get_all(self) -> list[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict]:
        """Get OpenAI-compatible schemas for all tools (sent to LLM)."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def list_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
