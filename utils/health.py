import time


class HealthState:
    def __init__(self):
        self.started_at = time.time()
        self.last_error = None

    def snapshot(self):
        return {
            "status": "degraded" if self.last_error else "ok",
            "uptime_seconds": round(time.time() - self.started_at, 2),
        }
