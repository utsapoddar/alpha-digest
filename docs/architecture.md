# Architecture

## System boundary

Alpha Digest is one scheduled Python process with external data, model, mail, and GitHub dependencies. It does not expose an API or maintain a server. GitHub Actions starts the process every Monday at 10:17 UTC.

## Data flow

### 1. Date window and configuration

`main.py` reads the last successful run boundary from the cached state file. If no state exists, it uses the previous seven days. `config/sources.yaml` controls which fetchers participate.

### 2. Collection

Fetcher modules return source-specific records:

- `sec_edgar.py` reads Form 4 insider transactions and 13F institutional holdings.
- `news.py` reads entity-specific Google News RSS results.
- `feeds.py` reads the configured publisher feeds and matches items to watched entities.
- `crypto.py` reads corporate crypto-treasury changes from CoinGecko.
- `commodities.py` computes weekly changes for gold, oil, and silver from Yahoo Finance.

Fetchers share one `requests.Session` for the run. The orchestration layer decides which source applies to each watchlist entity.

### 3. Enrichment

`digest/enrichers/context.py` joins filing records, treasury changes, and headlines by entity. The result separates insider trades, institutional holdings, crypto data, and supporting news before it reaches the model.

### 4. Structured summarization

`digest/summarizer.py` sends the enriched payload and commodity changes to an OpenAI-compatible endpoint. The model must return one JSON object with per-entity summaries and a macro note.

The provider chain is ordered and bounded:

1. `gemini-3.5-flash`
2. `gemini-3.1-flash-lite`
3. `nvidia/nemotron-3-super-120b-a12b`

Transient connection, timeout, rate-limit, server, malformed-JSON, and empty-response failures retry up to three times. Permanent API errors move directly to the next model. The SDK's internal retry loop is disabled so the pipeline owns the time budget.

### 5. Rendering and delivery

`digest/renderer.py` renders separate email and web documents from the same structured result. `digest/notifier.py` sends the email through Gmail SMTP. If mail configuration is missing or delivery fails, it saves the email HTML to `data/last_digest.html`.

`digest/publisher.py` clones the `gh-pages` branch into a temporary directory, writes the dated issue, rebuilds the archive index, and pushes one generated commit.

### 6. State

After delivery and publishing, the pipeline stores the end of the processed date window. GitHub Actions caches that state for the next scheduled run. SEC comparison snapshots also live under `data/cache`.

## Failure behavior

| Failure | Behavior |
|---|---|
| One model is rate-limited or times out | Retry with bounded exponential backoff |
| A model is unavailable or retired | Move to the next configured provider |
| Every model fails | Fail the workflow before publishing unsupported output |
| Email delivery fails | Save the generated email locally and continue to publishing |
| The published page has no content change | Skip the Git commit |
| Publishing fails | Log the Git error; the workflow artifact still preserves the rendered digest |

## Trust boundary

The model receives collected evidence, not unrestricted browsing access. Its output remains probabilistic. Source links, neutral language, and explicit non-advice wording reduce risk but do not replace human review.
