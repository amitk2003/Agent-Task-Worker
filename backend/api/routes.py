"""
API Routes — REST and WebSocket endpoints for the AI Task Worker.

Provides:
- Task initiation and inspection endpoints
- Real-time WebSocket streaming for the execution trace
- Interactive human-in-the-loop approval endpoints
- Inspection endpoints for the mock environments (Invoice Portal & Finance System)
  so evaluators can see the before/after state with their own eyes.
"""

import json
from typing import Dict
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agent.audit_store import get_audit_store
from agent.controller import AgentController
from agent.models import (
    ApprovalResponse,
    TaskRequest,
    TaskState,
    TaskStatus,
)
from mock_env.finance_system import FinanceSystem
from mock_env.invoice_portal import InvoicePortal
from tools.finance_fill import FillInvoiceFormTool
from tools.finance_open import OpenFinanceSystemTool
from tools.finance_submit import SubmitInvoiceTool
from tools.finance_verify import VerifySubmissionTool
from mock_env.email_system import EmailSystem
from mock_env.file_manager import FileManager
from mock_env.browser_engine import BrowserEngine
from tools.invoice_read import ReadInvoiceTool
from tools.invoice_search import SearchInvoicesTool
from tools.email_tools import SearchEmailsTool, ReadEmailTool, SendEmailTool
from tools.file_tools import ListFilesTool, ReadFileTool, SaveFileTool
from tools.browser_tools import BrowserNavigateTool, BrowserScreenshotTool
from tools.registry import ToolRegistry

router = APIRouter()

# ── Shared In-Memory State ──────────────────────────────────────────
tasks_db: Dict[str, TaskState] = {}
controllers_db: Dict[str, AgentController] = {}

# Shared singleton environments for INSPECTION endpoints only.
# Each task gets its OWN isolated copies inside create_tool_registry().
invoice_portal = InvoicePortal()
finance_system = FinanceSystem()
email_system = EmailSystem()
file_manager = FileManager()
browser_engine = BrowserEngine()


def create_tool_registry() -> ToolRegistry:
    """
    Build a fresh ToolRegistry with isolated environment instances.

    IMPORTANT: Each task call creates its OWN registry with its OWN
    mock-env objects. This prevents concurrent tasks from corrupting
    each other's state (task isolation).

    The shared singletons above are only used by inspection endpoints.
    """
    # Per-task isolated environments
    task_invoice_portal = InvoicePortal()
    task_finance_system = FinanceSystem()
    task_email_system = EmailSystem()
    task_file_manager = FileManager()
    task_browser_engine = BrowserEngine()

    registry = ToolRegistry()
    # Invoices & Finance
    registry.register(SearchInvoicesTool(task_invoice_portal))
    registry.register(ReadInvoiceTool(task_invoice_portal))
    registry.register(OpenFinanceSystemTool(task_finance_system))
    registry.register(FillInvoiceFormTool(task_finance_system))
    registry.register(SubmitInvoiceTool(task_finance_system))
    registry.register(VerifySubmissionTool(task_finance_system))
    # Email operations
    registry.register(SearchEmailsTool(task_email_system))
    registry.register(ReadEmailTool(task_email_system))
    registry.register(SendEmailTool(task_email_system))
    # File operations
    registry.register(ListFilesTool(task_file_manager))
    registry.register(ReadFileTool(task_file_manager))
    registry.register(SaveFileTool(task_file_manager))
    # Browser operations
    registry.register(BrowserNavigateTool(task_browser_engine))
    registry.register(BrowserScreenshotTool(task_browser_engine))
    return registry


# ── REST Endpoints ───────────────────────────────────────────────────


@router.post("/tasks", response_model=TaskState)
async def create_task(req: TaskRequest):
    """Create a new task record with the natural language goal."""
    task = TaskState(goal=req.goal)
    tasks_db[task.task_id] = task

    registry = create_tool_registry()
    controller = AgentController(registry)
    controllers_db[task.task_id] = controller

    return task


