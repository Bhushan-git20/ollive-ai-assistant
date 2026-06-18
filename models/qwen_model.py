import time
import threading
from typing import List, Dict, Any
from guardrails.safety_filter import SYSTEM_SAFETY_SUFFIX

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

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
    Generate a response using Qwen2.5-0.5B-Instruct.
    Returns: (response_text, prompt_tokens, completion_tokens, latency_ms)
    """
    pipe = _load_pipeline()

    base_system = system_prompt if system_prompt else "You are a helpful personal AI assistant."
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()

    messages = [{"role": "system", "content": full_system}]
    for msg in history[:-1]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": prompt})

    if tool_context:
        messages[-1]["content"] = f"[Tool result: {tool_context}]\n\nUser question: {messages[-1]['content']}"

    start = time.time()
    
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
    """Yields chunks of text as they arrive from Qwen using a background thread."""
    from transformers import TextIteratorStreamer
    from threading import Thread

    pipe = _load_pipeline()
    
    base_system = system_prompt if system_prompt else "You are a helpful personal AI assistant."
    full_system = f"{base_system}\n\n{SYSTEM_SAFETY_SUFFIX}".strip()

    messages = [{"role": "system", "content": full_system}]
    for msg in history[:-1]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": prompt})

    if tool_context:
        messages[-1]["content"] = f"[Tool result: {tool_context}]\n\nUser question: {messages[-1]['content']}"

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
