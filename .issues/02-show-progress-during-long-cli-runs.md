# Show progress during long CLI runs

## What to build

Show live progress for long `scrap-urls` and `start` runs using the persisted scraping run counters. The CLI should make long-running work observable without changing the existing command flow or output files.

## Acceptance criteria

- [x] `ohmyscrapper scrap-urls` displays progress while URLs are being processed.
- [x] `ohmyscrapper start` displays progress across scraping work when it reaches that stage.
- [x] Progress output reflects completed, skipped, and failed URLs from the persisted run state.
- [x] Non-interactive or test execution remains stable and does not require a terminal UI.
- [x] Tests cover progress reporting behavior without depending on timing-sensitive output.

## Blocked by

- [01-persist-scraping-run-status.md](01-persist-scraping-run-status.md)
