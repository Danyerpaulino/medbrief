# MedBrief Implementation Plan

## Context
A health system strategy team needs a tool that generates structured medical condition briefings (standard of care, emerging treatments, key players) to present to stakeholders. This is a demo-grade application deployed on Railway (backend) + Vercel (frontend) to showcase business value.

## Project Structure

```
medbrief/
├── backend/                  # FastAPI backend + venv
│   ├── venv/                 # Python virtual environment
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Settings via pydantic-settings
│   │   ├── database.py       # SQLAlchemy engine/session setup
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── briefings.py  # Briefing CRUD + polling endpoints
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py      # LangGraph workflow definition
│   │   │   ├── state.py      # Agent state schema
│   │   │   ├── nodes.py      # Graph node functions
│   │   │   └── tools.py      # PubMed + ClinicalTrials.gov tools
│   │   └── worker.py         # Background job runner
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py             # pytest fixtures and fake DB session
│   │   ├── test_health.py          # health check coverage
│   │   ├── test_briefings_api.py   # briefing CRUD API behavior
│   │   ├── test_agent_tools.py     # PubMed/ClinicalTrials parsing
│   │   ├── test_worker.py          # background job success/failure paths
│   │   └── test_schemas.py         # response schema validation
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # Next.js (scaffolded by user)
├── .gitignore
└── README.md
```

## Phase 1: Backend Scaffolding

### 1.1 Virtual Environment & Dependencies

```bash
cd backend/
python -m venv venv
source venv/bin/activate
```

**requirements.txt:**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0
alembic>=1.13
psycopg2-binary>=2.9
pydantic>=2.0
pydantic-settings>=2.0
langgraph>=0.2
langchain-openai>=0.2
langchain-community>=0.3
httpx>=0.27
python-dotenv>=1.0
pytest>=8.0
```

### 1.2 Database Models (`app/models.py`)

```python
class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(UUID, primary_key=True, default=uuid4)
    condition = Column(String, nullable=False)          # e.g. "Type 2 Diabetes"
    status = Column(String, default="pending")          # pending | processing | completed | failed
    result = Column(JSON, nullable=True)                # structured briefing output
    error = Column(Text, nullable=True)                 # error message if failed
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
```

Single table is sufficient for the demo. Status enum: `pending → processing → completed | failed`.

### 1.3 Pydantic Schemas (`app/schemas.py`)

```python
class BriefingCreate(BaseModel):
    condition: str  # "Type 2 Diabetes", "Non-Small Cell Lung Cancer", etc.

class BriefingResponse(BaseModel):
    id: UUID
    condition: str
    status: str
    result: BriefingResult | None
    created_at: datetime
    completed_at: datetime | None

class BriefingResult(BaseModel):
    standard_of_care: list[Section]
    emerging_treatments: list[Treatment]
    key_players: list[Player]
    summary: str

class Section(BaseModel):
    title: str
    content: str
    references: list[str]

class Treatment(BaseModel):
    name: str
    phase: str              # "Phase 1", "Phase 2", "Phase 3", "Approved"
    company: str
    mechanism: str
    description: str
    trial_id: str | None

class Player(BaseModel):
    name: str
    type: str               # "pharma", "biotech", "academic", "hospital_system"
    role: str               # what they're doing in this space
```

### 1.4 API Endpoints (`app/routes/briefings.py`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/briefings` | Create a new briefing request, kicks off background job |
| GET | `/api/briefings/{id}` | Poll status + retrieve result when complete |
| GET | `/api/briefings` | List all briefings (most recent first) |
| DELETE | `/api/briefings/{id}` | Delete a briefing |

### 1.5 Alembic Setup

```bash
alembic init alembic
# Configure alembic.ini to read DATABASE_URL from env
# Create initial migration for briefings table
```

## Phase 2: LangGraph Agent

### 2.1 Agent State (`app/agent/state.py`)

```python
class AgentState(TypedDict):
    condition: str
    pubmed_results: list[dict]
    clinical_trials: list[dict]
    standard_of_care: list[dict]
    emerging_treatments: list[dict]
    key_players: list[dict]
    summary: str
```

