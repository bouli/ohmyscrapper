from unittest.mock import Mock

import pytest
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.ie.options import Options as IeOptions
from selenium.webdriver.safari.options import Options as SafariOptions

from ohmyscrapper.modules import browser


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

    monkeypatch.setattr(browser, "get_sniffing", Mock(return_value=configured_browser))
    monkeypatch.setattr(browser.webdriver, webdriver_name, webdriver_constructor)

    result = browser.get_driver()

    assert result is driver
    browser.get_sniffing.assert_called_with("use-browser")
    webdriver_constructor.assert_called_once()
    assert isinstance(webdriver_constructor.call_args.kwargs["options"], options_type)


@pytest.mark.parametrize("configured_browser", ["chrome", "", None, "unknown"])
def test_get_driver_defaults_to_chrome(monkeypatch, configured_browser):
    driver = Mock(name="ChromeDriver")
    chrome = Mock(return_value=driver)

    monkeypatch.setattr(browser, "get_sniffing", Mock(return_value=configured_browser))
    monkeypatch.setattr(browser.webdriver, "Chrome", chrome)

    result = browser.get_driver()

    assert result is driver
    browser.get_sniffing.assert_called_with("use-browser")
    chrome.assert_called_once()
    assert isinstance(chrome.call_args.kwargs["options"], ChromeOptions)
