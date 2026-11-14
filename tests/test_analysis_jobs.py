from unittest.mock import patch
from ayuai.jobs.analysis import submit_analysis


class FakeTask:
    id = "job-123"
    state = "PENDING"


@patch("ayuai.jobs.analysis.celery_app.send_task", return_value=FakeTask())
def test_submit_analysis_returns_job(mock_send):
    job = submit_analysis("Analyze BTC", "user-1")
    assert job.job_id == "job-123"
    assert job.state == "PENDING"
    mock_send.assert_called_once()
