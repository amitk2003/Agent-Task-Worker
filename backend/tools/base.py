"""
Base tool interface.

Every tool in the system must subclass BaseTool.
This enforces a consistent interface that the controller
and LLM both understand.

To add a new tool:
  1. Create a new file in tools/
  2. Subclass BaseTool
  3. Define name, description, parameters (JSON Schema)
  4. Implement execute(**kwargs) → ToolResult
  5. Register it in api/routes.py → _create_registry()
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class ToolResult(BaseModel):
    """
    Standardized result returned by every tool.

    Fields:
        success:          Did the tool action succeed?
        data:             Structured output data.
        message:          Human-readable summary of what happened.
        error:            Error description (only if success=False).
        requires_approval:  If True, agent pauses for user confirmation.
        approval_message: Message shown to user when approval is needed.
    """
    success: bool
    data: dict[str, Any] = {}
    message: str = ""
    error: Optional[str] = None
    requires_approval: bool = False
    approval_message: str = ""


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    The LLM sees name + description + parameters to decide
    which tool to call. The controller calls execute() with
    the LLM-provided arguments.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier (used in LLM function calls)."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this tool does (included in LLM prompt)."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema for the tool's parameters."""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Run the tool with the given arguments."""
        ...

    def to_openai_schema(self) -> dict:
        """
        Convert to OpenAI-compatible function schema.
        Groq uses this same format for tool/function calling.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
