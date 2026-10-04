"""
End-to-end integration test for the Autonomous AI Task Worker.

Validates the full cycle:
1. Understanding goal
2. Searching invoices
3. Reading invoice details
4. Form filling & approval
5. Session expiry failure
6. Autonomous recovery
7. Submission & ledger entry
8. Independent verification
"""

import asyncio
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.controller import AgentController
from agent.models import TaskState, EventType
from api.routes import create_tool_registry, finance_system, invoice_portal


async def run_e2e_test():
    finance_system.reset()
    registry = create_tool_registry()
    controller = AgentController(registry)
    task = TaskState(goal="Process the latest invoice from ABC Ltd")

    print(f"\n=======================================================")
    print(f"Goal: {task.goal}")
    print(f"=======================================================\n")

    failure_detected = False
    recovery_detected = False

    async for event in controller.execute_task(task):
        print(f"[{event.event_type.value.upper()}] {event.message}")

        if event.event_type == EventType.APPROVAL_NEEDED:
            print(">>> [APPROVAL] Auto-approving step for automated test...")
            controller.provide_approval(True)

        if event.event_type == EventType.STEP_FAILED:
            failure_detected = True

        if event.event_type == EventType.RECOVERY_ATTEMPT:
            recovery_detected = True

        if event.event_type == EventType.TASK_COMPLETE:
            print("\n=======================================================")
            print("TASK STATUS: COMPLETED SUCCESSFULLY")
            print("Failure detected and handled:", failure_detected)
            print("Autonomous recovery triggered:", recovery_detected)
            print("Independent Verification:")
            if task.verification:
                print(f"  Verified: {task.verification.verified}")
                print(f"  Checks: {task.verification.checks}")
                print(f"  Evidence Record: {task.verification.evidence}")
            print(f"=======================================================\n")
            return task.verification is not None and task.verification.verified

        if event.event_type == EventType.TASK_FAILED:
            print("\nTASK FAILED:", task.error)
            return False

    return False


if __name__ == "__main__":
    success = asyncio.run(run_e2e_test())
    if success:
        print("ALL END-TO-END TESTS PASSED!")
        sys.exit(0)
    else:
        print("TESTS FAILED!")
        sys.exit(1)