### 2.2 Graph Nodes (`app/agent/nodes.py`)

The workflow is a **linear pipeline** (no cycles needed for v1):

```
START → research_pubmed → research_trials → analyze_standard_of_care → analyze_emerging → identify_players → synthesize → END
```

**Nodes:**
1. **research_pubmed** — Calls PubMed E-utilities API to fetch recent review articles and guidelines for the condition
2. **research_trials** — Calls ClinicalTrials.gov API to fetch active/recruiting trials for the condition
3. **analyze_standard_of_care** — GPT-4 synthesizes PubMed results into structured standard-of-care sections
4. **analyze_emerging** — GPT-4 analyzes clinical trials data to identify emerging treatments
5. **identify_players** — GPT-4 extracts key companies, institutions, and academic centers from all gathered data
6. **synthesize** — GPT-4 generates executive summary tying it all together

### 2.3 Tools (`app/agent/tools.py`)

```python
async def search_pubmed(query: str, max_results: int = 20) -> list[dict]:
    """Search PubMed via E-utilities API (esearch + efetch)."""
    # Uses httpx to call: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
    # Returns: title, abstract, authors, journal, pub_date, pmid

async def search_clinical_trials(condition: str, status: list[str] = None) -> list[dict]:
    """Search ClinicalTrials.gov v2 API."""
    # Uses httpx to call: https://clinicaltrials.gov/api/v2/studies
    # Returns: trial title, phase, status, sponsor, interventions, nct_id
```

### 2.4 Graph Assembly (`app/agent/graph.py`)

```python
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)
workflow.add_node("research_pubmed", research_pubmed_node)
workflow.add_node("research_trials", research_trials_node)
workflow.add_node("analyze_standard_of_care", analyze_soc_node)
workflow.add_node("analyze_emerging", analyze_emerging_node)
workflow.add_node("identify_players", identify_players_node)
workflow.add_node("synthesize", synthesize_node)

workflow.set_entry_point("research_pubmed")
workflow.add_edge("research_pubmed", "research_trials")
workflow.add_edge("research_trials", "analyze_standard_of_care")
workflow.add_edge("analyze_standard_of_care", "analyze_emerging")
workflow.add_edge("analyze_emerging", "identify_players")
workflow.add_edge("identify_players", "synthesize")
workflow.set_finish_point("synthesize")

graph = workflow.compile()
```

## Phase 3: Background Job Execution

### 3.1 Approach: FastAPI `BackgroundTasks` with in-process execution

For the demo, we'll use FastAPI's `BackgroundTasks` to run the LangGraph agent after the create response is returned. No external task queue (Celery/Redis) needed for a demo.

```python
# In the POST /api/briefings endpoint:
briefing = Briefing(condition=payload.condition, status="pending")
db.add(briefing)
db.commit()
background_tasks.add_task(run_briefing_agent, briefing.id)
return briefing
```

**`app/worker.py`:**
```python
async def run_briefing_agent(briefing_id: UUID):
    # 1. Update status to "processing"
    # 2. Run graph.ainvoke({"condition": condition})
    # 3. Parse result into BriefingResult schema
    # 4. Update briefing row with result, status="completed"
    # 5. On error: set status="failed", store error message
```

## Phase 4: Deployment Configuration

### 4.1 Dockerfile (backend/)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Environment Variables

```
DATABASE_URL=postgresql://...       # Railway Postgres addon provides this
OPENAI_API_KEY=sk-...               # OpenAI API key
FRONTEND_URL=https://medbrief.vercel.app  # For CORS
```

### 4.3 Railway Setup
- Add PostgreSQL plugin → auto-injects `DATABASE_URL`
- Set `OPENAI_API_KEY` and `FRONTEND_URL` as env vars
- Health check: `GET /health` endpoint returns `{"status": "ok"}`
- Start command in Dockerfile handles the rest

### 4.4 CORS (`app/main.py`)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Phase 5: Frontend API Contract

The Next.js frontend (built by user) will consume these endpoints:

```typescript
// POST /api/briefings
// Body: { "condition": "Type 2 Diabetes" }
// Response: { "id": "uuid", "condition": "...", "status": "pending", ... }

// GET /api/briefings/{id}  (poll every 3-5 seconds)
// Response: { "id": "uuid", "status": "processing|completed|failed", "result": {...} }

// GET /api/briefings
// Response: [{ "id": "uuid", "condition": "...", "status": "...", ... }, ...]
```

## Phase 6: Automated Test Suite

Use `pytest` for backend regression coverage. Tests should run locally without a real Postgres database, OpenAI call, PubMed call, or ClinicalTrials.gov call. Mock those boundaries so failures point to application behavior rather than external services.

### 6.1 Test Dependencies

Add pytest to `backend/requirements.txt`:

```
pytest>=8.0
```

### 6.2 Pytest Configuration (`backend/pytest.ini`)

```ini
[pytest]
testpaths = tests
pythonpath = .
```

### 6.3 Test Coverage

| File | Purpose |
|------|---------|
| `backend/tests/conftest.py` | Test environment variables and fake DB session fixtures |
| `backend/tests/test_health.py` | Verifies `/health` returns `{"status": "ok"}` |
| `backend/tests/test_briefings_api.py` | Verifies create/list/get/delete briefing endpoints and background job scheduling |
| `backend/tests/test_agent_tools.py` | Verifies PubMed XML parsing and ClinicalTrials.gov response mapping without network calls |
| `backend/tests/test_worker.py` | Verifies worker status transitions for completed and failed agent runs |
| `backend/tests/test_schemas.py` | Verifies nested briefing result response validation |

### 6.4 Local Test Command

```bash
cd backend
pytest
```

Run this before deployment commits and before pushing to GitHub/production.

## Git & GitHub Strategy

### Repository Setup

```bash
# From project root /medbrief
git init
gh repo create medbrief --private --source=. --remote=origin
```

**`.gitignore`** (committed first):
```
# Python
__pycache__/
*.py[cod]
*$py.class
backend/venv/
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Node (frontend)
frontend/node_modules/
frontend/.next/
frontend/out/

# Alembic
*.db
```

### Commit Strategy & Stopping Points

Each commit below represents a logical, self-contained unit of work. Commit at each of these points before moving on.

---

**Commit 1: `init: project structure and dependencies`**
- `.gitignore`
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/app/__init__.py`
- `backend/app/config.py`
- `IMPLEMENTATION_PLAN.md`

---

**Commit 2: `feat(db): add SQLAlchemy models and Alembic setup`**
- `backend/app/database.py`
- `backend/app/models.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/xxxx_initial_briefings_table.py`

---

**Commit 3: `feat(api): add briefing CRUD endpoints with Pydantic schemas`**
- `backend/app/schemas.py`
- `backend/app/routes/__init__.py`
- `backend/app/routes/briefings.py`
- `backend/app/main.py` (FastAPI app with CORS, router, health check)

---

**Commit 4: `feat(agent): add PubMed and ClinicalTrials.gov research tools`**
- `backend/app/agent/__init__.py`
- `backend/app/agent/tools.py`

---

**Commit 5: `feat(agent): add LangGraph workflow for briefing generation`**
- `backend/app/agent/state.py`
- `backend/app/agent/nodes.py`
- `backend/app/agent/graph.py`

---

**Commit 6: `feat(worker): wire background job execution to API`**
- `backend/app/worker.py`
- Update `backend/app/routes/briefings.py` (replace mock with real agent call)

---

**Commit 7: `test(backend): add pytest coverage for API, agent tools, and worker`**
- `backend/requirements.txt` (add `pytest`)
- `backend/pytest.ini`
- `backend/tests/conftest.py`
- `backend/tests/test_health.py`
- `backend/tests/test_briefings_api.py`
- `backend/tests/test_agent_tools.py`
- `backend/tests/test_worker.py`
- `backend/tests/test_schemas.py`

---

**Commit 8: `feat(deploy): add Dockerfile and Railway configuration`**
- `backend/Dockerfile`
- `backend/railway.toml` (if needed)
- `Procfile` or Railway start command config

---

**Commit 9: `docs: add README with setup and deployment instructions`**
- `README.md`

---

### Commit Message Convention

Format: `<type>(<scope>): <description>`

Types:
- `init` — project initialization
- `feat` — new feature or capability
- `fix` — bug fix
- `refactor` — code restructuring without behavior change
- `docs` — documentation only
- `chore` — build/config changes

Scope (optional): `db`, `api`, `agent`, `worker`, `deploy`, `frontend`

## Railway Deployment Details

### How It Works
Railway deploys directly from GitHub. Every push to `main` triggers a new deployment automatically.

### Setup Steps

1. **Create Railway project** at [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub Repo"
   - Select the `medbrief` private repo
   - Railway will detect the Dockerfile in `/backend`

2. **Add PostgreSQL**
   - In the Railway project dashboard, click "New" → "Database" → "Add PostgreSQL"
   - Railway auto-injects `DATABASE_URL` into your service's environment

3. **Configure the backend service**
   - Set the **Root Directory** to `/backend` (so it builds from the backend Dockerfile)
   - Add environment variables:
     ```
     OPENAI_API_KEY=sk-...
     FRONTEND_URL=https://your-app.vercel.app
     ```
   - `DATABASE_URL` is auto-provided by the Postgres plugin — no manual entry needed

4. **Health Check**
   - Set health check path to `/health`
   - Railway will wait for a 200 response before routing traffic

5. **Run Migrations on Deploy**
   - The Dockerfile CMD or a Railway deploy hook should run migrations before starting the server:
     ```dockerfile
     CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - Railway provides `$PORT` — you must bind to it (not hardcode 8000)

