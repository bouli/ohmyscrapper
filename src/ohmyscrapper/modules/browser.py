from collections import defaultdict
from threading import Condition

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


def _as_positive_int(value, default):
    if value is None or isinstance(value, bool):
        return default
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid sniffing.browser-pool-size: {value!r}") from exc
    if value < 1:
        raise ValueError("Invalid sniffing.browser-pool-size: must be >= 1")
    return value


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


def build_options(browser_name=None, proxy=None):
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

    if proxy is not None and browser_name not in {"safari", "ie"}:
        _add_argument(options, f"--proxy-server={proxy}")

    return options


def get_driver(proxy=None):
    browser_name = get_configured_browser_name()
    options = build_options(browser_name, proxy=proxy)

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


def get_browser_pool_size():
    return _as_positive_int(_get_sniffing_value("browser-pool-size", 1), 1)


class BrowserPool:
    def __init__(self, max_size=None, driver_factory=None):
        default_size = get_browser_pool_size()
        self.max_size = _as_positive_int(max_size, default_size)
        self.driver_factory = driver_factory if driver_factory is not None else get_driver
        self._available = defaultdict(list)
        self._total_drivers = 0
        self._closed = False
        self._condition = Condition()

    @property
    def total_drivers(self):
        with self._condition:
            return self._total_drivers

    def acquire(self, proxy=None):
        with self._condition:
            if self._closed:
                raise RuntimeError("browser pool is closed")

            key = self._pool_key(proxy)
            if self._available[key]:
                return self._available[key].pop()

            while self._total_drivers >= self.max_size:
                if self._close_one_idle_driver_locked():
                    break
                self._condition.wait()

            self._total_drivers += 1

        try:
            if proxy is None:
                return self.driver_factory()
            return self.driver_factory(proxy=proxy)
        except Exception:
            with self._condition:
                self._total_drivers -= 1
                self._condition.notify_all()
            raise

    def release(self, driver, proxy=None):
        if driver is None:
            return

        with self._condition:
            if self._closed:
                self._total_drivers -= 1
                should_quit = True
            else:
                self._available[self._pool_key(proxy)].append(driver)
                should_quit = False
            self._condition.notify_all()

        if should_quit:
            self._quit_driver(driver)

    def close_all(self):
        with self._condition:
            self._closed = True
            available_drivers = [
                driver
                for drivers in self._available.values()
                for driver in drivers
            ]
            self._available.clear()
            self._total_drivers -= len(available_drivers)
            self._condition.notify_all()

        for driver in available_drivers:
            self._quit_driver(driver)

    def _close_one_idle_driver_locked(self):
        for key, drivers in list(self._available.items()):
            if drivers:
                driver = drivers.pop()
                self._total_drivers -= 1
                if len(drivers) == 0:
                    self._available.pop(key, None)
                break
        else:
            return False

        self._condition.release()
        try:
            self._quit_driver(driver)
        finally:
            self._condition.acquire()
        return True

    def _pool_key(self, proxy):
        return proxy or "__default__"

    def _quit_driver(self, driver):
        if hasattr(driver, "quit"):
            try:
                driver.quit()
            except Exception:
                pass
