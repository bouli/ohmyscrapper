# Progress

## 2026-05-28 21:31 Europe/Berlin

- Completed `.issues/01-persist-scraping-run-status.md`.
- Added durable `scraping_runs` persistence with run creation, retrieval, total updates, counter increments, and final status updates.
- Wired `scrap_urls` and `start` scraping flows to create and update run records without adding a user-facing flag.
- Added tests for scraping run lifecycle, invalid status/counter validation, CLI start metadata, and scraping counter updates.
- Verification: `uv run pytest` passed with 127 tests.

## 2026-05-29 00:03 Europe/Berlin

- Completed `.issues/02-show-progress-during-long-cli-runs.md`.
- Added persisted scraping run progress formatting and output during `scrap-urls` processing.
- Reused the same `scrap_urls` flow for `start`, so progress appears when the start pipeline reaches scraping.
- Added tests for progress formatting, persisted progress reads, and deterministic progress output without terminal UI timing.
- Verification: `uv run pytest` passed with 130 tests.
