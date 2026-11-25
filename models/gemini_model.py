import os
import re
import time
from typing import Any, Dict, List, Optional
import google.generativeai as genai
from guardrails.safety_filter import SYSTEM_SAFETY_SUFFIX

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
_clients = {}


def _get_client(
    system_prompt: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
):
    global _clients
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file or environment variables.")
    genai.configure(api_key=api_key)

    chosen_model = model_name or DEFAULT_GEMINI_MODEL
    base_system = system_prompt if system_prompt else "You are a helpful personal AI assistant."
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()

    cache_key = (full_system, chosen_model, temperature)
    if cache_key not in _clients:
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=0.9,
        )
        _clients[cache_key] = genai.GenerativeModel(
            model_name=chosen_model,
            system_instruction=full_system,
            generation_config=generation_config,
        )
    return _clients[cache_key], chosen_model


def _format_model_error(model_name: str, exc: Exception) -> str:
    err_str = str(exc)
    err_lower = err_str.lower()
    if "404" in err_str or "not found" in err_lower or "no longer available" in err_lower:
        return (
            f"Configured model '{model_name}' is not found or deprecated on Google Generative AI API. "
            f"Please set GEMINI_MODEL to an available model (e.g. 'gemini-2.5-flash')."
        )
    return f"Model error: {exc}"


def generate(
    prompt: str,
    history: List[Dict[str, Any]],
    tool_context: str = "",
    system_prompt: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
) -> tuple[str, int, int, float]:
    start_time = time.time()

    if tool_context:
        prompt = f"[Tool Output: {tool_context}]\n\n{prompt}"

    model, actual_model_name = _get_client(
        system_prompt=system_prompt,
        model_name=model_name,
        temperature=temperature,
    )

    gemini_messages = []
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        gemini_messages.append({"role": role, "parts": [{"text": m["content"]}]})
    gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})

    try:
        response = model.generate_content(gemini_messages)
        latency = (time.time() - start_time) * 1000
        p_tokens = (
            model.count_tokens(gemini_messages).total_tokens
            if hasattr(model, "count_tokens")
            else 0
        )
        c_tokens = (
            model.count_tokens(response.text).total_tokens
            if hasattr(model, "count_tokens") and response.text
            else 0
        )
        return response.text, p_tokens, c_tokens, latency
    except Exception as exc:
        clean_msg = _format_model_error(actual_model_name, exc)
        raise RuntimeError(clean_msg) from exc


def generate_stream(
    prompt: str,
    history: List[Dict[str, Any]],
    tool_context: str = "",
    system_prompt: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
):
    if tool_context:
        prompt = f"[Tool Output: {tool_context}]\n\n{prompt}"

    model, actual_model_name = _get_client(
        system_prompt=system_prompt,
        model_name=model_name,
        temperature=temperature,
    )

    gemini_messages = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_messages.append({"role": role, "parts": [{"text": msg["content"]}]})
    gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})

    try:
        response_stream = model.generate_content(gemini_messages, stream=True)
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as exc:
        clean_msg = _format_model_error(actual_model_name, exc)
        raise RuntimeError(clean_msg) from exc
