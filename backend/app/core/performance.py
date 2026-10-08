import time
import logging
import statistics
from typing import Dict, Any, Optional, List
from contextlib import contextmanager, asynccontextmanager

logger = logging.getLogger("study_buddy.performance")

class PerformanceMetricsStore:
    """
    Thread-safe in-memory store for performance measurements with percentiles and counts.
    """
    def __init__(self, max_history_per_op: int = 500):
        self._history: Dict[str, List[float]] = {}
        self._counts: Dict[str, int] = {}
        self._errors: Dict[str, int] = {}
        self.max_history = max_history_per_op

    def record(self, operation: str, duration_ms: float, success: bool = True, metadata: Optional[Dict[str, Any]] = None):
        if operation not in self._history:
            self._history[operation] = []
            self._counts[operation] = 0
            self._errors[operation] = 0

        self._counts[operation] += 1
        if not success:
            self._errors[operation] += 1

        hist = self._history[operation]
        hist.append(duration_ms)
        if len(hist) > self.max_history:
            hist.pop(0)

        # Sanitized metadata string
        meta_str = ""
        if metadata:
            sanitized = {k: v for k, v in metadata.items() if not any(p in k.lower() for p in ("token", "pass", "content", "text", "auth"))}
            if sanitized:
                meta_str = " " + " ".join(f"{k}={v}" for k, v in sanitized.items())

        logger.info(f"PERF operation={operation} duration_ms={duration_ms:.2f} success={success}{meta_str}")

    def get_summary(self) -> Dict[str, Any]:
        summary = {}
        for op, durations in self._history.items():
            if not durations:
                continue
            sorted_durations = sorted(durations)
            n = len(sorted_durations)
            p50 = sorted_durations[int(n * 0.5)] if n > 0 else 0
            p95 = sorted_durations[min(int(n * 0.95), n - 1)] if n > 0 else 0
            summary[op] = {
                "count": self._counts.get(op, 0),
                "error_count": self._errors.get(op, 0),
                "avg_ms": round(sum(durations) / len(durations), 2),
                "min_ms": round(min(durations), 2),
                "max_ms": round(max(durations), 2),
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
            }
        return summary

    def clear(self):
        self._history.clear()
        self._counts.clear()
        self._errors.clear()

# Global performance metrics singleton
perf_store = PerformanceMetricsStore()

@contextmanager
def perf_tracker(operation: str, metadata: Optional[Dict[str, Any]] = None):
    start = time.perf_counter()
    success = True
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        perf_store.record(operation, duration_ms, success=success, metadata=metadata)

@asynccontextmanager
async def async_perf_tracker(operation: str, metadata: Optional[Dict[str, Any]] = None):
    start = time.perf_counter()
    success = True
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        perf_store.record(operation, duration_ms, success=success, metadata=metadata)
