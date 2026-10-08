# Large insider disclosures

The enabled `large_insiders` source uses original SEC Form 4 filings, not copied
aggregator data. It inspects at most 200 filings from the newest 200 current-feed
entries per run with a 180-second source budget, and retains individual P/S transactions worth US$1 million or
more. This is bounded discovery, not an exhaustive weekly market screen; the
email and web editions display the inspection limits and retrieval failures.
Trade dates and filing dates are shown separately, including late disclosures.
Unknown or non-finite prices cannot establish a qualifying trade. Original
transaction-row indices preserve distinct identical-sized trades; overlapping
watchlist and global discovery records are deduplicated.

Google Finance is a reference-tool link. OpenInsider and Finviz have reference
links per ticker. Their data is not copied into the public archive. Source
figures and these links render deterministically, independent of generated prose.
Existing commodity, crypto, news and 13F sources remain unchanged.

Verification on 2026-10-08: 13 tests passed, including source registration,
threshold boundaries, buys/sells, invalid prices, duplicate handling, both HTML
outputs and the main dry-run path. A bounded live SEC check inspected 20 filings,
with zero retrieval failures, and found four qualifying COE purchases. These are
recent disclosures; their trade dates may be older. No email was sent and no
public issue was replaced during local verification.
