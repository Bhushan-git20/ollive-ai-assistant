import re

# Hard-block patterns — expand as needed
_BLOCKED_PATTERNS = [
    # Expand to catch all common phrasings of harmful requests
    r"\b(how (to|do I|can I|would I|do you) (make|build|create|synthesize) (a |an )?(bomb|weapon|explosive|poison|drug))\b",
    r"\b(kill (yourself|myself|himself|herself))\b",
    r"\b(suicide (method|plan|how))\b",
    r"\b(child (porn|abuse|exploit))\b",
    r"\b(hack (into )?(a |the )?(bank|system|account|password))\b",
    r"\bjailbreak\b",
    r"\bignore (all )?(previous |prior )?(instructions?|prompt)\b",
    r"\byou are now (dan|an? (unrestricted|unfiltered|evil))\b",
    r"\bact as (an? )?(unrestricted|unfiltered|evil|dan)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]

SYSTEM_SAFETY_SUFFIX = """
You are a helpful, honest, and harmless AI assistant.
- Never provide instructions for illegal activities or violence.
- Never produce content that could harm or deceive users.
- If a question is outside your knowledge, say so clearly rather than guessing.
- Be transparent about being an AI.
"""

def check_input(text: str) -> tuple[bool, str]:
    """
    Returns (is_safe, reason).
    is_safe=False means block the message.
    """
    for pattern in _COMPILED:
        if pattern.search(text):
            return False, "This message was flagged by the safety filter and cannot be processed."
    return True, ""

def check_output(text: str) -> tuple[bool, str]:
    """
    Light post-generation check.
    Returns (is_safe, reason).
    """
    for pattern in _COMPILED:
        if pattern.search(text):
            return False, "[Response blocked by safety guardrail]"
    return True, ""
