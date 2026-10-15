from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from agent.agent import run_agent
from etl.youtube_fetcher import run_etl
from db.models import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Marketing AI Agent",
    description="AI-powered YouTube channel analytics agent using Groq (Llama) + LangChain",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this when you add a real frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str        # "user" or "assistant"
    content: str


class AskRequest(BaseModel):
    question: str
    chat_history: Optional[list[ChatMessage]] = []


class AskResponse(BaseModel):
    answer: str
    tools_used: list[str]


class ETLResponse(BaseModel):
    status: str
    message: str


# ── Startup ────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Ready.")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "Marketing AI Agent",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in (request.chat_history or [])
        ]
        result = run_agent(request.question, chat_history=history)
        return AskResponse(
            answer=result["answer"],
            tools_used=result.get("tools_used", []),
        )
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.post("/etl/run", response_model=ETLResponse)
def trigger_etl(max_results: int = 10):
    try:
        run_etl(max_results=max_results)
        return ETLResponse(status="success", message="ETL completed successfully.")
    except Exception as e:
        logger.error(f"ETL error: {e}")
        raise HTTPException(status_code=500, detail=f"ETL error: {str(e)}")
