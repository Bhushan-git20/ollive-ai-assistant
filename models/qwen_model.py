import time
from guardrails.safety_filter import SYSTEM_SAFETY_SUFFIX

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

_pipeline = None

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

def generate(prompt: str, history: list[dict], tool_context: str = "") -> tuple[str, int, int, float]:
    """
    Generate a response using Qwen2.5-0.5B-Instruct.
    Returns: (response_text, prompt_tokens, completion_tokens, latency_ms)
    """
    pipe = _load_pipeline()

    system_msg = f"You are a helpful personal AI assistant.{SYSTEM_SAFETY_SUFFIX}"

    messages = [{"role": "system", "content": system_msg}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": prompt})

    if tool_context:
        # Inject tool result before last user message
        messages[-1]["content"] = f"[Tool result: {tool_context}]\n\nUser question: {messages[-1]['content']}"

    start = time.time()
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

    # Extract generated text (last assistant turn)
    generated = output[0]["generated_text"]
    # pipeline returns full messages list — get last assistant message
    if isinstance(generated, list):
        text = generated[-1]["content"]
    else:
        text = str(generated)

    # Rough token count
    prompt_tokens = sum(len(m["content"].split()) for m in messages)
    completion_tokens = len(text.split())

    return text, prompt_tokens, completion_tokens, latency_ms
