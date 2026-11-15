# AYU Trade AI

AYU Trade AI is a Python-based research and paper-trading project. It combines an AYUAI multi-provider analysis pipeline with a separate deterministic market-data, signal, risk, and simulated portfolio system.

**Default operating mode is paper trading. AI analysis does not place orders. Live exchange execution is not validated or production-ready.**

## What is implemented

### AYUAI multi-agent analysis
- Supports OpenAI, Anthropic, Gemini, DeepSeek, and Perplexity provider adapters.
- Runs provider analyses independently before reasoning and adversarial review.
- Extracts claims, disagreements, assumptions, risks, uncertainty, and evidence gaps.
- Accepts only an explicit `CONCLUSION: ...` field as a provider action vote.
- Returns insufficient evidence on tied conclusions and requires human review for low confidence, incomplete coverage, contradictions, or unresolved issues.
- Stores completed decision summaries in the authenticated user's history.

### API and account security
- FastAPI endpoints for account registration, login, authenticated analysis, provider-key management, and decision history.
- Provider API keys are encrypted server-side with `AYUAI_KEY_VAULT_SECRET`.
- Analysis job status and event streams are restricted to the user who submitted the job.
- CORS uses an explicit origin allowlist.
- Docker Compose uses a shared Redis rate limiter. Local development can use the in-memory limiter.
- `/health` is a liveness check. `/ready` checks required secrets and database readiness, and checks Redis when Redis limiting is enabled.

### Trading and market data
- CCXT-based market data and historical candle validation.
- Optional secondary market-data provider for validated fallback and cross-source comparison.
- Technical and sentiment signals, deterministic risk checks, and backtesting modules.
- One SQLite-backed paper portfolio shared by the API, broker bridge's paper mode, and AYUAI paper-trading facade (persistent by default; in-memory mode is explicit for isolated tests).
- Portfolio orders are committed atomically to avoid stale in-memory writes.

## System layout

```text
Browser dashboard
  ├── Account and provider-key management
  ├── AYUAI question submission
  │     └── FastAPI → Redis/Celery → independent AI providers
  │                          └── reasoning → debate → decision
  │                                         └── PostgreSQL history
  └── Manual paper portfolio
        └── FastAPI → SQLite shared portfolio store

Market data → validation/fallback → indicators and sentiment
             → signal aggregation → deterministic risk checks
             → paper portfolio (separate from AYUAI analysis)
```

## Run with Docker Compose

### 1. Create your environment file

```bash
cp .env.example .env
```

Replace the example values with your own secrets. Use separate random values for all four secrets below:

- `AYU_API_KEY`
- `AYUAI_AUTH_SECRET`
- `AYUAI_KEY_VAULT_SECRET`
- `POSTGRES_PASSWORD`

You can generate a URL-safe secret with:

```bash
openssl rand -hex 32
```

Run that command separately for each secret. Do not reuse one secret for multiple purposes, do not commit `.env`, and do not put provider keys in frontend code.

Provider keys in `.env` are optional if a signed-in user saves their own key through the dashboard. Set `AYUAI_CORS_ORIGINS` to the exact browser origins you trust. The example permits the two local development origins.

### 2. Start services

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

Compose starts PostgreSQL and Redis, runs Alembic migrations, starts the FastAPI service, and starts the Celery worker. The API and worker wait for the database migration and infrastructure healthchecks.

### 3. Start the browser dashboard

In a separate terminal:

```bash
python -m http.server 8080 --directory frontend
```

Open `http://localhost:8080`. Connect to `http://localhost:8000`, create an account, and sign in.

### 4. Check service status

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
docker compose logs -f ayu-trade-ai celery-worker
```

The API container readiness check requires the secrets, PostgreSQL, and Redis when the Redis rate-limit backend is enabled.

## API reference

| Endpoint | Purpose | Access |
|---|---|---|
| `GET /health` | Liveness | Public |
| `GET /ready` | Configuration and dependency readiness | Public |
| `POST /auth/register` | Create an account | Rate limited |
| `POST /auth/login` | Sign in and receive a bearer token | Rate limited |
| `GET /auth/me` | Read the authenticated account ID | Bearer token |
| `GET /providers` | List saved provider names | Bearer token |
| `PUT /providers/{provider}` | Encrypt and save a provider key | Bearer token |
| `DELETE /providers/{provider}` | Remove a saved provider key | Bearer token |
| `POST /analysis` | Queue a new AYUAI analysis | Bearer token |
| `GET /analysis/{job_id}` | Read an owned job's status/result | Job owner |
| `GET /analysis/{job_id}/events` | Stream an owned job's events | Job owner |
| `GET /decisions` | Read the account's saved decision summaries | Bearer token |
| `GET /metrics` | Read paper portfolio metrics | `X-API-Key` |
| `GET /portfolio` | Read paper portfolio state | `X-API-Key` |
| `POST /paper/orders` | Submit a manual simulated order | `X-API-Key` |

AYUAI uses `Authorization: Bearer <token>`. The paper portfolio uses the separate `X-API-Key` header. The browser dashboard keeps these credentials in page memory and does not save them to local storage.

## Local test and validation commands

```bash
python -m pip install -r requirements-test.txt
python -m compileall -q api ayuai core paper_api.py
python -m pytest tests -q
node --check frontend/app.js
cp .env.example .env
docker compose config --quiet
```

GitHub Actions runs the Python test suite, Python compilation, frontend JavaScript syntax check, and Compose configuration validation.

## Data and backups

- PostgreSQL stores AYUAI accounts, provider credentials, decisions, and analysis-job ownership.
- Redis stores Celery messages/results and the shared API rate-limit counters.
- SQLite at `PAPER_PORTFOLIO_DB` stores the shared simulated portfolio.
- Docker named volumes persist PostgreSQL and Redis data. The local `data/` directory stores the paper portfolio database.

Back up the persistent volumes and the SQLite file before migrations or upgrades. Keep the encryption secret: losing `AYUAI_KEY_VAULT_SECRET` means saved provider keys cannot be decrypted.

## Important limitations

- Tests use deterministic fakes for many external services. Real provider calls and live data-feed behavior have not been validated with production credentials.
- A secondary market-data provider is optional and must be explicitly configured by the caller. The service does not silently choose another exchange.
- Docker Compose configuration is validated in CI, but a full deployment against real hosted infrastructure still needs an operator-run acceptance test.
- Paper results and AI summaries do not prove future performance.
- The live exchange path in the legacy broker bridge is not reviewed, not validated, and is not enabled by the Compose deployment. Keep `PAPER_TRADE=true`.
- AYUAI results are informational only. They do not place paper or live orders.
