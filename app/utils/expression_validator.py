import re

MAX_EXPRESSION_LENGTH = 500
BLOCKED_PATTERNS = [
    r"__",
    r"\bimport\b",
    r"\bexec\b",
    r"\beval\b",
    r"\bopen\b",
    r"\bos\.",
    r"\bsys\.",
    r"\bsubprocess\b",
]


def validate_expression(expr: str) -> str:
    cleaned = (expr or "").strip()
    if not cleaned:
        raise ValueError("Expression is empty")
    if len(cleaned) > MAX_EXPRESSION_LENGTH:
        raise ValueError(f"Expression too long (max {MAX_EXPRESSION_LENGTH})")
    lower = cleaned.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, lower):
            raise ValueError("Invalid expression")
    return cleaned
