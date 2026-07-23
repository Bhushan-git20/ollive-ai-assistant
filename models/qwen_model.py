import time
import os
import requests
import json
import threading
from typing import List, Dict, Any
from guardrails.safety_filter import SYSTEM_SAFETY_SUFFIX

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct/v1/chat/completions"

_pipeline = None
_model_lock = threading.Lock()

def _load_pipeline():
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        _pipeline = pipeline(
            "text-generation",
            model=MODEL_ID,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True,
        )
    return _pipeline

def generate(prompt: str, history: List[Dict[str, Any]], tool_context: str = "", system_prompt: str = None) -> tuple[str, int, int, float]:
    """
    Generate a response using Qwen2.5-7B-Instruct via Serverless API,
    falling back to local Qwen2.5-0.5B-Instruct pipeline if API is unavailable.
    """
    base_system = system_prompt if system_prompt else "You are a helpful personal AI assistant."
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()

    messages = [{"role": "system", "content": full_system}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    user_content = prompt
    if tool_context:
        user_content = f"[Tool result: {tool_context}]\n\nUser question: {prompt}"
    messages.append({"role": "user", "content": user_content})

    start = time.time()
    
    # Try Hugging Face Serverless API first
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HF_API_KEY")
    if hf_token:
        try:
            headers = {
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.7,
                "stream": False
            }
            res = requests.post(API_URL, headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                latency_ms = (time.time() - start) * 1000
                prompt_tokens = sum(len(m["content"].split()) for m in messages)
                completion_tokens = len(text.split())
                return text, prompt_tokens, completion_tokens, latency_ms
        except Exception as api_err:
            print(f"HF Serverless API error: {api_err}. Falling back to local pipeline.", flush=True)

    # Local pipeline fallback
    pipe = _load_pipeline()
    with _model_lock:
        output = pipe(
            messages,
            max_new_tokens=512,
            max_length=None,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=pipe.tokenizer.eos_token_id,
        )
    latency_ms = (time.time() - start) * 1000

    generated = output[0]["generated_text"]
    if isinstance(generated, list):
        text = generated[-1]["content"]
    else:
        text = str(generated)

    prompt_tokens = sum(len(m["content"].split()) for m in messages)
    completion_tokens = len(text.split())

    return text, prompt_tokens, completion_tokens, latency_ms

def generate_stream(prompt: str, history: List[Dict[str, Any]], tool_context: str = "", system_prompt: str = None):
    """
    Yields chunks of text as they arrive from Qwen2.5-7B-Instruct via Serverless API,
    falling back to local Qwen2.5-0.5B-Instruct pipeline.
    """
    base_system = system_prompt if system_prompt else "You are a helpful personal AI assistant."
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()

    messages = [{"role": "system", "content": full_system}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    user_content = prompt
    if tool_context:
        user_content = f"[Tool result: {tool_context}]\n\nUser question: {prompt}"
    messages.append({"role": "user", "content": user_content})

    hf_token = os.getenv("HF_TOKEN") or os.getenv("HF_API_KEY")
    if hf_token:
        try:
            headers = {
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.7,
                "stream": True
            }
            res = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=10)
            if res.status_code == 200:
                for line in res.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').strip()
                        if decoded.startswith("data: "):
                            data_str = decoded[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                content = chunk_json["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue
                return
        except Exception as api_err:
            print(f"HF Serverless Stream error: {api_err}. Falling back to local pipeline.", flush=True)

    # Local pipeline fallback streaming
    from transformers import TextIteratorStreamer
    from threading import Thread

    pipe = _load_pipeline()
    streamer = TextIteratorStreamer(pipe.tokenizer, skip_prompt=True, skip_special_tokens=True)
    
    def locked_generate():
        with _model_lock:
            try:
                pipe(
                    messages,
                    streamer=streamer,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=pipe.tokenizer.eos_token_id,
                )
            except Exception as e:
                import sys
                print(f"Qwen stream error: {e}", file=sys.stderr)
                if hasattr(streamer, "text_queue") and hasattr(streamer, "stop_signal"):
                    streamer.text_queue.put(f"\n[Model Error: {e}]")
                    streamer.text_queue.put(streamer.stop_signal)

    thread = Thread(target=locked_generate)
    thread.start()

    for new_text in streamer:
        yield new_text
