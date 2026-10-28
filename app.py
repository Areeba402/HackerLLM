"""
HackerLLM: An AI-powered cybersecurity agent that turns natural language into real security tool execution.
FastAPI Backend Gateway
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

from utils.security_sanitizer import sanitize_and_validate_target
from tools.universal_runner import run_tool
from providers.manager import LLMManager

app = FastAPI(
    title="HackerLLM",
    description="An AI-powered cybersecurity agent that turns natural language into real security tool execution.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_manager = LLMManager()

class ToolExecutionRequest(BaseModel):
    target: str = ""
    options: str = ""
    job_id: str = Field(default="default", alias="jobId")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.2

@app.on_event("startup")
async def startup_event():
    port = os.getenv("PORT", "5000")
    print(f"\n==================================================", file=sys.stderr)
    print(f"  [+] HackerLLM: AI Cybersecurity Agent Ready", file=sys.stderr)
    print(f"  [+] Web UI:   http://localhost:{port}", file=sys.stderr)
    print(f"  [+] API Docs: http://localhost:{port}/docs", file=sys.stderr)
    print(f"==================================================\n", file=sys.stderr)

@app.get("/ping")
def ping():
    return {"status": "online", "app": "HackerLLM", "version": "1.0.0"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "HackerLLM AI Agent",
        "endpoints": ["/", "/ping", "/health", "/v1/chat/completions", "/run/{tool_name}"]
    }

@app.post("/v1/chat/completions")
async def chat_proxy(request: Request):
    """
    Proxies user chat messages to the configured LLM provider (BYOAPI).
    Supports: Ollama, Google Gemini, Groq, OpenAI, and compatible endpoints.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages = body.get("messages", [])
    model = body.get("model")
    temperature = body.get("temperature", 0.2)

    auth_header = request.headers.get("Authorization", "")
    client_key = auth_header.replace("Bearer ", "").strip() if auth_header else None

    try:
        response = await llm_manager.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            client_api_key=client_key
        )
        return response
    except Exception as e:
        print(f"[!] [CHAT ERROR] {str(e)}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run/{tool_name}")
def run_tool_endpoint(tool_name: str, req: ToolExecutionRequest):
    """
    Executes a security tool via the Universal Runner inside Kali Linux.
    Sanitizes target and passes options safely.
    """
    clean_target = ""
    if req.target and req.target.strip():
        is_valid, sanitized_target, err_msg = sanitize_and_validate_target(req.target)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Target Security Violation: {err_msg}")
        clean_target = sanitized_target

    result = run_tool(
        tool_name=tool_name,
        target=clean_target,
        options=req.options,
        job_id=req.job_id
    )
    return result

# Serve the Single-Page Web Interface
frontend_file = Path(__file__).parent / "frontend" / "index.html"

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    if frontend_file.exists():
        return HTMLResponse(content=frontend_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>HackerLLM Backend Online. Frontend file not found.</h1>", status_code=404)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
