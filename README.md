# Autonomous AI Task Worker

An end-to-end prototype of an **Autonomous AI Task Worker** that accepts natural-language business goals, decomposes them into tool actions, executes them against external systems, observes results, recovers from unexpected errors, and independently verifies business outcomes.

---

## 🏗️ Architecture & Mental Model

```
                    ┌─────────────────────────┐
                    │     React Dashboard     │
                    │  (Vite + Tailwind CSS)  │
                    └────────────┬────────────┘
                                 │ REST + WebSocket
                                 ▼
                    ┌─────────────────────────┐
                    │     FastAPI Backend     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Agent Controller     │
                    │ (Observe → Decide → Act)│
                    └────┬───────────┬────────┘
                         │           │
           LLM Decisions │           │ Tool Execution
                         ▼           ▼
        ┌──────────────────┐    ┌───────────────────────────┐
        │  Planner (Groq)  │    │       Tool Registry       │
        │ llama-3.1-70b-v  │    ├───────────────────────────┤
        └──────────────────┘    │ • search_invoices         │
                                │ • read_invoice_details    │
                                │ • open_finance_system     │
                                │ • fill_invoice_form       │
                                │ • submit_invoice          │
                                │ • verify_submission       │
                                └─────────────┬─────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
        ┌───────────────────────────┐                   ┌───────────────────────────┐
        │    Mock Invoice Portal    │                   │   Internal Finance System │
        │  (ABC Ltd, XYZ, Acme...)  │                   │ (Session Expiry Recovery) │
        └───────────────────────────┘                   └───────────────────────────┘
```

---

## 🌟 Key Features

1. **Autonomous Execution Loop (Observe → Decide → Act)**
   - No hardcoded sequences. The LLM decides what to do next based on the observed state after each step.
2. **Deterministic Independent Verification**
   - The agent never assumes success from an API call or button click. It re-opens and queries the ledger to confirm invoice number, vendor, amount, and due date match expectations.
3. **Intentional Failure & Autonomous Recovery**
   - The mock finance system triggers a `Session expired` error on the first submit attempt. The agent detects this failure, re-authenticates, re-populates the form, and re-submits without crashing.
4. **Human-in-the-Loop Approval**
   - When reaching high-stakes financial operations (`fill_invoice_form` before `submit_invoice`), the agent pauses and prompts the user for explicit confirmation before proceeding.
5. **Generalization across Vendors**
   - Handles different company names (`ABC Ltd`, `XYZ Corp`, `Acme Industries`) dynamically through the same agent architecture without code changes.
6. **Live Environment Inspector**
   - The dashboard includes a live inspector showing invoices in the portal and ledger records in the finance system before and after execution.

---

## 🚀 Getting Started

### 1. Backend Setup

```bash
cd backend

# Create .env from template
cp .env.example .env
```

Edit `backend/.env` and add your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
MAX_STEPS=15
MAX_RETRIES_PER_STEP=2
```

Start the FastAPI backend:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be accessible at: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:5173`

---

## 🧪 Demonstration Walkthrough

1. Open `http://localhost:5173`.
2. Notice the **Live System Inspector** at the bottom showing the 5 invoices in the portal and 0 recorded in the Finance System.
3. Click the preset: **"ABC Ltd (with error recovery)"** and click **Run Task Worker**.
4. **Step 1 — Search**: Agent searches for "ABC Ltd" and finds `ABC-1023` and `ABC-1019`.
5. **Step 2 — Read**: Agent extracts amount (₹45,000) and due date (2026-10-15) for the latest invoice.
6. **Step 3 — Open System**: Agent opens the finance system.
7. **Step 4 — Fill Form & Approval**: Form is filled, triggering a **Human-in-the-Loop** confirmation modal. Click **Approve & Continue**.
8. **Step 5 — Failure Trigger**: The finance system intentionally returns `Session expired. Please re-authenticate and try again.`
9. **Step 6 — Autonomous Recovery**: Notice the amber recovery event. The agent re-authenticates, re-fills the form, and re-submits.
10. **Step 7 — Verification**: The agent calls `verify_submission`, re-reading the stored ledger entry.
11. **Outcome**: The Outcome card shows all 4 checkmarks (`invoice_no_match`, `vendor_match`, `amount_match`, `due_date_match`) and the recorded ledger entry ID.
12. Inspect the **Live System Inspector** again to see the new record recorded in the ledger!

---

## 🔧 Extensibility Guide: How to Add Features

### Adding a New Tool
1. Create a file in `backend/tools/my_new_tool.py`:
   ```python
   from tools.base import BaseTool, ToolResult

   class MyNewTool(BaseTool):
       @property
       def name(self) -> str:
           return "my_new_tool"

       @property
       def description(self) -> str:
           return "Detailed description for the LLM planner."

       @property
       def parameters(self) -> dict:
           return {
               "type": "object",
               "properties": {
                   "param1": {"type": "string", "description": "Parameter description"}
               },
               "required": ["param1"]
           }

       async def execute(self, **kwargs) -> ToolResult:
           # Perform action
           return ToolResult(success=True, data={"result": "..."})
   ```
2. Register it in `backend/api/routes.py` inside `create_tool_registry()`:
   ```python
   registry.register(MyNewTool(...))
   ```
3. That's it! The agent will automatically see the tool schema and know when to use it based on natural-language goals.
