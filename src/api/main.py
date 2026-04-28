import json
import os
import secrets
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from src.rag import embed_query, search_documents, build_context, format_sources, stream_answer

app = FastAPI(title="IAM-KB API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

security = HTTPBasic()

_API_USERNAME = os.environ.get("API_USERNAME", "")
_API_PASSWORD = os.environ.get("API_PASSWORD", "")


def verify(credentials: HTTPBasicCredentials = Depends(security)):
    if not _API_USERNAME or not _API_PASSWORD:
        raise HTTPException(status_code=500, detail="Auth not configured")
    ok = secrets.compare_digest(credentials.username.encode(), _API_USERNAME.encode()) and \
         secrets.compare_digest(credentials.password.encode(), _API_PASSWORD.encode())
    if not ok:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


class QueryRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {"status": "ok", "service": "IAM-KB API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/auth")
def auth_check(_: HTTPBasicCredentials = Depends(verify)):
    return {"status": "ok"}


@app.post("/query")
def query(req: QueryRequest, _: HTTPBasicCredentials = Depends(verify)):
    """
    Stream a RAG answer as Server-Sent Events (SSE).

    Event types:
      {"type": "searching"}
      {"type": "token",   "content": "..."}
      {"type": "sources", "content": [...]}
      {"type": "done"}
      {"type": "error",   "content": "..."}
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    def generate():
        try:
            yield f"data: {json.dumps({'type': 'searching'})}\n\n"

            embedding = embed_query(req.question)
            docs = search_documents(embedding)

            if not docs:
                yield f"data: {json.dumps({'type': 'error', 'content': 'No relevant documents found. Try rephrasing your question.'})}\n\n"
                return

            context = build_context(docs)

            for token in stream_answer(req.question, context):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            sources = format_sources(docs)
            yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
