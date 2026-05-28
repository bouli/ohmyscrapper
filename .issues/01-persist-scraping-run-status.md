# Persist scraping run status

## What to build

Persist a durable scraping run record whenever `ohmyscrapper start` or `ohmyscrapper scrap-urls` begins work. Each run should expose status, timestamps, URL totals, completed counts, skipped counts, and failure counts so later CLI and dashboard features can report progress from the same source of truth.

## Acceptance criteria

- [x] Starting a scraping command creates a run record with a stable identifier and `running` status.
- [x] Completed, failed, and interrupted runs update their final status and timestamps.
- [x] Scraping progress updates durable counters that can be read after the process exits.
- [x] Existing scraping behavior and exports continue to work without requiring a new command flag.
- [x] Tests cover run creation, status updates, and counter updates.

## Blocked by

None - can start immediately
