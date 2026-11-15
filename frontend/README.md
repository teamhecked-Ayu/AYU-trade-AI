# AYU Trade AI dashboard

The static dashboard contains two separate areas:

- **AYUAI workspace:** create an account, sign in, save encrypted provider keys, submit analysis questions, review independent provider responses, reasoning, debate, final confidence and saved decision history.
- **Paper portfolio:** connect with the separate `AYU_API_KEY` and use manual simulated paper orders. AYUAI analysis does not submit orders.

## Run locally

1. Copy `.env.example` to `.env` and set strong, separate values for `AYU_API_KEY`, `AYUAI_AUTH_SECRET`, and `AYUAI_KEY_VAULT_SECRET`.
2. Configure at least one provider key in `.env` or save a user-owned key in the dashboard.
3. Start the API, database, Redis and Celery worker with `docker compose up --build`.
4. Serve this folder with `python -m http.server 8080 --directory frontend`.
5. Open `http://localhost:8080` and connect to `http://localhost:8000`.

For local non-Docker development, set `AYUAI_RATE_LIMIT_BACKEND=memory`. For Docker Compose, Redis is used for a shared API rate limit.

## Security notes

- AYUAI session tokens remain in page memory and are not saved to browser storage.
- Provider keys are encrypted server-side with `AYUAI_KEY_VAULT_SECRET`; the dashboard clears the key field after saving.
- The API only allows configured browser origins through `AYUAI_CORS_ORIGINS`.
- The paper API key is kept in page memory only.
- Keep `PAPER_TRADE=true`. AI analysis is informational and does not place trades.
