# Add bounded browser pool for concurrent scraping

## What to build

Add a bounded pool of browser instances for scraping workloads that need browser-backed access. The pool should improve throughput while keeping resource usage predictable and ensuring every browser instance is cleaned up.

## Acceptance criteria

- [ ] Browser pool size is configurable.
- [ ] Scraping work borrows browser instances from the pool and returns them after use.
- [ ] Browser instances are closed cleanly when a run completes or fails.
- [ ] Pool behavior is bounded so configured concurrency is not exceeded.
- [ ] Tests cover pool acquisition, release, cleanup, and failure paths without requiring real browsers.

## Blocked by

- [04-support-headless-browser-runtime-configuration.md](04-support-headless-browser-runtime-configuration.md)
