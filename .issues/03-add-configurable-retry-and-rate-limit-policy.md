# Add configurable retry and rate-limit policy

## What to build

Add configuration-driven delays and retry behavior for scraping requests. Failed scrapes should be retried according to policy, rate limits should slow request cadence predictably, and final errors should still be recorded clearly for later reporting.

## Acceptance criteria

- [ ] Scraping delay, retry count, and retry backoff can be configured through the existing configuration system.
- [ ] Retryable failures are retried before being marked as failed.
- [ ] Final failure details remain available in the URL database or scraping result state.
- [ ] Default settings preserve the current quick local development workflow.
- [ ] Tests cover configured delay policy, retry success, and retry exhaustion.

## Blocked by

None - can start immediately
