# Introduce optional queue-backed scraping worker

## What to build

Introduce Celery and Redis as an optional execution mode for distributed scraping. Users should be able to enqueue scraping work and run workers without losing the existing local CLI flow.

## Acceptance criteria

- [x] Queue-backed execution is optional and local CLI scraping remains the default.
- [x] A scraping run can be enqueued and processed by a worker.
- [x] Worker progress updates the same persisted run status used by local scraping.
- [x] Queue and Redis configuration are documented in project configuration defaults.
- [x] Tests cover enqueue behavior and worker task execution with fakes or test doubles.

## Blocked by

- [01-persist-scraping-run-status.md](01-persist-scraping-run-status.md)
- [03-add-configurable-retry-and-rate-limit-policy.md](03-add-configurable-retry-and-rate-limit-policy.md)
