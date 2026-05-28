from unittest.mock import Mock

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


def test_get_driver_reports_browser_startup_errors(monkeypatch):
    chrome = Mock(side_effect=Exception("binary missing"))

    patch_browser_config(monkeypatch, {"use-browser": "chrome"})
    monkeypatch.setattr(browser.webdriver, "Chrome", chrome)

    with pytest.raises(RuntimeError, match="Unable to start chrome browser"):
        browser.get_driver()
