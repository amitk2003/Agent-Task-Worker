# Autonomous AI Task Worker — Project Discussion & Implementation Guide

## 1. What the assignment is asking

The assignment asks for a prototype of an **Autonomous AI Task Worker**.

In simple terms:

> Build an AI agent that receives a natural-language business goal, figures out the steps required, uses a computer/tools to perform those steps, observes what happened, decides what to do next, handles failures, verifies the final outcome, and reports the result to the user.

Example request:

> “Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done.”

The system should not merely explain how to do this. It should actually attempt to perform the work.

---

# 2. Chatbot vs Autonomous AI Worker

## Normal chatbot

User:

> Find my latest invoice.

AI:

> You can find it in the billing portal under invoices.

The chatbot gives instructions.

## Autonomous worker

User:

> Find my latest invoice.

The worker should independently:

1. Open the relevant application.
2. Navigate to invoices.
3. Search for the relevant company.
4. Identify the latest invoice.
5. Extract the required information.
6. Perform the requested update/action.
7. Check whether the action succeeded.
8. Recover from reasonable failures.
9. Verify the final state.
10. Report the result and evidence.

The key difference is **execution**.

---

# 3. Mental model: AI employee

Think of the system as a small AI employee.

```text
                 User Task
                     |
                     v
              +--------------+
              | AI Planner   |
              | Understand   |
              | Goal         |
              +------+-------+
                     |
                     v
              +--------------+
              | AI Worker    |
              | Choose next  |
              | action       |
              +------+-------+
                     |
          +----------+----------+
          |          |          |
          v          v          v
       Browser     Files       APIs
          |          |          |
          +----------+----------+
                     |
                     v
              +--------------+
              |   Observe    |
              | What happened|
              +------+-------+
                     |
                     v
              +--------------+
              |   Decide     |
              | What next?   |
              +------+-------+
                     |
               +-----+-----+
               |           |
               v           v
             Done       Retry /
                        Alternative
```

---

# 4. Core execution loop

The most important technical concept is:

```text
OBSERVE
   ↓
DECIDE
   ↓
ACT
   ↓
OBSERVE
   ↓
DECIDE
   ↓
ACT
   ↓
...
```

The agent should not blindly generate one giant plan and execute it without checking the environment.

Example:

### Step 1

Observe:

```text
Browser is showing the login page.
```

Decision:

```text
Need to log in.
```

Action:

```text
Enter username
Enter password
Click login
```

### Step 2

Observe:

```text
Dashboard is visible.
```

Decision:

```text
Need to find invoices.
```

Action:

```text
Click Invoices
```

### Step 3

Observe:

```text
Invoice table is displayed.
```

Decision:

```text
Need latest invoice from ABC Ltd.
```

Action:

```text
Search/filter ABC Ltd.
```

And so on.

---

# 5. Why unexpected states matter

Real applications do not always behave exactly as expected.

Example:

The agent wants to click Submit, but the application says:

```text
Session expired.
Please log in again.
```

A weak system crashes.

A better agent reasons:

```text
Expected:
Submission should succeed.

Actual:
Session expired.

Recovery:
Log in again → return to form → submit again.
```

This demonstrates **reliability**.

---

# 6. Retry and alternative actions

Suppose the agent searches for:

```text
ABC Ltd
```

and receives:

```text
No results found.
```

A robust agent can attempt a reasonable alternative:

```text
Try:
"ABC"

or:
search by invoice sender

or:
search files instead of the web application
```

The important point is that the system should not immediately stop when an expected action fails.

---

# 7. Verification is critical

A common bad implementation is:

```text
Click Save
↓
Assume success
↓
Tell user "Done"
```

A better implementation is:

```text
Click Save
↓
Observe confirmation
↓
Reopen the record
↓
Check stored values
↓
Compare with intended values
↓
Mark task as verified
```

For example:

```text
Expected address:
Pune, Maharashtra

Actual address after update:
Pune, Maharashtra

VERIFIED ✓
```

Only then should the system report successful completion.

---

# 8. Temporary memory / execution state

The worker needs to remember information discovered during the task.

For example:

```json
{
  "invoice_number": "ABC-1023",
  "company": "ABC Ltd",
  "amount": 45000,
  "due_date": "2026-10-15"
}
```

