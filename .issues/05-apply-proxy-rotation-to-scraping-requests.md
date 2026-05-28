# Apply proxy rotation to scraping requests

## What to build

Add proxy pool configuration and apply proxy selection consistently across scraping requests. The feature should reduce repeated requests from the same network path while keeping failures visible when a proxy cannot be used.

## Acceptance criteria

- [ ] A list of proxies can be configured using the existing configuration system.
- [ ] Scraping requests select proxies from the configured pool.
- [ ] Browser-backed scraping receives compatible proxy settings when enabled.
- [ ] Proxy connection failures are recorded as scrape failures with useful context.
- [ ] Tests cover proxy selection and request/browser configuration behavior.

## Blocked by

- [04-support-headless-browser-runtime-configuration.md](04-support-headless-browser-runtime-configuration.md)
