"""
Agent Controller — the heart of the autonomous AI worker.

Implements the core observe → decide → act loop described in
the project document. This is the single most important file
in the entire codebase.

Responsibilities:
  - Orchestrate the agent loop with bounded steps
  - Delegate decisions to the LLM planner
  - Execute tools and observe results
  - Handle failures with bounded retries
  - Request user approval for high-stakes actions
  - Verify task completion
  - Emit events for real-time UI updates

Design notes:
  - The controller does NOT know which tools exist — it uses the registry.
  - The controller does NOT talk to the LLM directly — it uses the planner.
  - Events are yielded (async generator) so the caller (WebSocket route)
    can stream them to the frontend in real time.
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional

from agent.audit_store import get_audit_store
from agent.memory import ExecutionMemory
from agent.models import (
    AgentEvent,
    EventType,
    StepRecord,
    StepStatus,
    TaskState,
    TaskStatus,
    VerificationResult,
)
from agent.planner import Planner
from config import get_settings
from tools.registry import ToolRegistry


class AgentController:
    """
    Orchestrates the autonomous agent's execution loop.

    Usage:
        controller = AgentController(registry)
        async for event in controller.execute_task(task):
            send_to_frontend(event)
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry
        self._planner = Planner()
        self._settings = get_settings()
        # Approval synchronization
        self._approval_event: Optional[asyncio.Event] = None
        self._approval_result: bool = False

    # ── Main Loop ────────────────────────────────────────────────────

    async def execute_task(
        self, task: TaskState
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Run the observe-decide-act loop for a task.

        Yields AgentEvent objects as the agent progresses.
        The caller streams these to the frontend over WebSocket.
        """
        memory = ExecutionMemory()
        task.status = TaskStatus.RUNNING

        yield AgentEvent(
            event_type=EventType.THINKING,
            message=f"Understanding goal: {task.goal}",
        )

        retry_counts: dict[str, int] = {}

        while task.current_step < self._settings.max_steps:
            task.current_step += 1

            # ── DECIDE ───────────────────────────────────────────
            try:
                decision = await self._planner.decide_next_action(
                    goal=task.goal,
                    memory=memory.to_dict(),
                    history=task.history,
                    tool_schemas=self._registry.get_schemas(),
                )
            except Exception as e:
                yield AgentEvent(
                    event_type=EventType.TASK_FAILED,
                    message=f"Planner error: {str(e)}",
                )
                task.status = TaskStatus.FAILED
                task.error = str(e)
                return

            tool_name = decision.get("tool_name")
            tool_args = decision.get("tool_args", {})
            reasoning = decision.get("reasoning", "")

            # No tool selected → LLM believes we're done
            if not tool_name:
                yield AgentEvent(
                    event_type=EventType.THINKING,
                    message=reasoning or "Agent believes task is complete.",
                )
                break

            # ── ACT ──────────────────────────────────────────────
            tool = self._registry.get(tool_name)
            if not tool:
                # Record unknown tool in history so LLM can self-correct
                bad_step = StepRecord(
                    step_number=task.current_step,
                    action=tool_name,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    result={"error": f"Tool '{tool_name}' does not exist"},
                    status=StepStatus.FAILED,
                    error=f"Tool '{tool_name}' does not exist. Choose from available tools.",
                )
                task.history.append(bad_step)
                yield AgentEvent(
                    event_type=EventType.STEP_FAILED,
                    message=f"Unknown tool '{tool_name}' — asking agent to self-correct.",
                )
                continue

            yield AgentEvent(
                event_type=EventType.STEP_START,
                message=f"Executing: {tool_name}",
                data={
                    "tool": tool_name,
                    "args": tool_args,
                    "reasoning": reasoning,
                },
            )

            try:
                result = await tool.execute(**tool_args)
            except Exception as e:
                step = StepRecord(
                    step_number=task.current_step,
                    action=tool_name,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    result={"error": str(e)},
                    status=StepStatus.FAILED,
                    error=str(e),
                )
                task.history.append(step)
                yield AgentEvent(
                    event_type=EventType.STEP_FAILED,
                    message=f"Tool execution error: {str(e)}",
                    data={"error": str(e)},
                )
                continue

            # ── OBSERVE ──────────────────────────────────────────
            if result.success:
                step = StepRecord(
                    step_number=task.current_step,
                    action=tool_name,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    result=result.data,
                    status=StepStatus.SUCCESS,
                )
                task.history.append(step)

                # Persist step to audit log
                try:
                    audit = await get_audit_store()
                    await audit.save_step(
                        task_id=task.task_id,
                        step_number=step.step_number,
                        tool_name=step.tool_name,
                        tool_args=step.tool_args,
                        result=step.result,
                        status=step.status.value,
                        error=step.error,
                        timestamp=step.timestamp,
                    )
                except Exception:
                    pass  # Audit failure never blocks the agent

                # Update memory with discovered data
                if result.data:
                    self._update_memory(memory, tool_name, result.data)

                # Handle user approval if required
                if result.requires_approval:
                    task.status = TaskStatus.AWAITING_APPROVAL
                    self._approval_event = asyncio.Event()
                    yield AgentEvent(
                        event_type=EventType.APPROVAL_NEEDED,
                        message=result.approval_message,
                        data={"tool": tool_name, "args": tool_args},
                    )

                    await self._approval_event.wait()
                    task.status = TaskStatus.RUNNING

                    if not self._approval_result:
                        yield AgentEvent(
                            event_type=EventType.TASK_FAILED,
                            message="User rejected the action. Task stopped.",
                        )
                        task.status = TaskStatus.FAILED
                        task.error = "User rejected action"
                        return

                yield AgentEvent(
                    event_type=EventType.STEP_COMPLETE,
                    message=result.message,
                    data=result.data,
                )

                # Check for successful verification → task is done
                if (
                    tool_name == "verify_submission"
                    and result.data.get("verified")
                ):
                    verification = VerificationResult(
                        verified=True,
                        checks=result.data.get("checks", {}),
                        evidence=result.data.get("record", {}),
                        message="All fields verified successfully.",
                    )
                    task.verification = verification

                    yield AgentEvent(
                        event_type=EventType.VERIFICATION_RESULT,
                        message="[VERIFIED] Task verified successfully",
                        data=verification.model_dump(),
                    )
                    break

                # Reset retry count on success
                retry_counts[tool_name] = 0

            else:
                # ── FAILURE HANDLING ─────────────────────────────
                current_retries = retry_counts.get(tool_name, 0)

                step = StepRecord(
                    step_number=task.current_step,
                    action=tool_name,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    result=result.data,
                    status=StepStatus.FAILED,
                    error=result.error,
                )
                task.history.append(step)

                # Persist failed step to audit log
                try:
                    audit = await get_audit_store()
                    await audit.save_step(
                        task_id=task.task_id,
                        step_number=step.step_number,
                        tool_name=step.tool_name,
                        tool_args=step.tool_args,
                        result=step.result,
                        status=step.status.value,
                        error=step.error,
                        timestamp=step.timestamp,
                    )
                except Exception:
                    pass

                if current_retries < self._settings.max_retries_per_step:
                    retry_counts[tool_name] = current_retries + 1
                    yield AgentEvent(
                        event_type=EventType.RECOVERY_ATTEMPT,
                        message=(
                            f"Action failed: {result.error}. "
                            f"Agent deciding recovery strategy… "
                            f"(attempt {current_retries + 1}/{self._settings.max_retries_per_step})"
                        ),
                        data={
                            "error": result.error,
                            "retry": current_retries + 1,
                        },
                    )
                    # Loop continues — planner sees failure+error in history
                    # and independently decides the recovery action
                else:
                    yield AgentEvent(
                        event_type=EventType.TASK_FAILED,
                        message=(
                            f"Max retries exceeded for {tool_name}. "
                            f"Task failed: {result.error}"
                        ),
                        data={"error": result.error},
                    )
                    task.status = TaskStatus.FAILED
                    task.error = f"Max retries exceeded: {result.error}"
                    # Persist final failed state
                    try:
                        audit = await get_audit_store()
                        await audit.save_task(
                            task_id=task.task_id, goal=task.goal,
                            status=task.status.value,
                            created_at=task.created_at,
                            error=task.error,
                            total_steps=len(task.history),
                        )
                    except Exception:
                        pass
                    return

        # ── COMPLETION ───────────────────────────────────────────
        if task.status != TaskStatus.FAILED:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.memory = memory.to_dict()

            # Persist completed task to audit store
            try:
                audit = await get_audit_store()
                await audit.save_task(
                    task_id=task.task_id,
                    goal=task.goal,
                    status=task.status.value,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                    total_steps=len(task.history),
                    memory=task.memory,
                )
            except Exception:
                pass

            yield AgentEvent(
                event_type=EventType.TASK_COMPLETE,
                message="Task completed successfully.",
                data={
                    "memory": memory.to_dict(),
                    "total_steps": len(task.history),
                    "verification": (
                        task.verification.model_dump()
                        if task.verification
                        else None
                    ),
                },
            )

    # ── Approval ─────────────────────────────────────────────────

    def provide_approval(self, approved: bool) -> None:
        """
        Called by the WebSocket route when the user approves/rejects.
        Unblocks the agent loop.
        """
        self._approval_result = approved
        if self._approval_event:
            self._approval_event.set()

    # ── Memory Helpers ───────────────────────────────────────────

    def _update_memory(
        self, memory: ExecutionMemory, tool_name: str, data: dict
    ) -> None:
        """
        Intelligently update agent memory based on tool results.

        Each tool's output is mapped to meaningful memory keys so
        downstream tools can reference discovered data.
        """
        if tool_name == "search_invoices":
            invoices = data.get("invoices", [])
            if invoices:
                memory.set("search_results", invoices)
                # Auto-select the latest invoice by due date
                latest = max(
                    invoices, key=lambda x: x.get("due_date", "")
                )
                memory.set("selected_invoice_id", latest["invoice_id"])
                memory.set("selected_company", latest["company"])

        elif tool_name == "read_invoice_details":
            invoice = data.get("invoice", {})
            if invoice:
                memory.set("invoice_details", invoice)
                memory.set("invoice_id", invoice.get("invoice_id"))
                memory.set("amount", invoice.get("amount"))
                memory.set("due_date", invoice.get("due_date"))
                memory.set("company", invoice.get("company"))

        elif tool_name == "submit_invoice":
            record = data.get("record", {})
            if record:
                memory.set("submission_record", record)
                memory.set("record_id", record.get("record_id"))

        elif tool_name == "verify_submission":
            memory.set("verification", data)

        elif tool_name == "search_emails":
            emails = data.get("emails", [])
            if emails:
                memory.set("found_emails", emails)
                memory.set("latest_email_id", emails[0].get("id"))

        elif tool_name == "read_email":
            email = data.get("email", {})
            if email:
                memory.set("email_content", email)
                # If email has invoice info, map it
                body = email.get("body", "")
                memory.set("email_body", body)

        elif tool_name == "save_file":
            memory.set("saved_file_path", data.get("path"))

        elif tool_name == "read_file":
            memory.set("file_content", data.get("content"))

        elif tool_name in ("browser_navigate", "browser_screenshot"):
            if data.get("screenshot_path"):
                memory.set("last_screenshot", data.get("screenshot_path"))
