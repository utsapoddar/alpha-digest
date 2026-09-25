# Design Walkthrough

## Overview

Alpha Digest is a scheduled investor-research pipeline. It collects SEC filings, crypto-treasury data, commodity moves, and financial news for 25 tracked entities. It joins that evidence, sends a bounded payload through a cross-provider model chain, then renders and distributes one email and one archived web issue. GitHub Actions runs it every Monday.

## Reliability history

The first model setup was too fragile. A token cap truncated JSON, a pinned model was retired, and provider-level outages stopped scheduled issues. The replacement uses pinned models across Gemini and NVIDIA, explicit transient and permanent error handling, and a workflow timeout sized from the real retry path. The README's Reliability section has the timeline.

Where to verify it:

- `digest/summarizer.py` contains the ordered provider chain and error classes.
- `.github/workflows/weekly-digest.yml` documents the time budget.
- GitHub Actions history shows the scheduled runs.
- The `gh-pages` archive shows the published output.

## Design rationale

### Why use an LLM here?

The source records are heterogeneous. Form 4 trades, 13F holdings, price changes, and headlines need a common plain-English presentation. The model handles that compression after deterministic collection and enrichment. It does not choose sources or browse freely.

### How are hallucinations limited?

The prompt restricts the model to supplied fields and URLs, requires JSON, asks for neutral language, and tells it to state when context is missing. Those controls reduce unsupported text; they do not prove every sentence. The published digest is a research aid, not financial advice.

### What happens when a provider fails?

Transient errors retry on the same model with bounded backoff. Permanent API errors move to the next provider. If every provider fails, the run stops before rendering, rather than publishing a fabricated fallback.

### Why publish static HTML?

The product updates weekly and has no interactive server-side feature. Static GitHub Pages output has a small operating surface, keeps old issues addressable, and makes deployment state visible.

## Next improvements

1. Add contract tests for every fetcher with stored source fixtures.
2. Validate the complete model-response schema before rendering.
3. Add source citations beside each generated claim instead of only attaching related news URLs.
4. Record per-source freshness and coverage metrics in the issue.
5. Alert on a missed Monday run rather than relying on manual Actions inspection.

## Boundaries

- A 13F report describes past holdings and arrives after the reporting period.
- RSS and news search can miss context or surface duplicates.
- A provider fallback improves availability, not factual accuracy.
- Current automated tests focus on the summarizer. The fetchers and publisher need broader fixture coverage.
- The system produces research summaries. It does not forecast returns or generate trade instructions.