This information can then be used when interacting with another application.

For a prototype, sophisticated long-term memory is not required. Structured execution state is likely enough.

---

# 9. User approval

The worker should know when it cannot safely continue without the user.

Example:

```text
Invoice amount: ₹4,50,000

The next action will submit this amount
to the internal billing system.

Do you want me to continue?
```

The user approves:

```text
Yes.
```

Then the agent proceeds.

For a prototype, one clear approval mechanism is sufficient to demonstrate the concept.

---

# 10. Recommended narrow prototype

Do NOT try to build a general-purpose computer-use agent.

The assignment explicitly says:

> A narrow prototype that genuinely works is better than a broad system where most functionality is mocked.

A strong project could be:

## Invoice Processing AI Worker

User:

> “Process the latest invoice from Acme.”

The worker:

1. Finds the invoice.
2. Extracts invoice information.
3. Stores information in execution memory.
4. Opens a simulated internal finance application.
5. Enters the data.
6. Submits it.
7. Verifies the resulting record.
8. Reports success with evidence.

This single workflow can demonstrate almost every evaluation criterion.

---

# 11. Simulated environment is acceptable

The assignment explicitly allows a:

> simulated company application

Therefore, real websites are not necessary.

You can build a small mock environment.

## Invoice Portal

```text
+--------------------------------------+
|          ACME INVOICE PORTAL         |
+--------------------------------------+
| Search: [ ABC Ltd             ] [🔍] |
|                                      |
| Invoice       Date       Amount      |
| ABC-1023      02 Oct     ₹45,000     |
| ABC-1019      20 Sep     ₹32,000     |
+--------------------------------------+
```

## Internal Finance System

```text
+--------------------------------------+
|       INTERNAL FINANCE SYSTEM        |
+--------------------------------------+
| Invoice No: [____________]           |
| Vendor:     [____________]           |
| Amount:     [____________]           |
| Due Date:   [____________]           |
|                                      |
|             [ SUBMIT ]               |
+--------------------------------------+
```

The AI worker interacts with both applications.

---

# 12. Recommended architecture

A suitable architecture, especially given experience with Python/FastAPI and React:

```text
                    +------------------+
                    |   React UI       |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    FastAPI       |
                    |    Agent API     |
                    +--------+---------+
                             |
                             v
                +-------------------------+
                |     Agent Runtime       |
                |                         |
                | Planner                 |
                | Decision Maker           |
                | State Manager            |
                | Verifier                 |
                | Error Handler            |
                +-----------+-------------+
                            |
                +-----------+-----------+
                |           |           |
                v           v           v
             Browser      Files        APIs
                |           |           |
                v           v           v
           Playwright    Python      Internal
                                     System
```

---

# 13. Role of the LLM

Do not make the LLM responsible for everything.

Give the LLM tools.

Example:

```python
tools = [
    search_invoice,
    read_invoice,
    open_finance_app,
    fill_invoice_form,
    submit_invoice,
    verify_invoice,
]
```

The LLM decides:

```text
Goal:
Process latest invoice from ABC.

→ search_invoice("ABC")
```

Tool returns:

```json
{
  "invoice_id": "ABC-1023",
  "amount": 45000,
  "due_date": "2026-10-15"
}
```

The LLM then decides:

```text
Invoice found.

Next I need to enter it into the finance system.

→ open_finance_app()
```

Then:

```text
→ fill_invoice_form(...)
→ submit_invoice()
→ verify_invoice(...)
```

The key architectural separation is:

```text
LLM
↓
Reasoning / decision making

Tools
↓
Actual execution
```

---

# 14. Browser automation

Playwright is a good option for browser automation.

Example:

```python
await page.goto("http://invoice-portal")

await page.fill(
    "#search",
    "ABC Ltd"
)

await page.click("#search-button")
```

Then observe the page:

```python
content = await page.locator("body").inner_text()
```

The agent can receive:

```text
Invoice ABC-1023
Vendor: ABC Ltd
Amount: ₹45,000
Due Date: 15 Oct 2026
```

It can then decide what action to perform next.

---

# 15. Strong demonstration scenario

A particularly good demo intentionally includes a failure.

