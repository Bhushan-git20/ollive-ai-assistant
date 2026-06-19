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

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    model: str
    message: str
    system_prompt: Optional[str] = None

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
    system_prompt = request.system_prompt

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
            user_input, fresh_history, tool_context=tool_result or "", system_prompt=system_prompt
        )
        # Save user message only if generation succeeds
        save_message(session_id, model_choice, "user", user_input)
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

from fastapi.responses import StreamingResponse
import json
import subprocess
import os
import sys

@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    user_input = request.message
    session_id = request.session_id
    model_choice = request.model
    system_prompt = request.system_prompt

    is_safe, reason = check_input(user_input)
    if not is_safe:
        def err_stream():
            yield f"data: {json.dumps({'content': f'🚫 {reason}', 'tool_used': None})}\n\n"
        return StreamingResponse(err_stream(), media_type="text/event-stream")

    tool_name, tool_result = route_tool(user_input)
    fresh_history = get_history(session_id, model_choice)

    def generate_responses():
        tool_str = f"{tool_name} -> {tool_result}" if tool_result else None
        user_msg_saved = False
        
        try:
            if model_choice == "gemini-flash-lite-latest" or "gemini" in model_choice:
                from models.gemini_model import generate_stream
                stream = generate_stream(user_input, fresh_history, tool_context=tool_result or "", system_prompt=system_prompt)
            else:
                from models.qwen_model import generate_stream
                stream = generate_stream(user_input, fresh_history, tool_context=tool_result or "", system_prompt=system_prompt)

            full_response = ""
            for chunk in stream:
                full_response += chunk
                payload = {
                    "content": chunk,
                    "tool_used": tool_str,
                    "is_done": False
                }
                yield f"data: {json.dumps(payload)}\n\n"
            
            # Post generation check
            out_safe, out_reason = check_output(full_response)
            if not out_safe:
                yield f"data: {json.dumps({'content': f'\\n\\n🚫 {out_reason}', 'is_done': False})}\n\n"
            
            # Save BOTH user and assistant messages at the end to prevent corruption on crash
            save_message(session_id, model_choice, "user", user_input)
            msg_id = save_message(session_id, model_choice, "assistant", full_response)
            log_request(session_id, model_choice, len(user_input.split()), len(full_response.split()), 0.0, tool_used=tool_name)

            yield f"data: {json.dumps({'content': '', 'is_done': True, 'message_id': msg_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_responses(), media_type="text/event-stream")

class RateRequest(BaseModel):
    rating: int

@app.post("/api/rate/{message_id}")
def rate(message_id: int, req: RateRequest):
    from memory.sqlite_memory import rate_message
    rate_message(message_id, req.rating)
    return {"status": "success"}

# --- EVAL RUNNER ---
import threading
from eval.eval_runner import main as run_eval_main

eval_thread = None

def run_eval_background(log_path):
    import sys, io
    with open(log_path, "w") as f:
        old_stdout = sys.stdout
        sys.stdout = f
        try:
            run_eval_main()
        except Exception as e:
            f.write(f"\nERROR: {e}\n")
            import traceback
            traceback.print_exc(file=f)
        finally:
            sys.stdout = old_stdout

@app.post("/api/eval/run")
def run_eval():
    global eval_thread
    if eval_thread and eval_thread.is_alive():
        return {"status": "already_running"}
    
    log_path = os.path.join(os.path.dirname(__file__), "eval", "eval_logs.txt")
    eval_thread = threading.Thread(target=run_eval_background, args=(log_path,))
    eval_thread.start()
    return {"status": "started"}

@app.get("/api/eval/logs")
def get_eval_logs():
    global eval_thread
    log_path = os.path.join(os.path.dirname(__file__), "eval", "eval_logs.txt")
    logs = ""
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logs = f.read()
    
    is_running = eval_thread is not None and eval_thread.is_alive()
    return {"logs": logs, "is_running": is_running}

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

from fastapi.staticfiles import StaticFiles

frontend_out = os.path.join(os.path.dirname(__file__), "frontend", "out")
if os.path.exists(frontend_out):
    app.mount("/", StaticFiles(directory=frontend_out, html=True), name="frontend")
