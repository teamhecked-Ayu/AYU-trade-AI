# AYUAI Intelligence Worker

The background worker now calls the AYUAI orchestration pipeline.

## Pipeline

1. Independent provider analysis
2. Reasoning and evidence checks
3. Agent debate
4. Final decision synthesis

The API only submits a job. Provider credentials remain server-side and are not
included in Redis messages or API responses.

## Deployment requirement

A deployment must register real providers in `ayuai.bootstrap.build_provider_manager()`.
An empty provider registry fails safely rather than fabricating an AI answer.
