# MedBrief

A medical condition briefing tool that generates structured reports covering standard of care, emerging treatments, and key players in a therapeutic area.

## Architecture

- **Backend**: FastAPI + LangGraph agent (Python 3.12)
- **Frontend**: Next.js (React 19, Tailwind CSS 4)
- **Database**: PostgreSQL (managed via Alembic migrations)
- **AI**: GPT-4o via OpenAI API
- **Data Sources**: PubMed E-utilities, ClinicalTrials.gov v2 API

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and OPENAI_API_KEY

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Health check: `GET /health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/briefings` | Create a new briefing (kicks off background processing) |
| GET | `/api/briefings/{id}` | Get briefing status and result |
| GET | `/api/briefings` | List all briefings |
| DELETE | `/api/briefings/{id}` | Delete a briefing |
| GET | `/health` | Health check |

### Example Usage

```bash
# Create a briefing
curl -X POST http://localhost:8000/api/briefings \
  -H "Content-Type: application/json" \
  -d '{"condition": "Type 2 Diabetes"}'

# Poll for result (use the id from the response above)
curl http://localhost:8000/api/briefings/{id}
```

## Deployment

### Railway (Backend)

1. Create a Railway project and connect the GitHub repo
2. Set root directory to `/backend`
3. Add PostgreSQL plugin (auto-injects `DATABASE_URL`)
4. Set environment variables: `OPENAI_API_KEY`, `FRONTEND_URL`
5. Railway auto-deploys on push to `main`

### Vercel (Frontend)

1. Connect the same repo to Vercel
2. Set root directory to `/frontend`
3. Set `NEXT_PUBLIC_API_URL` to your Railway backend URL
4. Vercel auto-deploys on push to `main`

## Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | Railway (auto) | PostgreSQL connection string |
| `OPENAI_API_KEY` | Manual | OpenAI API key for GPT-4o |
| `FRONTEND_URL` | Manual | Frontend URL for CORS |
| `PORT` | Railway (auto) | Port to bind (defaults to 8000) |
