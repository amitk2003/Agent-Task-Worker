"""
LLM-based planner — the "brain" of the agent.

Uses Groq's function-calling API to decide the next action
based on the current goal, memory, and execution history.

Design notes:
- Temperature is set low (0.1) for deterministic, predictable decisions.
- The system prompt enforces tool usage — the LLM must always call a tool.
- Context is built fresh each iteration so the LLM sees the latest state.
- To swap LLM providers, change the client initialization and keep
  the rest of the interface identical (OpenAI-compatible format).
"""

import json

from groq import AsyncGroq

from config import get_settings
from agent.models import StepRecord


# ── System Prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an autonomous AI task worker. Your job is to accomplish the user's business goal by executing the available tools step-by-step.

CAPABILITIES AVAILABLE:
- INVOICES & FINANCE: search_invoices, read_invoice_details, open_finance_system, fill_invoice_form, submit_invoice, verify_submission
- EMAIL OPERATIONS: search_emails, read_email, send_email (notify users/managers upon completion)
- FILE OPERATIONS: list_files, read_file, save_file (export reports, audit logs, summaries)
- BROWSER & VISUAL EVIDENCE: browser_navigate (open web pages/portals), browser_screenshot (capture visual proof)

RULES:
1. After each tool result, decide what to do next based on what you OBSERVED.
2. If something fails, attempt recovery (e.g., re-authenticate if session expired, then re-fill form and re-submit).
3. Do NOT assume an action succeeded — always observe the result before moving on.
4. When finance actions are done, ALWAYS use verify_submission to confirm the final outcome.
5. If the user asks to send an email, check emails, read a file, save an audit report, or capture browser evidence, use the appropriate tools.
6. Keep your reasoning concise — one sentence max.
7. You MUST call exactly one tool in every response. Never respond with just text.

FAILURE RECOVERY:
- If submit_invoice fails with "Session expired": call open_finance_system to re-authenticate, then fill_invoice_form again, then submit_invoice again.
- If search returns no results: try searching emails or checking local files for backup copies.
"""


class Planner:
    """
    Decides the agent's next action via LLM function calling.

    The planner is stateless — all context is passed in per call.
    This makes it easy to test and to swap implementations.
    """

    def __init__(self):
        settings = get_settings()
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    async def decide_next_action(
        self,
        goal: str,
        memory: dict,
        history: list[StepRecord],
        tool_schemas: list[dict],
    ) -> dict:
        """
        Ask the LLM to decide the next action.

        Args:
            goal:         Natural-language task description.
            memory:       Current execution memory (discovered data).
            history:      List of steps taken so far.
            tool_schemas: OpenAI-compatible tool schemas for function calling.

        Returns:
            dict with keys:
                tool_name:  str | None  (None means LLM thinks task is done)
                tool_args:  dict
                reasoning:  str
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._build_context(goal, memory, history)},
        ]

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=1024,
        )

        message = response.choices[0].message
        reasoning = message.content or ""

        # Extract the tool call if present
        if message.tool_calls and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            return {
                "tool_name": tool_call.function.name,
                "tool_args": json.loads(tool_call.function.arguments),
                "reasoning": reasoning,
            }

        # No tool call — LLM believes task is complete (or is confused)
        return {
            "tool_name": None,
            "tool_args": {},
            "reasoning": reasoning,
        }

    def _build_context(
        self,
        goal: str,
        memory: dict,
        history: list[StepRecord],
    ) -> str:
        """
        Build a single context string for the LLM.

        Includes the goal, current memory, and step-by-step history
        so the LLM can reason about what happened and what to do next.
        """
        parts = [f"GOAL: {goal}"]

        if memory:
            parts.append(
                f"\nCURRENT MEMORY (data discovered so far):\n"
                f"{json.dumps(memory, indent=2)}"
            )

        if history:
            parts.append("\nEXECUTION HISTORY:")
            for step in history:
                icon = {
                    "success": "✓",
                    "failed": "✗",
                    "recovered": "↺",
                    "skipped": "–",
                }.get(step.status.value, "?")

                parts.append(
                    f"  {icon} Step {step.step_number}: "
                    f"{step.tool_name}({json.dumps(step.tool_args)}) → {step.status.value}"
                )
                if step.error:
                    parts.append(f"    Error: {step.error}")
                if step.result:
                    result_str = json.dumps(step.result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    parts.append(f"    Result: {result_str}")

        parts.append(
            "\nDecide the next action. You MUST call exactly one tool."
        )

        return "\n".join(parts)
