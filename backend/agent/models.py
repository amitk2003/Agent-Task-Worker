"""
Data models for the Autonomous AI Task Worker.

Every data contract (request, response, state, event) lives here.
This is the single source of truth for the shape of data flowing
through the system. When you add a feature, define its data here first.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────


class TaskStatus(str, Enum):
    """Lifecycle states of a task."""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Outcome of a single execution step."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RECOVERED = "recovered"


class EventType(str, Enum):
    """
    Types of events emitted during execution.

    The frontend maps these to different UI treatments
    (icons, colors, animations). Add new types here when
    you add new observable behaviors to the agent.
    """
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    STEP_FAILED = "step_failed"
    RECOVERY_ATTEMPT = "recovery_attempt"
    APPROVAL_NEEDED = "approval_needed"
    VERIFICATION_START = "verification_start"
    VERIFICATION_RESULT = "verification_result"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    THINKING = "thinking"


# ── Step & Verification Records ──────────────────────────────────────


class StepRecord(BaseModel):
    """Record of a single action taken by the agent."""
    step_number: int
    action: str
    tool_name: str
    tool_args: dict[str, Any] = {}
    result: dict[str, Any] = {}
    status: StepStatus
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VerificationResult(BaseModel):
    """Result of verifying the task outcome."""
    verified: bool
    checks: dict[str, bool] = {}
    evidence: dict[str, Any] = {}
    message: str = ""


# ── Events ───────────────────────────────────────────────────────────


class AgentEvent(BaseModel):
    """
    Event emitted by the agent during execution.

    These flow over WebSocket to the React dashboard for
    real-time display. Each event has a type, human-readable
    message, and optional structured data.
    """
    event_type: EventType
    message: str
    data: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Task State ───────────────────────────────────────────────────────


class TaskState(BaseModel):
    """
    Complete state of a task execution.

    This is the "execution memory" described in the project doc.
    It tracks the goal, current progress, discovered data,
    step history, and verification result.
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    current_step: int = 0
    memory: dict[str, Any] = {}
    history: list[StepRecord] = []
    verification: Optional[VerificationResult] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


# ── API Contracts ────────────────────────────────────────────────────


class TaskRequest(BaseModel):
    """API request to create a new task."""
    goal: str


class ApprovalResponse(BaseModel):
    """User's approval/rejection for a pending action."""
    approved: bool
    message: str = ""
