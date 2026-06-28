# Marketing AI Agent — Backend

An autonomous AI agent that analyzes YouTube channel performance data and generates actionable marketing insights. Demonstrates the intersection of **marketing data pipelines**, **LLM tool calling**, and **agentic AI systems**.

---

## Overview

The agent connects to the YouTube Data API, stores channel and video metrics in PostgreSQL, and exposes a conversational REST API powered by **Groq (Llama 3.3 70B)** and **LangChain**. Users can ask natural language questions and the agent autonomously decides which tools to call, fetches real data, and returns structured insights with recommendations.

**Example questions:**
- *"What channels are being tracked?"*
- *"Show me the top 5 videos for [channel]"*
- *"Compare [channel A] vs [channel B]"*
- *"What is the overall performance of [channel]?"*

---

## Architecture

```
YouTube Data API v3
        │
        ▼
  ETL Pipeline (Python)          ← triggered via API endpoint
        │
        ▼
  PostgreSQL (Docker)            ← channel_snapshots + video_stats
        │
        ▼
  LangChain Agent (Groq)         ← tool calling · reasoning · synthesis
        │
        ▼
  FastAPI Backend                ← REST API
```

**CI/CD:** GitHub Actions → SSH → Docker Compose on Cloud VM

---

## Tech Stack

| Layer | Technology |
|---|---|
| ETL & Backend | Python, FastAPI, SQLAlchemy |
| AI Agent | LangChain, Groq (Llama 3.3 70B) |
| Data Source | YouTube Data API v3 |
| Database | PostgreSQL 15 |
| Infrastructure | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

## Agent Tools

| Tool | Description |
|---|---|
| `list_tracked_channels` | List all monitored YouTube channels |
| `get_channel_stats` | Get latest subscriber count, views, and video count |
| `get_top_videos` | Get top performing videos by view count |
| `compare_channels` | Side-by-side benchmark of two channels |

---

## Project Structure

```
marketing-ai-agent/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD — deploy on push to main
├── agent/
│   ├── agent.py                # LangChain AgentExecutor with Groq
│   └── tools.py                # StructuredTools with Pydantic schemas
├── api/
│   └── main.py                 # FastAPI — /ask and /etl/run endpoints
├── db/
│   └── models.py               # SQLAlchemy models + init_db()
├── etl/
│   └── youtube_fetcher.py      # YouTube Data API → PostgreSQL ETL
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- YouTube Data API v3 key — [Google Cloud Console](https://console.cloud.google.com)
- Groq API key — free at [console.groq.com](https://console.groq.com)

### Local Development

```bash
# 1. Clone the repo
git clone https://github.com/ferdianmaulana/marketing-ai-agent.git
cd marketing-ai-agent

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Fill in your values — see .env.example for reference

# 5. Start the database
docker compose up -d marketing-db

# 6. Run the API
uvicorn api.main:app --reload --port 8001
```

Open `http://localhost:8001/docs` for the interactive Swagger UI.

### Run with Docker

```bash
# Build and start all services
docker compose up -d --build

# Trigger ETL to populate data
curl -X POST http://localhost:8001/etl/run
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/ask` | Ask the AI agent a question |
| `POST` | `/etl/run` | Trigger YouTube data fetch |

### Example

```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What channels are being tracked?"}'
```

```json
{
  "answer": "Currently tracking 2 channels...",
  "tools_used": ["list_tracked_channels"]
}
```

---

## Relevance to Production

| This project | Production equivalent |
|---|---|
| PostgreSQL (single VM) | BigQuery + Cloud Storage |
| YouTube Data API | Meta Ads API, Google Ads API, TikTok API |
| Groq (Llama 3.3) | Gemini, Claude, or OpenAI |
| Manual ETL trigger | Apache Airflow DAG on schedule |
| Single VM deployment | Kubernetes / Cloud Run |
