<div align="center">
  <h1>CodeAgent</h1>
  <p>
    <strong>Autonomous AI coding agent that reads, fixes, and tests code — with live streaming</strong>
  </p>
  <p>
    <code>POST /tasks</code> &nbsp;→&nbsp; <code>Agent analyzes repo</code> &nbsp;→&nbsp; <code>✓ Tests pass</code>
  </p>
  <p>
    <a href="https://github.com/ishyverma/ai-coding-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python"></a>
    <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
    <a href="https://langchain-ai.github.io/langgraph/"><img src="https://img.shields.io/badge/LangGraph-0.2-1B3A4B" alt="LangGraph"></a>
  </p>
</div>

---

**CodeAgent** is an autonomous coding agent that clones a repository, analyzes a task, writes the fix, runs the tests, and retries if anything fails — all streamed live to a web dashboard. Give it a broken repo and a task description, and it figures out the rest.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- A [Groq API key](https://console.groq.com) (free tier, no credit card)

### Backend

```bash
# Clone the repo
git clone https://github.com/ishyverma/ai-coding-agent.git
cd ai-coding-agent

# Set up Python environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the dashboard.

---

## Features

### Autonomous Agent Loop
- **Clone** — pulls the target repository into an isolated work directory
- **Inspect** — discovers files, test files, and project structure automatically
- **Analyze** — LLM reads the codebase and identifies the problem
- **Modify** — generates structured code changes (file path + full content)
- **Test** — runs the project's test suite (pytest, go test, npm test, cargo test)
- **Recover** — if tests fail, reads the error output and tries again (up to 3 attempts)

### Real-Time Streaming
- **WebSocket log stream** — every agent step pushed to the frontend as it happens
- **Step-level granularity** — see `setup → inspect → analyze → modify → run_tests` in real time
- **Status badges** — task and run status updated live (pending → running → done | failed)

### Eval Framework
- **5 pre-built broken repos** — off-by-one, wrong variable, wrong operator, missing return, missing function
- **Automated scoring** — pass rate, avg attempts, avg tokens, avg duration
- **JSON results** — programmatic access to eval outcomes
- **Benchmark showpiece** — demonstrate the agent's capabilities quantitatively

### API-First Design
- **REST API** at `/api/v1/` with auto-generated docs at `/docs`
- **Pydantic validation** — request/response schemas enforced automatically
- **Background execution** — POST a task, get a `run_id`, stream logs via WebSocket
- **Health check** — `/health` endpoint for Railway/load balancer monitoring

### Multi-Language Support
- **Python** — `pytest` test runner
- **Go** — `go test ./...`
- **Node.js / TypeScript** — `npm test`
- **Rust** — `cargo test`
- Auto-detected from project files

### Production Ready
- **PostgreSQL** in production (Railway), **SQLite** in development
- **Alembic** migrations for schema management
- **Docker** deployment with cache-busting for Railway
- **CORS** configured for frontend/backend separation
- **Non-root container** for security

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CodeAgent System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────┐    ┌───────────────────────────────┐  │
│   │   Next.js Frontend  │    │      FastAPI Backend           │  │
│   │                     │    │                               │  │
│   │  Task List          │    │  POST /api/v1/tasks           │  │
│   │  Task Form          │◄──►│  POST /api/v1/tasks/{id}/run  │  │
│   │  Live Log Viewer    │ WS │  WS   /api/v1/runs/{id}/stream│  │
│   │  Eval Dashboard     │    │  GET  /api/v1/evals           │  │
│   └─────────────────────┘    └──────────────┬────────────────┘  │
│                                              │                   │
│                                              ▼                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                    LangGraph Agent                        │  │
│   │                                                          │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐   │  │
│   │  │  Setup   │→ │ Inspect │→ │ Analyze │→ │  Modify  │   │  │
│   │  │  clone   │  │  files  │  │  LLM    │  │  LLM     │   │  │
│   │  │  repo    │  │  structure│ │  thinks │  │  writes  │   │  │
│   │  └─────────┘  └─────────┘  └─────────┘  └────┬─────┘   │  │
│   │                                                │         │  │
│   │                           ┌────────────────────┘         │  │
│   │                           ▼                              │  │
│   │                      ┌──────────┐                        │  │
│   │                      │Run Tests │                        │  │
│   │                      │pytest/etc│                        │  │
│   │                      └────┬─────┘                        │  │
│   │                           │                              │  │
│   │                    pass? ──┤── fail?                      │  │
│   │                    │      │      │                       │  │
│   │                    ▼      │      ▼                       │  │
│   │                  DONE     │   ┌──────────┐              │  │
│   │                           │   │ Recovery │              │  │
│   │                           │   │ retry?   │──→ Analyze   │  │
│   │                           │   └──────────┘   (loop)     │  │
│   └───────────────────────────┴──────────────────────────────┘  │
│                                              │                   │
│                                              ▼                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                    Storage                                │  │
│   │  SQLite / PostgreSQL                                     │  │
│   │  Tables: tasks, runs, run_logs, eval_results             │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
POST /api/v1/tasks  { repo_url, task_text }
  → Create task (status: pending)
  → POST /api/v1/tasks/{id}/run
    → Create run (status: running)
    → BackgroundTasks dispatches the agent:
      → Setup: clone repo to /tmp/agent-repos/
      → Inspect: list files, find tests, read source
      → Analyze: LLM reads code + task, produces analysis
      → Modify: LLM generates code changes, apply them
      → Run Tests: execute test command, capture output
      → If pass → status: done
      → If fail → Recovery: check retry limit
        → If retries left → loop back to Analyze with error context
        → If max attempts → status: failed
    → Each step writes a RunLog entry
    → WebSocket streams RunLog entries to frontend in real time
```

---

## API Reference

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tasks` | Create a new task (repo_url + task_text) |
| `GET` | `/api/v1/tasks` | List all tasks (newest first) |
| `GET` | `/api/v1/tasks/{id}` | Get a single task |
| `POST` | `/api/v1/tasks/{id}/run` | Trigger the agent on this task |

### Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/runs/{id}` | Get run details (status, attempts, tokens, duration) |
| `GET` | `/api/v1/runs/{id}/logs` | Get all log entries for a run |
| `WS` | `/api/v1/runs/{id}/stream` | WebSocket — live log streaming |

### Eval

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/evals/run` | Run the full eval suite |
| `GET` | `/api/v1/evals` | List all eval results |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (Railway monitoring) |

---

## Agent Tools

The agent has access to five tools during execution:

| Tool | Description |
|------|-------------|
| `list_files` | List all files in the repository (skips .git, node_modules, etc.) |
| `read_file` | Read file contents (100KB limit, directory traversal blocked) |
| `write_file` | Write or overwrite a file (creates parent directories) |
| `run_shell` | Execute shell commands with a 30s timeout |
| `run_tests` | Run pytest and parse pass/fail counts + failure details |

All file operations are sandboxed to the repository directory — the agent cannot escape to read system files.

---

## Eval Framework

Run the agent against 5 pre-built broken repositories:

| Eval Task | Bug Type | Description |
|-----------|----------|-------------|
| `fix_off_by_one` | Off-by-one error | List slicing boundary issue |
| `fix_wrong_variable` | Wrong variable | String method called on wrong object |
| `fix_wrong_operator` | Wrong operator | Comparison vs assignment operator |
| `add_missing_return` | Missing return | Function doesn't return a value |
| `add_missing_function` | Missing function | Called function doesn't exist |

### Running the Eval

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/evals/run

# View results
curl http://localhost:8000/api/v1/evals
```

### Example Output

```json
{
  "eval_name": "coding-agent-eval",
  "total_tasks": 5,
  "passed": 4,
  "failed": 1,
  "pass_rate": 0.80,
  "avg_attempts": 1.4,
  "avg_tokens": 3200,
  "avg_duration_s": 12.5
}
```

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Web framework with auto-docs, Pydantic validation, BackgroundTasks |
| **LangGraph** | Agent workflow as a state graph with conditional routing |
| **LangChain + Groq** | LLM tooling with Llama 3.3 70B via Groq (250+ tok/s) |
| **SQLAlchemy 2.0** | ORM with sync sessions (SQLite dev, PostgreSQL prod) |
| **Alembic** | Database schema migrations |
| **LangSmith** | Optional LLM call tracing and debugging |
| **GitPython** | Repository cloning |

### Frontend

| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework with App Router |
| **TypeScript** | Type safety |
| **Tailwind CSS + shadcn/ui** | Styling and accessible components |
| **TanStack Query** | Data fetching, caching, polling |
| **WebSocket** | Real-time log streaming from agent |

### Deployment

| Service | Purpose |
|---------|---------|
| **Railway** | Backend hosting with PostgreSQL (free $5/mo credit) |
| **Vercel** | Frontend hosting (free tier) |
| **GitHub Actions** | CI — runs ruff + pytest on every PR |

---

## Database Schema

```
tasks
  id          INTEGER  PRIMARY KEY
  repo_url    TEXT     NOT NULL
  task_text   TEXT     NOT NULL
  status      TEXT     NOT NULL  DEFAULT 'pending'
  created_at  DATETIME NOT NULL  DEFAULT now()

runs
  id          INTEGER  PRIMARY KEY
  task_id     INTEGER  REFERENCES tasks(id)
  status      TEXT     NOT NULL  DEFAULT 'running'
  attempts    INTEGER  NOT NULL  DEFAULT 0
  tokens_used INTEGER  NOT NULL  DEFAULT 0
  duration_s  FLOAT
  error_msg   TEXT
  created_at  DATETIME NOT NULL  DEFAULT now()
  completed_at DATETIME

run_logs
  id          INTEGER  PRIMARY KEY
  run_id      INTEGER  REFERENCES runs(id)
  step        TEXT     NOT NULL
  level       TEXT     NOT NULL  DEFAULT 'info'
  message     TEXT     NOT NULL
  created_at  DATETIME NOT NULL  DEFAULT now()

eval_results
  id              INTEGER  PRIMARY KEY
  eval_name       TEXT     NOT NULL
  total_tasks     INTEGER  NOT NULL
  passed          INTEGER  NOT NULL
  failed          INTEGER  NOT NULL
  pass_rate       FLOAT    NOT NULL
  avg_attempts    FLOAT    NOT NULL
  avg_tokens      FLOAT    NOT NULL
  avg_duration_s  FLOAT    NOT NULL
  run_at          DATETIME NOT NULL  DEFAULT now()
```

---

## Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- No CGO required

### Commands

```bash
make help             Show all available commands
make install          Install all dependencies (backend + frontend)
make test             Run all tests (backend + frontend build check)
make test-backend     Run backend unit tests only
make test-frontend    Run frontend build check only
make lint             Run ruff linter + format check
```

### Project Structure

```
ai-coding-agent/
├── backend/
│   ├── app/
│   │   ├── main.py             ← FastAPI app + lifespan
│   │   ├── config.py           ← pydantic-settings (reads .env)
│   │   ├── database.py         ← SQLAlchemy engine + session
│   │   ├── models.py           ← Task, Run, RunLog, EvalResult
│   │   ├── schemas.py          ← Pydantic request/response shapes
│   │   ├── crud.py             ← All database operations
│   │   ├── api/                ← REST endpoints
│   │   │   ├── tasks.py        ← CRUD + trigger agent
│   │   │   ├── runs.py         ← Run status + WebSocket stream
│   │   │   └── evals.py        ← Eval suite runner
│   │   ├── agent/              ← LangGraph agent
│   │   │   ├── graph.py        ← StateGraph assembly
│   │   │   ├── nodes.py        ← Agent step functions
│   │   │   ├── state.py        ← AgentState TypedDict
│   │   │   ├── tools.py        ← read_file, write_file, etc.
│   │   │   ├── llm.py          ← Groq LLM integration
│   │   │   ├── executor.py     ← Shell command runner
│   │   │   └── recovery.py     ← Retry decision logic
│   │   └── eval/
│   │       ├── runner.py       ← EvalRunner class
│   │       ├── scorer.py       ← Score computation
│   │       └── fixtures/       ← Broken repos for eval
│   ├── tests/                  ← pytest test suite
│   ├── alembic/                ← DB migrations
│   ├── Dockerfile
│   ├── railway.json
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx            ← Task list dashboard
│   │   ├── tasks/new/page.tsx  ← Create new task
│   │   └── tasks/[id]/page.tsx ← Task detail + live logs
│   ├── components/
│   │   ├── Dashboard.tsx       ← Overview stats
│   │   ├── LogViewer.tsx       ← WebSocket-powered log stream
│   │   └── EvalDashboard.tsx   ← Eval results display
│   ├── lib/
│   │   ├── api.ts              ← Typed API client
│   │   └── useRunStream.ts     ← WebSocket hook
│   └── package.json
│
├── Makefile
├── Dockerfile
├── railway.json
└── PHASE.md                    ← Complete build guide
```

---

## Environment Variables

### Required

| Variable | Description | Where to get |
|----------|-------------|--------------|
| `GROQ_API_KEY` | Groq API key for LLM inference | [console.groq.com](https://console.groq.com) (free) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGSMITH_TRACING` | `false` | Enable LLM call tracing |
| `LANGSMITH_API_KEY` | — | [smith.langchain.com](https://smith.langchain.com) (free) |
| `LANGSMITH_PROJECT` | `coding-agent` | LangSmith project name |
| `DATABASE_URL` | `sqlite:///./dev.db` | PostgreSQL URL for production |
| `APP_ENV` | `development` | `development` or `production` |
| `SECRET_KEY` | — | Random string for production |
| `AGENT_MAX_ATTEMPTS` | `3` | Max retry attempts per task |
| `AGENT_REPO_WORK_DIR` | `/tmp/agent-repos` | Where repos are cloned |

---

## Deployment

### Backend (Railway)

```bash
# Login and link
railway login
railway link

# Set environment variables
railway variables set GROQ_API_KEY="your_key_here"
railway variables set APP_ENV="production"
railway variables set SECRET_KEY="$(openssl rand -hex 32)"

# Add PostgreSQL
railway add --database postgresql

# Deploy
railway up
```

### Frontend (Vercel)

```bash
cd frontend
vercel --prod
```

Set `NEXT_PUBLIC_API_URL` to your Railway backend URL in Vercel dashboard.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built with <a href="https://fastapi.tiangolo.com">FastAPI</a>, <a href="https://langchain-ai.github.io/langgraph/">LangGraph</a>, <a href="https://groq.com">Groq</a>, and <a href="https://nextjs.org">Next.js</a></sub>
</div>
