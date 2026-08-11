from __future__ import annotations

import hashlib
import re
from typing import Any

PII_PATTERNS: dict[str, str] = {
    "email": r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    "cccd": r"(?<!\d)\d{12}(?!\d)",
    "cmnd": r"(?<!\d)(?![0][35789])\d{9}(?!\d)",
    "passport_vn": r"(?<![A-Za-z0-9])[B-HK-NP-Z]\d{7,8}(?![A-Za-z0-9])",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "secret": r"(?i)\b(?:sk-[a-zA-Z0-9_-]{20,}|ghp_[a-zA-Z0-9]{36}|Bearer\s+[a-zA-Z0-9\._\-]+|(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[^\s'\"]+['\"]?)",
    "address": r"(?i)\b(?:Số\s+\d+|Thôn|Xóm|Ngõ|Ngách|Hẻm|Đường|Phố|Phường|Xã|Thị\s+trấn|Quận|Huyện|Thị\s+xã|Tỉnh|TP|Thành\s+phố)\s+[^,\n]+(?:,\s*(?:Đường|Phố|Phường|Xã|Thị\s+trấn|Quận|Huyện|Tỉnh|TP|Thành\s+phố)\s+[^,\n]+)*",
}


def scrub_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def scrub_data(obj: Any) -> Any:
    """Duyệt đệ quy để scrub PII trong Dict, List, Tuple hoặc Primitive Types."""
    if isinstance(obj, str):
        return scrub_text(obj)
    elif isinstance(obj, dict):
        return {k: scrub_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [scrub_data(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(scrub_data(item) for item in obj)
    return obj


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str | None) -> str:
    if not user_id:
        return "anonymous"
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]

