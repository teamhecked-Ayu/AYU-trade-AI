# Background jobs

AYUAI uses Redis and Celery for long-running work.

## Why

AI analysis, large backtests and market processing should not block an API request.

## Local services

Start infrastructure:

    docker compose up -d postgres redis

Start a worker:

    celery -A ayuai.jobs.tasks.celery_app worker --loglevel=info

## Production

Use authenticated Redis, private networking and separate API/worker processes.
Do not expose Redis directly to the public internet.
