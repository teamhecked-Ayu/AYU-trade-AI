from ayuai.jobs.queue import REDIS_URL, TaskStatus


def test_task_status_is_structured():
    status = TaskStatus(task_id="task-1", state="queued")
    assert status.task_id == "task-1"
    assert status.state == "queued"


def test_default_redis_url_is_configured():
    assert REDIS_URL.startswith("redis://")
