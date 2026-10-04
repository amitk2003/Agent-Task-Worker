# Autonomous AI Task Worker

An end-to-end prototype of an **Autonomous AI Task Worker** that accepts natural-language business goals, decomposes them into tool actions, executes them against external systems, observes results, recovers from unexpected errors, and independently verifies business outcomes.

---

## 🧾 Project Description

This is a prototype of an **Autonomous AI Task Worker** — a system where a user describes a business goal in plain English (e.g. *"Find the latest invoice from TechCorp, enter it into the finance system, and confirm once done"*), and the AI agent breaks it into steps, picks the right tools, executes them in sequence, handles errors, and verifies the outcome — all without any manual intervention. The system supports invoice processing, finance entry, email search & sending, file read/write, and browser navigation. It demonstrates real-world office automation using an LLM-powered autonomous loop with human-in-the-loop safety checks for high-stakes actions.

---

## 🏗️ Overall Architecture

```
+--------------------------------------------------+
|              React Frontend  (port 5173)         |
|   TaskInput -> ExecutionLog -> EnvironmentInspector|
+---------------------+----------------------------+
                      |  HTTP (REST) + WebSocket
+---------------------v----------------------------+
|             FastAPI Backend  (port 8000)         |
|  +-----------+  +-----------------------------+  |
|  | API Routes|  |      Agent Controller       |  |
|  | /api/*    |  |  observe -> decide -> act   |  |
|  +-----------+  +------------+----------------+  |
|                              |                   |
|               +--------------v-----------+       |
|               |   Planner (Groq LLM)    |       |
|               |   decides next tool     |       |
|               +--------------+----------+       |
|                              |                   |
|               +--------------v-----------+       |
|               |      Tool Registry      |       |
|               |  12 tools registered    |       |
|               +--------------+----------+       |
|                              |                   |
|   +---------------------------v---------------+  |
|   |            Mock Environments             |  |
|   |  InvoicePortal | FinanceSystem           |  |
|   |  EmailSystem   | FileManager             |  |
|   |  BrowserEngine (Playwright + httpx)      |  |
|   +------------------------------------------+  |
+--------------------------------------------------+
```

**Data flow in one sentence:**
User task -> `POST /api/tasks` -> `AgentController` loops (LLM picks tool -> tool runs -> result stored in memory -> event streamed via WebSocket -> repeat) -> task verified -> WebSocket closes.

---

## 🤖 Which Parts Are Autonomous

| Part | Autonomous? | Details |
|---|---|---|
| Task decomposition | Yes | LLM decides the full sequence of steps from a single sentence |
| Tool selection | Yes | LLM picks the right tool and arguments each iteration |
| Error recovery | Yes | Agent retries and re-authenticates on session expiry |
| Task verification | Yes | Agent independently re-reads the system to confirm success |
| Human-in-the-loop pause | Hybrid | Agent pauses before high-stakes writes; user approves |
| Environment data | No | Invoice/email/file data is pre-seeded mocks |

---

## 🔩 What Is Currently Hardcoded or Manually Configured

| Item | Location | Notes |
|---|---|---|
| Groq API key & model | `backend/.env` | Must be set manually before running |
| Invoice mock data | `mock_env/invoice_portal.py` | Pre-seeded list of 5 invoices |
| Email mock data | `mock_env/email_system.py` | Pre-seeded inbox/outbox |
| Finance system session-expiry error | `mock_env/finance_system.py` | Intentionally injected on first submit |
| Max steps & retries | `backend/.env` | `MAX_STEPS=15`, `MAX_RETRIES_PER_STEP=3` |
| High-stakes tool list | `agent/controller.py` | Tools that trigger approval are hardcoded by name |
| File sandbox path | `mock_env/file_manager.py` | Writes only to `backend/storage/` |
| CORS origins | `backend/main.py` | Hardcoded to `localhost:5173` |

---

## 🛠️ Models, APIs, Frameworks & Tools Used

