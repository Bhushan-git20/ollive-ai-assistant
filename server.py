import hmac
import json
import os
import threading
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles

load_dotenv()

# Internal modules
from eval.eval_runner import EVAL_RESULTS_JSON_PATH, main as run_eval_main
from guardrails.safety_filter import check_input, check_output
from memory.sqlite_memory import (
    clear_history,
    count_history,
    get_history,
    init_db,
    rate_message,
    save_message,
)
from observability.logger import (
    count_eval_history,
    count_stats,
    get_eval_history,
    get_stats,
    init_logs_db,
    log_request,
    save_eval_run,
)
from schemas import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    CompareModelResult,
    CompareRequest,
    CompareResponse,
    ErrorResponse,
    EvalHistoryResponse,
    EvalLogsResponse,
    EvalRunOut,
    EvalRunTriggerResponse,
    HealthResponse,
    HistoryResponse,
    ModelStatsOut,
    RateRequest,
    RateResponse,
    RootResponse,
    StatsResponse,
    StatusResponse,
)
from tools.tool_router import route_tool

# Initialize databases
init_db()
init_logs_db()

COMMON_ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad request or guardrail violation"},
    422: {"model": ErrorResponse, "description": "Request validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
}

AUTH_ERROR_RESPONSES = {
    **COMMON_ERROR_RESPONSES,
    401: {"model": ErrorResponse, "description": "Missing API key"},
    403: {"model": ErrorResponse, "description": "Invalid API key"},
    503: {"model": ErrorResponse, "description": "API key not configured on server"},
}

app = FastAPI(
    title="Ollive AI Assistant API",
    version="1.0.0",
    description="Dual-model AI personal assistant comparing Gemini and Qwen with tools, guardrails, observability, and structured evaluation.",
)

# Configure CORS for frontend access
allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
env_origin = os.getenv("ALLOWED_ORIGIN")
if env_origin and env_origin not in allowed_origins:
    allowed_origins.append(env_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ---------------------------------------------------------------------------
# Consistent Error Handlers
# ---------------------------------------------------------------------------

def _error_payload(error: str, detail: str, status_code: int, request: Request) -> dict:
    return ErrorResponse(
        error=error,
        detail=detail,
        status_code=status_code,
        path=str(request.url.path),
    ).model_dump()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            error="http_error",
            detail=str(exc.detail),
            status_code=exc.status_code,
            request=request,
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        parts.append(f"{loc}: {msg}" if loc else msg)
    detail = "; ".join(parts) if parts else "Request validation failed."
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            error="validation_error",
            detail=detail,
            status_code=422,
            request=request,
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            error="internal_server_error",
            detail="An unexpected server error occurred.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request=request,
        ),
    )


# ---------------------------------------------------------------------------
# Auth & Model Resolution Helpers
# ---------------------------------------------------------------------------

def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Validate X-API-Key header against OLLIVE_API_KEY environment variable."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header.",
        )
    expected_key = os.getenv("OLLIVE_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server API key is not configured.",
        )
    if not hmac.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )
    return api_key


DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
DEFAULT_QWEN_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")


def _resolve_gemini_model_id(model_choice: str) -> str:
    """Resolve requested model choice to an available Gemini model, falling back to GEMINI_MODEL."""
    if model_choice in ("gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"):
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if model_choice == "gemini-flash-lite-latest":
        return "gemini-flash-lite-latest"
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _seed_eval_history_if_empty() -> None:
    """Sync saved eval/eval_results.json into SQLite when eval_runs is empty."""
    if count_eval_history() > 0 or not os.path.exists(EVAL_RESULTS_JSON_PATH):
        return
    try:
        with open(EVAL_RESULTS_JSON_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
        run_at = payload.get("generated_at", "")
        for model_name, model_data in payload.get("models", {}).items():
            for run in model_data.get("runs", []):
                save_eval_run(
                    run_at=run.get("run_at", run_at),
                    model_name=model_data.get("exact_model_name", model_name),
                    passed=int(run.get("passed", 0)),
                    total=int(run.get("total", 0)),
                    score_pct=float(run.get("score_pct", 0.0)),
                    category_scores=run.get("category_scores", {}),
                )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse, responses=COMMON_ERROR_RESPONSES)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/api/history/{session_id}", response_model=HistoryResponse, responses=COMMON_ERROR_RESPONSES)
