# Large insider trades — approved SEC-backed source adjustment

User approved US$1 million or more per individual insider purchase or sale.
Do not apply this threshold to unrelated news, commodities or quarterly holdings.

## Source constraint
Google Finance prohibits copying and redistribution without written consent.
OpenInsider permits personal transitory viewing but forbids public display and
mirroring. Alpha Digest publishes a public archive, so copying their data into
that archive is not the approved implementation path. User approved the source adjustment on 2026-10-08: use SEC Form 4 as the underlying data and include Google Finance
and OpenInsider links for reader verification. Do not quietly represent links
as completed automated ingestion of those sites.

## Proposed ingestion
Extend SEC discovery beyond the existing watchlist so large trades elsewhere are
not missed. Fetch original filings with bounded requests; preserve filing URL,
transaction date, filing date, issuer ticker, reporting owner, P/S transaction
code, quantity and price. Calculate value per transaction, never per cluster.
Keep only known values at or above the threshold and deduplicate against existing
watchlist records using accession and transaction identity. Unknown prices do
not establish a large trade. Separate amended/late disclosures from trade dates.

## Output and verification
Supply source-grounded large-trade evidence to the summarizer and render source
links in email and web output. Preserve the existing schedule and delivery path.
Tests cover the threshold boundary, purchases and sales, non-P/S exclusions,
unknown prices, duplicate discovery, date distinctions and rendered links.
A live bounded SEC fetch and rendered sample are required before completion.
Similar aggregators should not be added merely to duplicate the same filings;
select another source only when it provides a distinct, permitted contribution.

## Final source selection — 2026-10-08

User approved SEC ingestion, existing Yahoo market context, and optional
OpenInsider exploration links. Remove Google Finance links from both editions.
Do not add aggregator ingestion, new signals, or alter schedules in this change.
