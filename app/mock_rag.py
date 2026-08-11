from __future__ import annotations

import time

from .incidents import STATE
from .tracing import get_langfuse_client, observe

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, traces localize them, logs explain root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}


@observe()
def retrieve(message: str) -> list[str]:
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)
    lowered = message.lower()
    for key, docs in CORPUS.items():
        if key in lowered:
            get_langfuse_client().update_current_span(
                metadata={"matched_key": key, "doc_count": len(docs)}
            )
            return docs
    get_langfuse_client().update_current_span(metadata={"matched_key": None, "doc_count": 0})
    return ["No domain document matched. Use general fallback answer."]
