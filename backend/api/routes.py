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
from tools.invoice_read import ReadInvoiceTool
from tools.invoice_search import SearchInvoicesTool
from tools.registry import ToolRegistry

router = APIRouter()

# ── Shared In-Memory State ──────────────────────────────────────────
# For a production deployment, replace tasks dict with a database.
tasks_db: Dict[str, TaskState] = {}
controllers_db: Dict[str, AgentController] = {}

# Mock environments (singletons for demonstration)
invoice_portal = InvoicePortal()
finance_system = FinanceSystem()


def create_tool_registry() -> ToolRegistry:
    """Instantiate and register all tools wired to the mock systems."""
    registry = ToolRegistry()
    registry.register(SearchInvoicesTool(invoice_portal))
    registry.register(ReadInvoiceTool(invoice_portal))
    registry.register(OpenFinanceSystemTool(finance_system))
    registry.register(FillInvoiceFormTool(finance_system))
    registry.register(SubmitInvoiceTool(finance_system))
    registry.register(VerifySubmissionTool(finance_system))
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


@router.post("/reset")
async def reset_environments():
    """Reset the mock systems for a clean demo run."""
    finance_system.reset()
    return {"status": "environments reset successfully"}


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
