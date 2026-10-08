# Large insider sources implementation plan

Goal: show SEC-sourced individual US$1M+ purchases/sales with approved reference links.
Architecture: bounded global SEC discovery, shared Form 4 parsing, de-duplication,
then enrichment and deterministic email/web rendering. No copied aggregator data.
Tech: Python, requests, ElementTree, Decimal, Jinja2, pytest.

- [x] Write failing tests in tests/test_large_insiders.py and verify missing fetcher.
- [x] Implement digest/fetchers/large_insiders.py; register and enable the source.
- [x] Extend shared parser with ticker, owner, transaction date/index and finite Decimal amounts.
- [x] Wire main.py into enrichment and render exact trade data outside generated prose.
- [x] Add templates/large_insiders.html.j2 to both outputs with coverage and source links.
- [x] Run full pytest (13 pass), targeted py_compile and a live 20-filing SEC check (4 qualifying trades).
- [x] Deployed only these changes atop current remote main, preserving unrelated local changes.

Production source verified at 26874ca on remote main; weekly workflow is active and its schedule is unchanged. No manual production email/publication run was triggered.
