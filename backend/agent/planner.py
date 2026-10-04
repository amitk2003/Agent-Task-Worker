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

CORE RULES:
1. After each tool result, decide what to do NEXT based purely on what you OBSERVED — not what you expected.
2. NEVER assume a previous action succeeded. Read the result carefully before proceeding.
3. Do NOT repeat a tool call with identical arguments if it just failed — change the approach.
4. After finance actions, ALWAYS call verify_submission to confirm the actual outcome.
5. Keep your reasoning to one sentence.
6. You MUST call exactly one tool per response. Never respond with only text.

INDEPENDENT RECOVERY PLAYBOOK (use these when you observe failures):

  SESSION EXPIRED (from submit_invoice or fill_invoice_form):
    → call open_finance_system  (re-authenticate)
    → call fill_invoice_form again with same data from memory
    → call submit_invoice again

  SEARCH RETURNS EMPTY (from search_invoices):
    → try search_emails with a related keyword (e.g., vendor name)
    → if email found: call read_email to extract invoice details
    → if still empty: call list_files to check local file storage

  FILE NOT FOUND (from read_file):
    → call list_files to see what files actually exist
    → choose the closest matching file and call read_file again

  UNKNOWN TOOL CALLED (tool does not exist):
    → check the available tool list and call the correct tool name
    → NEVER repeat the same unknown tool name

  SUBMIT FAILS (non-session error):
    → call verify_submission first — the record may have been saved despite the error
    → if not verified: call fill_invoice_form then submit_invoice once more

  SEND EMAIL FAILS:
    → call save_file to write the notification as a local audit record instead
    → then call send_email again once with fixed parameters

COMPLETION CRITERIA:
- For invoice/finance tasks: verified=true in verify_submission result
- For email tasks: send_email returned success=true
- For file tasks: save_file returned success=true
- For browser tasks: browser_screenshot captured evidence
- If ALL expected outcomes are confirmed: output your final reasoning WITHOUT calling a tool (this ends the task)
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