| Category | Tool / Library | Purpose |
|---|---|---|
| **LLM** | Groq API (`openai/gpt-oss-120b`) | Planning, tool selection, verification |
| **Backend framework** | FastAPI | REST API + WebSocket server |
| **ASGI server** | Uvicorn / Gunicorn + UvicornWorker | Dev and production serving |
| **Frontend framework** | React (Vite) | UI dashboard |
| **Real-time communication** | WebSocket (native FastAPI) | Live event streaming to UI |
| **Browser automation** | Playwright (Chromium) + httpx fallback | BrowserEngine tool |
| **Data validation** | Pydantic v2 | Request/response models |
| **Config management** | pydantic-settings + python-dotenv | `.env` loading |
| **AI Coding Tool** | Google Antigravity (Gemini) | Entire project built with AI pair programming |

---

## ⚠️ Biggest Technical Limitations

1. **No persistent state** — All task history, invoices, emails, and finance records live in Python in-memory objects. A server restart wipes everything. There is no database.

2. **Single-user, single-task** — The agent controller is not designed for concurrent tasks. Multiple simultaneous users would share the same mock environments and potentially corrupt each other's state.

3. **LLM non-determinism** — The planner relies on the LLM returning a strictly structured JSON. If the model returns free text or deviates from the schema, the agent fails. There is basic error handling but no robust prompt self-healing.

4. **Mock environments only** — The system does not connect to any real email, ERP, or browser target. All "external systems" are Python dictionaries with fake data. Replacing them with real integrations would require significant rework.

5. **No memory across tasks** — Each task starts fresh. The agent has no persistent memory of previous runs, learned preferences, or past mistakes.

---

## 🔮 Future Improvements

- **Persistent database** — Replace in-memory mocks with PostgreSQL/SQLite so state survives restarts and supports multiple users.
- **Real integrations** — Connect to Gmail API, real ERP systems (QuickBooks, SAP), and public websites via Playwright.
- **Multi-agent support** — Spawn parallel sub-agents for tasks that can be done concurrently (e.g., processing 10 invoices at once).
- **Agent memory** — Add vector-store-based long-term memory so the agent learns from past task runs.
- **Better LLM reliability** — Add structured output enforcement (e.g., Instructor or function calling) to guarantee valid JSON from the planner.
- **Auth & multi-tenancy** — Add user accounts so multiple teams can run tasks independently with isolated data.

---

## 🏖️ If I Had 2 More Weeks, I Would Build...

**Week 1 — Real-world integrations**
- Connect `EmailSystem` to Gmail via OAuth
- Connect `FinanceSystem` to a real QuickBooks sandbox API
- Add a real database (PostgreSQL) to persist tasks, results, and audit logs
- Replace the Playwright mock target with real public websites for evidence capture

**Week 2 — Intelligence & scale**
- Add **long-term agent memory** using a vector DB (Chroma/Pinecone) — agent remembers vendor preferences, recurring tasks, and past errors
- Build a **task scheduler** so users can say "Run this every Monday at 9am"
- Add **multi-agent orchestration** — a supervisor agent that spawns specialist sub-agents (email agent, finance agent) and merges their results
- Build a proper **audit dashboard** with task history, replay, and rollback

---

## 🚀 Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium

cp .env.example .env
# Add your GROQ_API_KEY to .env

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### Production (Render / Railway / Heroku)

| Field | Value |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT` |

---

## 🔧 How to Add a New Tool

1. Create `backend/tools/my_tool.py` inheriting `BaseTool`
2. Implement `name`, `description`, `parameters`, and `execute()`
3. Register it in `backend/api/routes.py` inside `create_tool_registry()`

```python
from tools.base import BaseTool, ToolResult

class MyNewTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_new_tool"

    @property
    def description(self) -> str:
        return "Describe what this tool does so the LLM knows when to call it."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "What this param does"}
            },
            "required": ["param1"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        result = do_something(kwargs["param1"])
        return ToolResult(success=True, data={"result": result})
```
