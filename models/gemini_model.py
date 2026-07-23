import os
import time
import google.generativeai as genai
from guardrails.safety_filter import SYSTEM_SAFETY_SUFFIX
from typing import List, Dict, Any

_clients = {}

def _get_client(system_prompt: str = None, model_name: str = "gemini-1.5-flash"):
    global _clients
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")
    genai.configure(api_key=api_key)
    
    base_system = system_prompt if system_prompt else "You are a helpful personal AI assistant."
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()
    
    cache_key = (full_system, model_name)
    if cache_key not in _clients:
        _clients[cache_key] = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=full_system
        )
    return _clients[cache_key]

def generate(prompt: str, history: List[Dict[str, Any]], tool_context: str = "", system_prompt: str = None, model_name: str = "gemini-1.5-flash") -> tuple[str, int, int, float]:
    start_time = time.time()
    
    # Prepend tool context to prompt if available
    if tool_context:
        prompt = f"[Tool Output: {tool_context}]\n\n{prompt}"

    model = _get_client(system_prompt, model_name)
    
    gemini_messages = []
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        gemini_messages.append({"role": role, "parts": [{"text": m["content"]}]})
    gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})

    response = model.generate_content(gemini_messages)
    
    latency = (time.time() - start_time) * 1000
    p_tokens = model.count_tokens(gemini_messages).total_tokens if hasattr(model, 'count_tokens') else 0
    c_tokens = model.count_tokens(response.text).total_tokens if hasattr(model, 'count_tokens') else 0
    
    return response.text, p_tokens, c_tokens, latency

def generate_stream(prompt: str, history: List[Dict[str, Any]], tool_context: str = "", system_prompt: str = None, model_name: str = "gemini-1.5-flash"):
    if tool_context:
        prompt = f"[Tool Output: {tool_context}]\n\n{prompt}"

    model = _get_client(system_prompt, model_name)
    
    gemini_messages = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_messages.append({"role": role, "parts": [{"text": msg["content"]}]})
        
    gemini_messages.append({"role": "user", "parts": [{"text": prompt}]})

    response_stream = model.generate_content(gemini_messages, stream=True)
    
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text
