# ai-news-aggregator1

Tracks shopping and skincare brands (H&M, Oh Polly, skincare brands, ...), scraping
their sites and reading promotional Gmail messages for offers/new releases, storing
everything in Postgres. Once a day it builds an LLM-written digest (Groq / Llama)
of the last 24h of offers -- short snippets with links back to the source -- and
emails it to your inbox.

## Project layout

```
src/app/
├── main.py            # orchestration entrypoint (init db -> scrape -> gmail -> digest -> email)
├── config.py           # env-based settings (pydantic-settings)
├── prompts/            # the "user insight" system prompt fed to Claude
├── db/                 # SQLAlchemy models, engine/session, create_tables script
├── seed/                # starter list of tracked sources + idempotent seed script
├── scrapers/             # requests+BeautifulSoup scraper, config-driven per source
├── gmail_ingest/           # Gmail API (OAuth) promo-email ingestion
├── llm/                     # Claude API wrapper for digest summarization
└── digest/                   # builds the daily digest, renders + sends the email
docker/
├── docker-compose.yml   # local Postgres for development
└── Dockerfile           # app image, used for the Render cron deployment
```

## Setup

1. **Install dependencies** (uv-managed project):
   ```bash
   uv sync
   ```

2. **Start local Postgres:**
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
   Runs on `localhost:5433` (not 5432) to avoid clashing with any Postgres you
   already have installed locally.

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Fill in `DATABASE_URL` (already correct if you used the compose file above),
   and whichever of these you're ready to set up (see "Optional integrations"
   below) -- `GROQ_API_KEY`, the Gmail OAuth credentials, and SMTP creds.

4. **Create the database tables:**
   ```bash
   uv run python -m app.db.create_tables
   ```

5. **Seed tracked sources:**
   ```bash
   uv run python -m app.seed.seed_sources
   ```
   Ships with H&M, Oh Polly, and two placeholder skincare brands. Edit
   `src/app/seed/sources_seed.py` to add/remove brands or fix scrape selectors
   (marked `# TODO` where they're unverified against live HTML) -- re-run the
   seed script any time, it's idempotent (upserts by name).

## Running the pipeline

Run everything end to end:
```bash
uv run ai-news-aggregator1
```

Or run each stage independently:
```bash
uv run python -m app.scrapers.run_all        # scrape active sources, dedupe, insert offers
uv run python -m app.gmail_ingest.run_ingest # ingest recent promo emails (needs Gmail creds)
uv run python -m app.digest.builder          # build/reuse today's digest from the last 24h
uv run python -m app.digest.mailer <digest_id>  # send a specific digest by id
```

Every stage is safe to re-run: scraping dedupes by a hash of source+url+title, the
digest builder reuses the existing digest for the current date instead of
duplicating it, and Gmail ingestion skips messages it's already processed.

To force a fresh digest rebuild on the same day:
```bash
docker exec docker-postgres-1 psql -U app -d ai_news -c "DELETE FROM digest_item; DELETE FROM digest;"
uv run python -m app.digest.builder
```

## Optional integrations

Each of these degrades gracefully when not configured -- the rest of the pipeline
keeps working without it.

**LLM digest summaries (Groq / Llama 3.3 70B)** -- without `GROQ_API_KEY` set, the
digest builder falls back to a deterministic `"{title} — {discount_text}"` summary
per offer instead of an LLM-written one. Get a key at [console.groq.com](https://console.groq.com).

**Gmail promo email ingestion** -- requires a Google Cloud OAuth client:
1. Create/select a project at [console.cloud.google.com](https://console.cloud.google.com), enable the Gmail API.
2. Configure the OAuth consent screen (External is fine for personal use; add yourself as a test user).
3. Create OAuth credentials, type **Desktop app**, download the JSON.
4. Save it as `credentials/gmail_credentials.json` (gitignored).
5. Run `uv run python -m app.gmail_ingest.run_ingest` -- it opens a browser for a
   one-time sign-in/consent, then refreshes silently afterward.

**Sending the digest email** -- requires SMTP credentials, e.g. a Gmail app
password:
1. Enable 2-Step Verification on the sending Gmail account.
2. Google Account -> Security -> App passwords -> generate one for "Mail".
3. Set `SMTP_USERNAME` and `SMTP_PASSWORD` in `.env`, plus `DIGEST_RECIPIENT_EMAIL`.

## Deploying to Render (daily cron)

The pipeline runs as a scheduled Render **Cron Job** built from `docker/Dockerfile`,
driven by the `render.yaml` blueprint at the repo root. On every run it also
creates tables and seeds sources itself (idempotent), so a brand-new database
bootstraps automatically on the first firing -- no manual setup step needed
beyond creating the database and setting env vars.

**Gmail ingestion is intentionally disabled in this deployment** (`ENABLE_GMAIL_INGESTION=false`
in `render.yaml`) -- its OAuth token expires roughly weekly while the app stays in
Google's "Testing" publish status, and the browser-based re-consent can't run
unattended on a server. Keep running `uv run python -m app.gmail_ingest.run_ingest`
locally/manually whenever you want to refresh promo-email offers; the cron job
still handles scraping, digest building, and sending the email every day.

### 1. Create a free Postgres database (Neon)

1. Sign up at [neon.tech](https://neon.tech) (free tier).
2. Create a project, then a database (or use the default one).
3. Copy the connection string from the dashboard and adapt it to this app's
   driver: it should look like
   `postgresql+psycopg://<user>:<password>@<host>/<dbname>?sslmode=require`
   (Neon requires SSL; note the `+psycopg` after `postgresql`, which Neon's
   copy-paste string won't include by default).

### 2. Push this repo to GitHub

Render deploys from a connected git repo:
```bash
git init   # if not already a repo
git add .
git commit -m "Initial commit"
gh repo create ai-news-aggregator1 --private --source=. --push
```
(or create the GitHub repo manually and `git push` to it).

### 3. Create a Render account and deploy the blueprint

1. Sign up at [render.com](https://render.com).
2. Dashboard -> **New** -> **Blueprint** -> connect the GitHub repo you just pushed.
3. Render reads `render.yaml` and proposes a Cron Job service named
   `ai-news-aggregator1` -- click through to create it.
4. Before (or right after) the first run, go to the service's **Environment**
   tab and fill in the secret env vars `render.yaml` left blank
   (`sync: false`): `DATABASE_URL` (from step 1), `GROQ_API_KEY`,
   `SMTP_USERNAME`, `SMTP_PASSWORD`, `DIGEST_RECIPIENT_EMAIL`.
5. The schedule in `render.yaml` (`0 14 * * *`, i.e. 14:00 UTC / 7am Arizona)
   can be changed from the Render dashboard's **Settings** tab, or by editing
   `render.yaml` and pushing.

### 4. Verify

Trigger a manual run from the Render dashboard (cron job services have a
"Trigger Run" button) and check the **Logs** tab -- it should show the same
init -> scrape -> digest -> email sequence you've seen locally, and an email
should land in your inbox.

## Future work

- Scrapers use plain `requests` + BeautifulSoup, which can't execute
  client-side JavaScript or get past bot-detection (H&M, Sephora, Zara, Urban
  Outfitters, and Victoria's Secret are all currently blocked -- documented
  with the specific reason in `src/app/seed/sources_seed.py`) -- fixing these
  would mean adding a headless-browser engine (e.g. Playwright, ideally with
  stealth plugins) as a per-source fallback.
- Getting the Gmail OAuth app out of Google's "Testing" publish status (via
  their verification process) would remove the weekly token-expiry limitation
  and let Gmail ingestion run unattended in the cron job too.
