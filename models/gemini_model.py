import os
import time
import google.generativeai as genai
from guardrails.safety_filter import SYSTEM_SAFETY_SUFFIX

MODEL_NAME = "gemini-2.5-flash-preview-05-20"

def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=f"You are a helpful personal AI assistant.{SYSTEM_SAFETY_SUFFIX}"
    )

def generate(prompt: str, history: list[dict], tool_context: str = "") -> tuple[str, int, int, float]:
    """
    Generate a response using Gemini 2.5 Flash.
    Returns: (response_text, prompt_tokens, completion_tokens, latency_ms)
    """
    model = _get_client()

    # Build Gemini-format history
    gemini_history = []
    for msg in history[:-1]:  # exclude last (current user message)
        gemini_history.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [msg["content"]]
        })

    full_prompt = prompt
    if tool_context:
        full_prompt = f"[Tool result: {tool_context}]\n\nUser question: {prompt}"

    chat = model.start_chat(history=gemini_history)

    start = time.time()
    response = chat.send_message(full_prompt)
    latency_ms = (time.time() - start) * 1000

    text = response.text
    # Gemini usage metadata
    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", len(prompt.split()))
    completion_tokens = getattr(usage, "candidates_token_count", len(text.split()))

    return text, prompt_tokens, completion_tokens, latency_ms
