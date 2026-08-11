from collections import Counter

import app.metrics as metrics
from app.metrics import percentile


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_snapshot_error_rate_counts_successful_and_failed_requests(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 0)
    monkeypatch.setattr(metrics, "ERRORS", Counter())

    for _ in range(4):
        metrics.record_request(
            latency_ms=100,
            cost_usd=0.01,
            tokens_in=10,
            tokens_out=20,
            quality_score=0.8,
        )
    metrics.record_error("TimeoutError")

    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 5
    assert snapshot["error_rate_pct"] == 20.0
    assert snapshot["error_breakdown"] == {"TimeoutError": 1}


def test_snapshot_error_rate_is_zero_without_traffic(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 0)
    monkeypatch.setattr(metrics, "ERRORS", Counter())

    snapshot = metrics.snapshot()

    assert snapshot["error_rate_pct"] == 0.0