### Railway-Specific Configuration

**`backend/Dockerfile`** (production-ready):
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Railway provides $PORT dynamically
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**`backend/railway.toml`** (optional, for explicit config):
```toml
[build]
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

### Environment Variables Summary

| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | Railway (auto) | PostgreSQL connection string from Railway Postgres plugin |
| `OPENAI_API_KEY` | Manual | OpenAI API key for GPT-4 calls |
| `FRONTEND_URL` | Manual | Vercel deployment URL for CORS allowlist |
| `PORT` | Railway (auto) | Port Railway assigns for the service to bind to |

### Vercel Frontend Deployment

1. Connect the same GitHub repo to Vercel
2. Set the **Root Directory** to `/frontend`
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
   ```
4. Vercel auto-detects Next.js and deploys on push to `main`

### Deployment Flow (After Initial Setup)

```
git push origin main
    ├── Railway detects push → builds backend Dockerfile → runs migrations → deploys
    └── Vercel detects push → builds Next.js frontend → deploys
```

Both platforms deploy from the same repo, each watching its own root directory.

## Build Order (Revised)

1. **Project init** — `.gitignore`, requirements, config, empty structure → **Commit 1**
2. **Database layer** — models, alembic, initial migration → **Commit 2**
3. **API routes** — schemas, endpoints, FastAPI app → **Commit 3**
4. **Agent tools** — PubMed + ClinicalTrials.gov integrations → **Commit 4**
5. **LangGraph workflow** — state, nodes, graph assembly → **Commit 5**
6. **Background worker** — wire agent to API endpoints → **Commit 6**
7. **Automated tests** — pytest config and backend coverage → **Commit 7**
8. **Deployment config** — Dockerfile, railway.toml, PORT binding → **Commit 8**
9. **Documentation** — README with setup/deploy instructions → **Commit 9**
10. **Run tests locally** — `cd backend && pytest`
11. **Push to GitHub** → Railway + Vercel auto-deploy
12. **Integration testing** — end-to-end verification on deployed infra

## Verification

1. **Automated backend tests**: `cd backend && pytest`
2. **Local API**: `uvicorn app.main:app --reload` — POST a briefing, poll until complete
3. **Railway**: Push to GitHub, confirm health check passes at `/health`
4. **Database**: Verify Alembic migration runs on deploy (check Railway deploy logs)
5. **CORS**: Hit the Railway backend from `localhost:3000` (frontend dev) — no CORS errors
6. **End-to-end**: Frontend submits condition → backend processes → frontend displays briefing
