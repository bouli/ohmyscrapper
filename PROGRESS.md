# Progress

## 2026-05-28 21:31 UTC

- Completed `.issues/01-persist-scraping-run-status.md`.
- Added durable `scraping_runs` persistence with run creation, retrieval, total updates, counter increments, and final status updates.
- Wired `scrap_urls` and `start` scraping flows to create and update run records without adding a user-facing flag.
- Added tests for scraping run lifecycle, invalid status/counter validation, CLI start metadata, and scraping counter updates.
- Verification: `uv run pytest` passed with 127 tests.

## 2026-05-29 00:03 UTC

- Completed `.issues/02-show-progress-during-long-cli-runs.md`.
- Added persisted scraping run progress formatting and output during `scrap-urls` processing.
- Reused the same `scrap_urls` flow for `start`, so progress appears when the start pipeline reaches scraping.
- Added tests for progress formatting, persisted progress reads, and deterministic progress output without terminal UI timing.
- Verification: `uv run pytest` passed with 130 tests.

## 2026-05-29 00:10 UTC

- Completed `.issues/03-add-configurable-retry-and-rate-limit-policy.md`.
- Added configurable scraping request delay, retry count, and retry backoff under the existing `sniffing` config section.
- Preserved old config compatibility by falling back to quick default delay/retry values when the new keys are absent.
- Added retry handling in `scrap_url` so retryable sniffing failures are retried before the final error is recorded on the URL.
- Added tests for configured delay policy, retry success, and retry exhaustion.
- Verification: `uv run pytest` passed with 133 tests.

## 2026-05-28 22:16 UTC

- Completed `.issues/04-support-headless-browser-runtime-configuration.md`.
- Added config-driven browser runtime mapping for headless mode, Docker/Kubernetes-friendly Chrome arguments, and custom browser arguments.
- Preserved existing local non-headless browser behavior while defaulting unknown/true browser settings to Chrome.
- Improved browser startup error reporting so scraping records the affected URL when a browser cannot start.
- Added tests for browser option mapping, startup error wrapping, sniff URL startup errors, and scrape failure recording.
- Verification: `uv run pytest` passed with 138 tests.
