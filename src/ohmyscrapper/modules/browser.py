from selenium import webdriver

from ohmyscrapper.core.config import get_sniffing


CONTAINER_BROWSER_ARGUMENTS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]


def _get_sniffing_value(param, default=None):
    try:
        return get_sniffing(param)
    except Exception:
        return default


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [value]


def get_configured_browser_name():
    configured_browser = _get_sniffing_value("use-browser", "chrome")
    if isinstance(configured_browser, bool):
        return "chrome"
    if configured_browser is None:
        return "chrome"

    configured_browser = str(configured_browser).strip().lower()
    if configured_browser in {"", "true", "yes", "on", "1"}:
        return "chrome"
    return configured_browser


def _add_argument(options, argument):
    if hasattr(options, "add_argument"):
        options.add_argument(argument)


def build_options(browser_name=None):
    if browser_name is None:
        browser_name = get_configured_browser_name()

    if browser_name == "safari":
        from selenium.webdriver.safari.options import Options
    elif browser_name == "firefox":
        from selenium.webdriver.firefox.options import Options
    elif browser_name == "ie":
        from selenium.webdriver.ie.options import Options
    else:
        from selenium.webdriver.chrome.options import Options

    options = Options()
    if _as_bool(_get_sniffing_value("browser-headless", False)):
        if browser_name == "firefox":
            _add_argument(options, "-headless")
        elif browser_name not in {"safari", "ie"}:
            _add_argument(options, "--headless=new")

    if (
        browser_name not in {"firefox", "safari", "ie"}
        and _as_bool(_get_sniffing_value("browser-container-options", False))
    ):
        for argument in CONTAINER_BROWSER_ARGUMENTS:
            _add_argument(options, argument)

    for argument in _as_list(_get_sniffing_value("browser-arguments", [])):
        _add_argument(options, argument)

    return options


def get_driver():
    browser_name = get_configured_browser_name()
    options = build_options(browser_name)

    try:
        if browser_name == "safari":
            driver = webdriver.Safari(options=options)
        elif browser_name == "firefox":
            driver = webdriver.Firefox(options=options)
        elif browser_name == "ie":
            driver = webdriver.Ie(options=options)
        else:  # default: chrome
            driver = webdriver.Chrome(options=options)
    except Exception as exc:
        raise RuntimeError(f"Unable to start {browser_name} browser: {exc}") from exc

    return driver
