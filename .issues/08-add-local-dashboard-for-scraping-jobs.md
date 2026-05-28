# Add local dashboard for scraping jobs

## What to build

Add a minimal local web dashboard for monitoring scraping jobs. The dashboard should show recent runs, current status, progress counters, and recent errors using the persisted run data.

## Acceptance criteria

- [x] A local dashboard can be started from the project using a documented command.
- [x] The dashboard lists recent scraping runs with status, timestamps, and progress.
- [x] A run detail view shows counters and recent scrape errors.
- [x] Dashboard data comes from the same persisted run records used by CLI progress.
- [x] Tests cover the dashboard data path and at least one rendered run state.

## Blocked by

- [01-persist-scraping-run-status.md](01-persist-scraping-run-status.md)
- [02-show-progress-during-long-cli-runs.md](02-show-progress-during-long-cli-runs.md)