def get_chat_history(
    session_id: str,
    model: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HistoryResponse:
    total = count_history(session_id, model)
    rows = get_history(session_id, model, limit=limit, offset=offset)
    items = [ChatMessageOut(**r) for r in rows]
    return HistoryResponse(
        session_id=session_id,
        model=model,
        history=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@app.delete("/api/history/{session_id}", response_model=StatusResponse, responses=COMMON_ERROR_RESPONSES)
def delete_chat_history(session_id: str, model: str = Query(..., min_length=1)) -> StatusResponse:
    clear_history(session_id, model)
    return StatusResponse(status="success", message=f"Cleared history for session '{session_id}'.")


@app.get("/api/stats", response_model=StatsResponse, responses=COMMON_ERROR_RESPONSES)
def get_observability_stats(
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> StatsResponse:
    total = count_stats()
    effective_limit = limit if limit is not None else max(total, 20)
    rows = get_stats(limit=limit, offset=offset)
    items = [ModelStatsOut(**r) for r in rows]
    return StatsResponse(
        stats=items,
        total=total,
        limit=effective_limit,
        offset=offset,
        has_more=(offset + len(items)) < total if limit is not None else False,
    )


@app.post("/api/chat", response_model=ChatResponse, responses=COMMON_ERROR_RESPONSES)
def chat(request: ChatRequest) -> ChatResponse:
    user_input = request.message
    session_id = request.session_id
    model_choice = request.model
    system_prompt = request.system_prompt

    is_safe, reason = check_input(user_input)
    if not is_safe:
        log_request(session_id, model_choice, len(user_input.split()), 0, 0.0, guardrail_triggered=True)
        return ChatResponse(
            role="assistant",
            content=f"🚫 {reason}",
            latency=0.0,
            tokens=0,
            tool_used=None,
            guardrail_triggered=True,
        )

    tool_name, tool_result = route_tool(user_input)
    fresh_history = get_history(session_id, model_choice)

    try:
        if "gemini" in model_choice.lower():
            from models.gemini_model import generate as gemini_generate

            gemini_id = _resolve_gemini_model_id(model_choice)
            response, p_tok, c_tok, latency = gemini_generate(
                user_input,
                fresh_history,
                tool_context=tool_result or "",
                system_prompt=system_prompt,
                model_name=gemini_id,
            )
        else:
            from models.qwen_model import generate as qwen_generate

            response, p_tok, c_tok, latency = qwen_generate(
                user_input,
                fresh_history,
                tool_context=tool_result or "",
                system_prompt=system_prompt,
            )
        save_message(session_id, model_choice, "user", user_input)
    except Exception as exc:
        response = f"⚠️ Model error: {exc}"
        p_tok, c_tok, latency = 0, 0, 0.0

    out_safe, out_reason = check_output(response)
    if not out_safe:
        response = out_reason
        log_request(session_id, model_choice, p_tok, c_tok, latency, guardrail_triggered=True, tool_used=tool_name)
    else:
        log_request(session_id, model_choice, p_tok, c_tok, latency, tool_used=tool_name)

    save_message(session_id, model_choice, "assistant", response)

    return ChatResponse(
        role="assistant",
        content=response,
        latency=float(latency),
        tokens=int(c_tok),
        tool_used=f"{tool_name} -> {tool_result}" if tool_result else None,
        guardrail_triggered=not out_safe,
    )


@app.post(
    "/api/chat/stream",
    responses={
        **COMMON_ERROR_RESPONSES,
        200: {
            "description": "Server-Sent Events stream of assistant tokens.",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        },
    },
)
def chat_stream(request: ChatRequest) -> StreamingResponse:
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
        try:
            if "gemini" in model_choice.lower():
                from models.gemini_model import generate_stream as gemini_generate_stream

                gemini_id = _resolve_gemini_model_id(model_choice)
                stream = gemini_generate_stream(
                    user_input,
                    fresh_history,
                    tool_context=tool_result or "",
                    system_prompt=system_prompt,
                    model_name=gemini_id,
                )
            else:
                from models.qwen_model import generate_stream as qwen_generate_stream

                stream = qwen_generate_stream(
                    user_input,
                    fresh_history,
                    tool_context=tool_result or "",
                    system_prompt=system_prompt,
                )

            full_response = ""
            for chunk in stream:
                full_response += chunk
                payload = {"content": chunk, "tool_used": tool_str, "is_done": False}
                yield f"data: {json.dumps(payload)}\n\n"

            out_safe, out_reason = check_output(full_response)
            if not out_safe:
                yield f"data: {json.dumps({'content': f'\\n\\n🚫 {out_reason}', 'is_done': False})}\n\n"

            save_message(session_id, model_choice, "user", user_input)
            msg_id = save_message(session_id, model_choice, "assistant", full_response)
            log_request(
                session_id,
                model_choice,
                len(user_input.split()),
                len(full_response.split()),
                0.0,
                tool_used=tool_name,
            )
            yield f"data: {json.dumps({'content': '', 'is_done': True, 'message_id': msg_id})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(generate_responses(), media_type="text/event-stream")


@app.post("/api/rate/{message_id}", response_model=RateResponse, responses=COMMON_ERROR_RESPONSES)
def rate(message_id: int, req: RateRequest) -> RateResponse:
    rate_message(message_id, req.rating)
    return RateResponse(status="success", message_id=message_id, rating=req.rating)


# --- EVAL RUNNER ---
eval_thread: Optional[threading.Thread] = None


def run_eval_background(log_path: str) -> None:
    import sys
    import traceback

    with open(log_path, "w", encoding="utf-8") as f:
        old_stdout = sys.stdout
        sys.stdout = f
        try:
            run_eval_main(runs=1)
        except Exception as exc:
            f.write(f"\nERROR: {exc}\n")
            traceback.print_exc(file=f)
        finally:
            sys.stdout = old_stdout


@app.post(
    "/api/eval/run",
    response_model=EvalRunTriggerResponse,
    responses=AUTH_ERROR_RESPONSES,
    dependencies=[Depends(verify_api_key)],
)
def run_eval() -> EvalRunTriggerResponse:
    """Trigger the evaluation suite in a background thread (API key required)."""
    global eval_thread
    if eval_thread and eval_thread.is_alive():
        return EvalRunTriggerResponse(
            status="already_running",
            message="Evaluation runner is already executing.",
        )

    log_path = os.path.join(os.path.dirname(__file__), "eval", "eval_logs.txt")
    eval_thread = threading.Thread(target=run_eval_background, args=(log_path,), daemon=True)
    eval_thread.start()
    return EvalRunTriggerResponse(
        status="started",
        message="Evaluation suite started in the background.",
    )


@app.get("/api/eval/logs", response_model=EvalLogsResponse, responses=COMMON_ERROR_RESPONSES)
def get_eval_logs() -> EvalLogsResponse:
    global eval_thread
    log_path = os.path.join(os.path.dirname(__file__), "eval", "eval_logs.txt")
    logs = ""
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logs = f.read()

    is_running = eval_thread is not None and eval_thread.is_alive()
    return EvalLogsResponse(logs=logs, is_running=is_running)


@app.get("/api/eval/history", response_model=EvalHistoryResponse, responses=COMMON_ERROR_RESPONSES)
def get_evaluation_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> EvalHistoryResponse:
    """Return paginated evaluation run history."""
    _seed_eval_history_if_empty()
    total = count_eval_history()
    rows = get_eval_history(limit=limit, offset=offset)
    items = [EvalRunOut(**r) for r in rows]
    return EvalHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@app.post("/api/compare", response_model=CompareResponse, responses=COMMON_ERROR_RESPONSES)
def compare(request: CompareRequest) -> CompareResponse:
    user_input = request.message

    is_safe, reason = check_input(user_input)
    if not is_safe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    tool_name, tool_result = route_tool(user_input)

    try:
        from models.gemini_model import generate as gemini_gen

        g_resp, _, g_ct, g_lat = gemini_gen(
            user_input, [], tool_context=tool_result or "", model_name=DEFAULT_GEMINI_MODEL
        )
        g_safe, g_reason = check_output(g_resp)
        g_resp = g_resp if g_safe else g_reason
    except Exception as exc:
        g_resp, g_ct, g_lat = f"Error: {exc}", 0, 0.0

    try:
        from models.qwen_model import generate as qwen_gen

        q_resp, _, q_ct, q_lat = qwen_gen(user_input, [], tool_context=tool_result or "")
        q_safe, q_reason = check_output(q_resp)
        q_resp = q_resp if q_safe else q_reason
    except Exception as exc:
        q_resp, q_ct, q_lat = f"Error: {exc}", 0, 0.0

    return CompareResponse(
        tool_used=f"{tool_name} -> {tool_result}" if tool_result else None,
        gemini=CompareModelResult(content=g_resp, latency=float(g_lat), tokens=int(g_ct)),
        qwen=CompareModelResult(content=q_resp, latency=float(q_lat), tokens=int(q_ct)),
    )


frontend_out = "/home/user/frontend_out"
if not os.path.exists(frontend_out):
    frontend_out = os.path.join(os.path.dirname(__file__), "frontend", "out")

if os.path.exists(frontend_out):
    app.mount("/", StaticFiles(directory=frontend_out, html=True), name="frontend")
else:
    @app.get("/", response_model=RootResponse, responses=COMMON_ERROR_RESPONSES)
    def read_root() -> RootResponse:
        return RootResponse(
            status="ok",
            message="Ollive AI Assistant Backend is running. Frontend static files are not mounted.",
        )