User:

> Process the latest invoice from ABC Ltd.

Agent:

```text
Searching invoice portal...
```

Finds:

```text
ABC-1023
₹45,000
15 Oct 2026
```

Then:

```text
Opening finance system...
```

The mock system intentionally returns:

```text
ERROR:
Session expired.
```

The agent detects the failure:

```text
Action failed.

Reason:
Session expired.

Attempting recovery...
```

Then:

```text
Re-authenticate
↓
Return to invoice form
↓
Enter data again
↓
Submit
```

Then:

```text
Submission successful.
```

Finally:

```text
Reopening record...
Checking invoice ABC-1023...

Invoice: ABC-1023 ✓
Amount: ₹45,000 ✓
Due Date: 15 Oct 2026 ✓

Task verified.
```

This single demo shows:

- Autonomy
- Execution
- Observation
- Failure detection
- Recovery
- Memory
- Verification

---

# 16. Suggested UI

A simple React dashboard could show:

```text
+------------------------------------------------+
|            AUTONOMOUS AI WORKER                |
+------------------------------------------------+
|                                                |
| Task                                           |
| +--------------------------------------------+ |
| | Process the latest invoice from ABC Ltd   | |
| +--------------------------------------------+ |
|                                                |
|               [ Run Task ]                    |
|                                                |
+------------------------------------------------+
| EXECUTION                                      |
|                                                |
| ✓ Understand task                              |
| ✓ Search invoice portal                        |
| ✓ Found ABC-1023                               |
| ✓ Extract amount: ₹45,000                      |
| ✓ Extract due date: 15 Oct 2026                |
| ✓ Open finance system                          |
| ⚠ Session expired                              |
| ✓ Re-authenticated                             |
| ✓ Submitted invoice                            |
| ✓ Verified invoice                             |
|                                                |
+------------------------------------------------+
| RESULT                                         |
|                                                |
| ✓ Task completed successfully                  |
|                                                |
| Invoice: ABC-1023                              |
| Amount: ₹45,000                                |
| Due: 15 Oct 2026                               |
|                                                |
| Evidence:                                      |
| [View execution log] [View screenshot]        |
+------------------------------------------------+
```

The evaluator should be able to see the autonomous behavior rather than only hearing about it.

---

# 17. Generalization

Avoid a workflow like:

```python
if task == "process ABC invoice":
    do_abc_invoice()
```

That is hardcoded.

Instead, the same agent should be able to handle variations such as:

```text
"Process the latest invoice from ABC."

"Find the latest invoice from XYZ and update finance."

"Get the newest invoice from Acme and enter it into the billing system."
```

The underlying agent stays the same.

Only the natural-language goal changes.

This addresses the evaluation criterion:

> Generalization — How much of the system can remain unchanged when given a different task?

---

# 18. Recommended technology stack

Given the existing experience with Python/FastAPI and React:

```text
Frontend:
React + Tailwind

Backend:
Python + FastAPI

Agent:
LLM API + structured tool calling

Browser automation:
Playwright

Database:
PostgreSQL or SQLite

Optional:
Redis for execution state

LLM:
GPT / Claude / Gemini / Groq
```

LangChain or LangGraph are optional. They are not required just because this is an AI-agent project.

A custom agent loop can actually make the architecture easier to explain.

---

# 19. Core agent loop

Conceptually:

```python
while not task_completed:

    state = observe_environment()

    decision = llm.decide(
        goal=goal,
        state=state,
        memory=memory,
        available_tools=tools
    )

    if decision.requires_approval:
        ask_user()

    result = execute(decision)

    memory.update(result)

    if result.failed:
        handle_failure()

    if verify_goal():
        task_completed = True
```

This loop is the heart of the project.

---

# 20. Preventing infinite loops

The agent should have bounded retries and steps.

For example:

```python
MAX_STEPS = 15
MAX_RETRIES = 2
```

Maintain execution history:

```text
Action failed
↓
Retry #1
↓
Failed
↓
Retry #2
↓
Failed
↓
Stop and ask user / report failure
```

Avoid:

```text
retry
retry
retry
retry
retry
...
```

---

# 21. Explicit execution state

A useful state representation could be:

