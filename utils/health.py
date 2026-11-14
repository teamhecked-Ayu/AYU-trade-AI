import time

class HealthState:
    def __init__(self):
        self.started_at = time.time()
        self.last_error = None
        self.last_success_at = time.time()

    def mark_success(self):
        self.last_success_at = time.time()
        self.last_error = None

    def mark_error(self, error):
        self.last_error = str(error)

    def snapshot(self):
        return {
            "status": "degraded" if self.last_error else "ok",
            "uptime_seconds": round(time.time() - self.started_at, 2),
            "last_success_at": self.last_success_at,
            "last_error": self.last_error,
        }
