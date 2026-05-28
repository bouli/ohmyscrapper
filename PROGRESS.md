# Progress

## 2026-05-29 00:45 UTC

- Completed `.issues/08-add-local-dashboard-for-scraping-jobs.md`.
- Added `ohmyscrapper dashboard` with configurable local host and port.
- Added a stdlib HTTP dashboard that lists persisted scraping runs and renders run detail counters with recent URL scrape errors.
- Added a URL-manager query for recent active URL errors so the dashboard uses existing persisted scraping data.
- Documented the dashboard command in `README.md`.
- Added tests for dashboard data reads, rendered run states, error ordering, and CLI dashboard routing.

## 2026-05-28 22:27 UTC

- Completed `.issues/07-introduce-optional-queue-backed-scraping-worker.md`.
- Added optional Celery/Redis queue support through `scrap-urls --queue`, while keeping local CLI scraping as the default path.
- Added a queue worker module that creates persisted scraping runs, enqueues work, and runs workers through the existing `scrap_urls(..., run_id=...)` flow so progress updates the same `scraping_runs` table.
- Documented queue defaults in the generated configuration and added an optional `queue` dependency extra.
- Added tests for enqueue behavior, worker task execution, missing Celery dependency reporting, and CLI queue routing.
- Verification: `uv run pytest` passed with 153 tests.

## 2026-05-29 00:25 UTC

- Completed `.issues/06-add-bounded-browser-pool-for-concurrent-scraping.md`.
- Added configurable `sniffing.browser-pool-size` with validation and default size `1`.
- Added a bounded `BrowserPool` that reuses compatible browser instances, evicts idle browsers when the pool is full, releases failed startup capacity, and closes all idle or returned browsers during cleanup.
- Routed browser-backed scraping through the pool so each URL borrows and returns a browser while preserving externally supplied drivers.
- Added tests for pool sizing, acquisition, release, bounded eviction, cleanup after run close, and startup failure capacity recovery.
- Verification: `uv run pytest` passed with 149 tests.

## 2026-05-28 22:20 UTC

- Completed `.issues/05-apply-proxy-rotation-to-scraping-requests.md`.
- Added optional `sniffing.proxies` configuration and round-robin proxy selection for scraping.
- Threaded selected proxies through sniffing requests and browser startup, including Selenium proxy arguments for supported browsers.
- Added proxy failure context so proxy connection errors are recorded by the existing scrape failure path.
- Added tests for proxy rotation, request proxy kwargs, browser proxy options, and proxy error context.
- Verification: `uv run pytest` passed with 144 tests.

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