```json
{
  "goal": "Process latest invoice from ABC Ltd",
  "status": "running",
  "current_step": "verify_submission",

  "memory": {
    "invoice_id": "ABC-1023",
    "amount": 45000,
    "due_date": "2026-10-15"
  },

  "history": [
    {
      "action": "search_invoice",
      "result": "success"
    },
    {
      "action": "extract_invoice",
      "result": "success"
    },
    {
      "action": "submit_invoice",
      "result": "session_expired"
    },
    {
      "action": "reauthenticate",
      "result": "success"
    },
    {
      "action": "submit_invoice",
      "result": "success"
    }
  ],

  "verification": {
    "invoice_id": true,
    "amount": true,
    "due_date": true
  }
}
```

This makes the system observable and debuggable, which is strong engineering practice.

---

# 22. What NOT to build

## 1. A chatbot pretending to execute

Bad:

```text
AI:
"I have successfully updated the invoice."
```

when nothing actually happened.

## 2. Completely hardcoded workflow

For example:

```python
click_x()
click_y()
click_z()
```

with no decision-making.

## 3. 50 mocked features

For example:

```text
Browser agent
Email agent
Slack agent
Calendar agent
Excel agent
CRM agent
GitHub agent
...
```

where almost nothing genuinely works.

The assignment explicitly prefers:

> A narrow prototype that genuinely works.

---

# 23. Likely technical interview questions

## Why did you use an LLM?

Suggested answer:

> The LLM is used for interpreting the user's natural-language goal and selecting the next action based on the current environment state. Deterministic tools handle actual execution.

## Why not hardcode the workflow?

Suggested answer:

> The goal is to demonstrate autonomous task execution. The same agent should be able to handle variations in the task without changing the underlying workflow.

## How do you know the task succeeded?

Suggested answer:

> I don't assume that a successful API response or button click means completion. The system performs a separate verification step against the resulting state.

## What happens when an action fails?

Suggested answer:

> The agent observes the failure, determines whether it is recoverable, and attempts a bounded retry or alternative action. If it cannot safely recover, it asks the user or reports the failure.

## How do you prevent the agent from looping forever?

Suggested answer:

> I use a maximum step limit, bounded retries, and execution history. If recovery attempts are exhausted, the agent stops instead of repeatedly performing the same action.

---

# 24. One-sentence project explanation

A strong interview description:

> **"I'm building an autonomous AI worker that converts a natural-language business goal into a sequence of tool actions, observes the environment after each action, maintains execution state, recovers from failures, and independently verifies that the requested outcome was actually achieved."**

---

# 25. Recommended final project direction

The recommended implementation is:

```text
                 React Dashboard
                       |
                       v
                    FastAPI
                       |
                       v
              Agent Controller
              /       |       \
             /        |        \
        Planner     Memory    Verifier
             \        |        /
              \       |       /
                 Tool Layer
                /     |      \
               /      |       \
        Playwright   Files    Mock API
             |                 |
             v                 v
       Invoice Portal    Finance System
```

Focus on:

1. One real workflow.
2. Natural-language task input.
3. Autonomous next-action selection.
4. Real tool execution.
5. Observation after every action.
6. Structured execution memory.
7. Failure detection.
8. Bounded retry/recovery.
9. User approval when appropriate.
10. Independent final verification.
11. Visible execution trace.
12. Evidence of completion.

A single workflow implemented this way is more valuable than a large collection of superficial features.

---

# 26. Overall interpretation of the assignment

The company is **not primarily asking for a chatbot, RAG system, or generic automation script**.

They are testing whether you can think about an AI agent as a software system:

```text
Natural-language goal
        ↓
Goal understanding
        ↓
Planning / next-action selection
        ↓
Tool execution
        ↓
Environment observation
        ↓
State / memory update
        ↓
Failure handling
        ↓
Verification
        ↓
Completion / human escalation
```

The most important product principle is:

> **The agent should optimize for accomplishing the user's actual goal, not merely generating a convincing response.**

The most important engineering principle is:

> **Never assume an action succeeded just because the action was executed. Observe and verify the resulting state.**

The most important scope principle is:

> **Build one narrow workflow that genuinely works end-to-end rather than a broad system where most capabilities are mocked.**

