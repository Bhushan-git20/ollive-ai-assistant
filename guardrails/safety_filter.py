import re

_LEET_MAP = str.maketrans({
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
    "!": "i",
})

# Hard-block patterns — expand as needed
_BLOCKED_PATTERNS = [
    # Harmful requests & leetspeak variants
    r"\b(how (to|do I|can I|would I|do you) (make|build|create|synthesize) (a |an )?(b[o0]mb|weapon|explosive|p[o0]is[o0]n|drug))\b",
    r"\b(kill (yourself|myself|himself|herself))\b",
    r"\b(suicide (method|plan|how))\b",
    r"\b(child (porn|abuse|exploit))\b",
    r"\b(hack (into )?(a |the )?(bank|system|account|password))\b",
    r"\bjailbreak\b",
    r"\bignore (all )?(previous |prior )?(instructions?|prompt)\b",
    r"\byou are now (dan|an? (unrestricted|unfiltered|evil))\b",
    r"\bact as (an? )?(unrestricted|unfiltered|evil|dan)\b",
    # SQL injection patterns
    r"\b(drop|alter|truncate)\s+(table|database)\b",
    r"\bdelete\s+(from\s+\w+|table|database)\b",
    r"\bunion\s+(all\s+)?select\b",
    r"(['\"])\s*or\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+",
    r"\bor\s+1\s*=\s*1\b",
    r";\s*(drop|alter|delete|truncate|insert|update|exec)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]

SYSTEM_SAFETY_SUFFIX = """
You are a helpful, honest, and harmless AI assistant.
- Never provide instructions for illegal activities or violence.
- Never produce content that could harm or deceive users.
- If a question is outside your knowledge, say so clearly rather than guessing.
- Be transparent about being an AI.
"""


def _normalize_leetspeak(text: str) -> str:
    return text.translate(_LEET_MAP)


def check_input(text: str) -> tuple[bool, str]:
    """
    Returns (is_safe, reason).
    is_safe=False means block the message.
    """
    candidates = (text, _normalize_leetspeak(text))
    for candidate in candidates:
        for pattern in _COMPILED:
            if pattern.search(candidate):
                return False, "This message was flagged by the safety filter and cannot be processed."
    return True, ""


def check_output(text: str) -> tuple[bool, str]:
    """
    Light post-generation check.
    Returns (is_safe, reason).
    """
    candidates = (text, _normalize_leetspeak(text))
    for candidate in candidates:
        for pattern in _COMPILED:
            if pattern.search(candidate):
                return False, "[Response blocked by safety guardrail]"
    return True, ""
