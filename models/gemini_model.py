import os
import time
import google.generativeai as genai
from guardrails.safety_filter import SYSTEM_SAFETY_SUFFIX
from typing import List, Dict, Any

MODEL_NAME = "gemini-2.5-flash"
_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")
        genai.configure(api_key=api_key)
        _client = genai
    return _client

def generate(prompt: str, history: List[Dict[str, Any]], tool_context: str = "", system_prompt: str = None) -> tuple[str, int, int, float]:
    start_time = time.time()
    
    # Prepend tool context to prompt if available
    if tool_context:
        prompt = f"[Tool Output: {tool_context}]\n\n{prompt}"

    base_system = system_prompt if system_prompt else ""
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()

    messages = [{"role": "system", "content": full_system}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    client = _get_client()
    
    # Safe fallback: prepend to the first user message
    gemini_messages = []
    for m in messages:
        if m["role"] == "system":
            # Just append it to the next user message to be safe across gemini versions
            gemini_messages.append({"role": "user", "parts": [{"text": f"System Instruction: {m['content']}"}]})
            gemini_messages.append({"role": "model", "parts": [{"text": "Understood."}]})
        else:
            role = "model" if m["role"] == "assistant" else "user"
            gemini_messages.append({"role": role, "parts": [{"text": m["content"]}]})

    model = client.GenerativeModel("gemini-2.5-flash") # Using latest available fallback
    
    response = model.generate_content(gemini_messages)
    
    latency = (time.time() - start_time) * 1000
    p_tokens = model.count_tokens(gemini_messages).total_tokens if hasattr(model, 'count_tokens') else 0
    c_tokens = model.count_tokens(response.text).total_tokens if hasattr(model, 'count_tokens') else 0
    
    return response.text, p_tokens, c_tokens, latency

def generate_stream(prompt: str, history: List[Dict[str, Any]], tool_context: str = "", system_prompt: str = None):
    if tool_context:
        prompt = f"[Tool Output: {tool_context}]\n\n{prompt}"

    base_system = system_prompt if system_prompt else ""
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()

    client = _get_client()
    
    gemini_messages = []
    gemini_messages.append({"role": "user", "parts": [{"text": f"System Instruction: {full_system}"}]})
    gemini_messages.append({"role": "model", "parts": [{"text": "Understood."}]})
    
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_messages.append({"role": role, "parts": [{"text": msg["content"]}]})
        
    gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})

    model = client.GenerativeModel("gemini-2.5-flash")
    
    response_stream = model.generate_content(gemini_messages, stream=True)
    
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text
