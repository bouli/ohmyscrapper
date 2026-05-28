# Support headless browser runtime configuration

## What to build

Make browser execution explicitly configurable for local, Docker, and Kubernetes-style environments. The scraping flow should be able to run browser-backed pages in headless mode without requiring ad hoc code changes.

## Acceptance criteria

- [x] Headless browser mode can be enabled through configuration and/or CLI options consistent with existing project patterns.
- [x] Browser setup supports container-friendly options needed for Docker or Kubernetes execution.
- [x] Existing non-headless local browser behavior remains available.
- [x] Browser startup errors are reported clearly and do not obscure the URL being processed.
- [x] Tests cover the browser configuration mapping without requiring a real remote browser.

## Blocked by

None - can start immediately
