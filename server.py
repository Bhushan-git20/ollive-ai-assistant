from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Internal modules
from memory.sqlite_memory import init_db, save_message, get_history, clear_history
from observability.logger import init_logs_db, log_request, get_stats
from guardrails.safety_filter import check_input, check_output
from tools.tool_router import route_tool

# Initialize databases
init_db()
init_logs_db()

app = FastAPI(title="Ollive AI Assistant API")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    model: str
    message: str

class CompareRequest(BaseModel):
    session_id: str
    message: str

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/history/{session_id}")
def get_chat_history(session_id: str, model: str):
    history = get_history(session_id, model)
    return {"history": history}

@app.delete("/api/history/{session_id}")
def delete_chat_history(session_id: str, model: str):
    clear_history(session_id, model)
    return {"status": "success"}

@app.get("/api/stats")
def get_observability_stats():
    stats = get_stats()
    return {"stats": stats}

@app.post("/api/chat")
def chat(request: ChatRequest):
    user_input = request.message
    session_id = request.session_id
    model_choice = request.model

    # Guardrail check on input
    is_safe, reason = check_input(user_input)
    if not is_safe:
        log_request(session_id, model_choice, len(user_input.split()), 0, 0.0, guardrail_triggered=True)
        return {
            "role": "assistant",
            "content": f"🚫 {reason}",
            "latency": 0,
            "tokens": 0,
            "tool_used": None,
            "guardrail_triggered": True
        }

    save_message(session_id, model_choice, "user", user_input)

    # Tool routing
    tool_name, tool_result = route_tool(user_input)

    # Load model and generate
    fresh_history = get_history(session_id, model_choice)
    try:
        if model_choice == "gemini-flash-lite-latest":
            from models.gemini_model import generate
        else:
            from models.qwen_model import generate

        response, p_tok, c_tok, latency = generate(
            user_input, fresh_history, tool_context=tool_result or ""
        )
    except Exception as e:
        response = f"⚠️ Model error: {e}"
        p_tok, c_tok, latency = 0, 0, 0.0

    # Output guardrail
    out_safe, out_reason = check_output(response)
    if not out_safe:
        response = out_reason
        log_request(session_id, model_choice, p_tok, c_tok, latency, guardrail_triggered=True, tool_used=tool_name)
    else:
        log_request(session_id, model_choice, p_tok, c_tok, latency, tool_used=tool_name)

    save_message(session_id, model_choice, "assistant", response)

    return {
        "role": "assistant",
        "content": response,
        "latency": latency,
        "tokens": c_tok,
        "tool_used": f"{tool_name} -> {tool_result}" if tool_result else None,
        "guardrail_triggered": not out_safe
    }

@app.post("/api/compare")
def compare(request: CompareRequest):
    user_input = request.message
    session_id = request.session_id

    is_safe, reason = check_input(user_input)
    if not is_safe:
        return {"error": reason}

    tool_name, tool_result = route_tool(user_input)

    # Gemini
    try:
        from models.gemini_model import generate as gemini_gen
        g_resp, g_pt, g_ct, g_lat = gemini_gen(user_input, [], tool_context=tool_result or "")
        g_safe, g_reason = check_output(g_resp)
        g_resp = g_resp if g_safe else g_reason
    except Exception as e:
        g_resp, g_pt, g_ct, g_lat = f"Error: {e}", 0, 0, 0

    # Qwen
    try:
        from models.qwen_model import generate as qwen_gen
        q_resp, q_pt, q_ct, q_lat = qwen_gen(user_input, [], tool_context=tool_result or "")
        q_safe, q_reason = check_output(q_resp)
        q_resp = q_resp if q_safe else q_reason
    except Exception as e:
        q_resp, q_pt, q_ct, q_lat = f"Error: {e}", 0, 0, 0

    return {
        "tool_used": f"{tool_name} -> {tool_result}" if tool_result else None,
        "gemini": {
            "content": g_resp,
            "latency": g_lat,
            "tokens": g_ct
        },
        "qwen": {
            "content": q_resp,
            "latency": q_lat,
            "tokens": q_ct
        }
    }
