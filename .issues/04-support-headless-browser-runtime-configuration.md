# Support headless browser runtime configuration

## What to build

Make browser execution explicitly configurable for local, Docker, and Kubernetes-style environments. The scraping flow should be able to run browser-backed pages in headless mode without requiring ad hoc code changes.

## Acceptance criteria

- [ ] Headless browser mode can be enabled through configuration and/or CLI options consistent with existing project patterns.
- [ ] Browser setup supports container-friendly options needed for Docker or Kubernetes execution.
- [ ] Existing non-headless local browser behavior remains available.
- [ ] Browser startup errors are reported clearly and do not obscure the URL being processed.
- [ ] Tests cover the browser configuration mapping without requiring a real remote browser.

## Blocked by

None - can start immediately
