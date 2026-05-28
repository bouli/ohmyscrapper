from unittest.mock import Mock, call

import pytest
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.ie.options import Options as IeOptions
from selenium.webdriver.safari.options import Options as SafariOptions

from ohmyscrapper.modules import browser


def patch_browser_config(monkeypatch, values):
    monkeypatch.setattr(
        browser,
        "get_sniffing",
        Mock(side_effect=lambda key: values.get(key)),
    )


@pytest.mark.parametrize(
    ("configured_browser", "webdriver_name", "options_type"),
    [
        ("safari", "Safari", SafariOptions),
        ("firefox", "Firefox", FirefoxOptions),
        ("ie", "Ie", IeOptions),
    ],
)
def test_get_driver_uses_configured_browser(
    monkeypatch,
    configured_browser,
    webdriver_name,
    options_type,
):
    driver = Mock(name=f"{webdriver_name}Driver")
    webdriver_constructor = Mock(return_value=driver)

    patch_browser_config(monkeypatch, {"use-browser": configured_browser})
    monkeypatch.setattr(browser.webdriver, webdriver_name, webdriver_constructor)

    result = browser.get_driver()

    assert result is driver
    webdriver_constructor.assert_called_once()
    assert isinstance(webdriver_constructor.call_args.kwargs["options"], options_type)


@pytest.mark.parametrize("configured_browser", ["chrome", "", None, "unknown"])
def test_get_driver_defaults_to_chrome(monkeypatch, configured_browser):
    driver = Mock(name="ChromeDriver")
    chrome = Mock(return_value=driver)

    patch_browser_config(monkeypatch, {"use-browser": configured_browser})
    monkeypatch.setattr(browser.webdriver, "Chrome", chrome)

    result = browser.get_driver()

    assert result is driver
    chrome.assert_called_once()
    assert isinstance(chrome.call_args.kwargs["options"], ChromeOptions)


def test_build_options_maps_headless_and_container_arguments_for_chrome(monkeypatch):
    patch_browser_config(
        monkeypatch,
        {
            "browser-headless": True,
            "browser-container-options": True,
            "browser-arguments": ["--window-size=1200,900"],
        },
    )

    options = browser.build_options("chrome")

    assert isinstance(options, ChromeOptions)
    assert "--headless=new" in options.arguments
    assert "--no-sandbox" in options.arguments
    assert "--disable-dev-shm-usage" in options.arguments
    assert "--disable-gpu" in options.arguments
    assert "--window-size=1200,900" in options.arguments


def test_build_options_maps_headless_for_firefox(monkeypatch):
    patch_browser_config(
        monkeypatch,
        {
            "browser-headless": "yes",
            "browser-container-options": True,
            "browser-arguments": "--width=1200,--height=900",
        },
    )

    options = browser.build_options("firefox")

    assert isinstance(options, FirefoxOptions)
    assert "-headless" in options.arguments
    assert "--width=1200" in options.arguments
    assert "--height=900" in options.arguments
    assert "--no-sandbox" not in options.arguments


def test_build_options_adds_proxy_argument_for_browser(monkeypatch):
    patch_browser_config(monkeypatch, {})

    options = browser.build_options("chrome", proxy="http://proxy-1:8080")

    assert "--proxy-server=http://proxy-1:8080" in options.arguments


def test_get_driver_reports_browser_startup_errors(monkeypatch):
    chrome = Mock(side_effect=Exception("binary missing"))

    patch_browser_config(monkeypatch, {"use-browser": "chrome"})
    monkeypatch.setattr(browser.webdriver, "Chrome", chrome)

    with pytest.raises(RuntimeError, match="Unable to start chrome browser"):
        browser.get_driver()


def test_get_browser_pool_size_reads_configured_value(monkeypatch):
    patch_browser_config(monkeypatch, {"browser-pool-size": "3"})

    assert browser.get_browser_pool_size() == 3


def test_browser_pool_reuses_released_driver_for_same_proxy():
    driver = Mock(name="driver")
    driver_factory = Mock(return_value=driver)
    pool = browser.BrowserPool(max_size=2, driver_factory=driver_factory)

    first = pool.acquire(proxy="http://proxy-1:8080")
    pool.release(first, proxy="http://proxy-1:8080")
    second = pool.acquire(proxy="http://proxy-1:8080")

    assert second is driver
    driver_factory.assert_called_once_with(proxy="http://proxy-1:8080")
    assert pool.total_drivers == 1

    pool.release(second, proxy="http://proxy-1:8080")
    pool.close_all()
    driver.quit.assert_called_once_with()


def test_browser_pool_evicts_idle_driver_when_pool_is_full():
    first_driver = Mock(name="first_driver")
    second_driver = Mock(name="second_driver")
    driver_factory = Mock(side_effect=[first_driver, second_driver])
    pool = browser.BrowserPool(max_size=1, driver_factory=driver_factory)

    first = pool.acquire(proxy="http://proxy-1:8080")
    pool.release(first, proxy="http://proxy-1:8080")
    second = pool.acquire(proxy="http://proxy-2:8080")

    assert second is second_driver
    assert pool.total_drivers == 1
    assert driver_factory.call_args_list == [
        call(proxy="http://proxy-1:8080"),
        call(proxy="http://proxy-2:8080"),
    ]
    first_driver.quit.assert_called_once_with()

    pool.release(second, proxy="http://proxy-2:8080")
    pool.close_all()
    second_driver.quit.assert_called_once_with()


def test_browser_pool_closes_released_driver_after_close_all():
    driver = Mock(name="driver")
    pool = browser.BrowserPool(max_size=1, driver_factory=Mock(return_value=driver))

    acquired_driver = pool.acquire()
    pool.close_all()
    pool.release(acquired_driver)

    driver.quit.assert_called_once_with()
    assert pool.total_drivers == 0


def test_browser_pool_releases_capacity_when_driver_start_fails():
    driver = Mock(name="driver")
    driver_factory = Mock(side_effect=[RuntimeError("missing"), driver])
    pool = browser.BrowserPool(max_size=1, driver_factory=driver_factory)

    with pytest.raises(RuntimeError, match="missing"):
        pool.acquire()

    assert pool.total_drivers == 0
    acquired_driver = pool.acquire()
    assert acquired_driver is driver
    pool.release(acquired_driver)
    pool.close_all()