@router.get("/tasks/{task_id}", response_model=TaskState)
async def get_task(task_id: str):
    """Retrieve full task state, step history, and verification results."""
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/approval")
async def post_approval(task_id: str, approval: ApprovalResponse):
    """Provide approval or rejection for a task awaiting human review."""
    controller = controllers_db.get(task_id)
    task = tasks_db.get(task_id)
    if not controller or not task:
        raise HTTPException(status_code=404, detail="Task not found")

    controller.provide_approval(approval.approved)
    return {"status": "ok", "approved": approval.approved}


# ── Inspection Endpoints for Evaluators ─────────────────────────────


@router.get("/portal/invoices")
async def get_portal_invoices():
    """Inspect all invoices currently residing in the mock invoice portal."""
    return invoice_portal._invoices


@router.get("/finance/records")
async def get_finance_records():
    """Inspect all recorded invoices currently stored in the mock finance system."""
    return {
        "records": list(finance_system._submitted_records.values()),
        "session_active": finance_system._session_active,
        "submit_attempts": finance_system._submit_attempts,
    }


@router.get("/email/inbox")
async def get_email_inbox():
    """Inspect incoming emails in inbox."""
    return email_system.get_inbox()


@router.get("/email/outbox")
async def get_email_outbox():
    """Inspect outgoing sent emails in outbox."""
    return email_system.get_outbox()


@router.get("/files/list")
async def get_files_list(sub_dir: str = ""):
    """Inspect files in workspace storage."""
    return file_manager.list_files(sub_dir)


@router.get("/browser/status")
async def get_browser_status():
    """Inspect last browser state and screenshot."""
    return browser_engine.get_last_state()


@router.post("/reset")
async def reset_environments():
    """Reset the mock systems for a clean demo run."""
    finance_system.reset()
    email_system.reset()
    return {"status": "all environments reset successfully"}


# ── Audit History Endpoints ────────────────────────────────


@router.get("/audit/history")
async def get_audit_history(limit: int = 50):
    """Return the most recent completed/failed tasks from persistent storage."""
    store = await get_audit_store()
    return await store.get_task_history(limit=limit)


@router.get("/audit/tasks/{task_id}/steps")
async def get_audit_steps(task_id: str):
    """Return all persisted steps for a specific task (audit trail)."""
    store = await get_audit_store()
    steps = await store.get_task_steps(task_id)
    if not steps:
        raise HTTPException(status_code=404, detail="No steps found for this task")
    return steps


# ── WebSocket Execution Stream ──────────────────────────────────────


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_stream(websocket: WebSocket, task_id: str):
    """
    Execute task and stream live agent events to client over WebSocket.
    Also accepts inbound client messages for approval decisions.
    """
    await websocket.accept()

    task = tasks_db.get(task_id)
    controller = controllers_db.get(task_id)

    if not task or not controller:
        await websocket.send_json({
            "event_type": "error",
            "message": "Task not found",
            "data": {},
            "timestamp": "",
        })
        await websocket.close()
        return

    # Background receiver task for interactive messages (like approval)
    async def listen_inbound():
        try:
            while True:
                data_text = await websocket.receive_text()
                data = json.loads(data_text)
                if data.get("action") == "approval":
                    approved = bool(data.get("approved", True))
                    controller.provide_approval(approved)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    import asyncio
    listener = asyncio.create_task(listen_inbound())

    try:
        async for event in controller.execute_task(task):
            event_payload = {
                "event_type": event.event_type.value,
                "message": event.message,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
            }
            await websocket.send_text(json.dumps(event_payload))
            # Yield control slightly for smooth websocket frame transmission
            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "event_type": "task_failed",
            "message": f"Execution exception: {str(e)}",
            "data": {"error": str(e)},
            "timestamp": "",
        }))
    finally:
        listener.cancel()
