import json
from unittest.mock import Mock, call

import pytest
import requests
from bs4 import BeautifulSoup

from ohmyscrapper.modules import sniff_url


HTML = """
<html>
  <head>
    <meta name="description" content="Plain description">
    <meta property="og:title" content="Open Graph Title">
    <meta property="og:description" content="Open Graph Description">
  </head>
  <body>
    <h1>Main Title</h1>
    <h2 class="subtitle">First subtitle</h2>
    <h2 class="subtitle">Second subtitle</h2>
    <section id="details">Details text</section>
    <a href="/relative">Relative Link</a>
    <a href="https://external.example/path">External Link</a>
    <a>No href</a>
  </body>
</html>
"""


@pytest.fixture
def soup():
    return BeautifulSoup(HTML, "html.parser")


def test_extract_meta_tags_returns_matching_name_and_property_values(soup):
    result = sniff_url._extract_meta_tags(
        soup=soup,
        silent=True,
        metatags_to_search=["description", "og:title"],
    )

    assert result == {
        "description": "Plain description",
        "og:title": "Open Graph Title",
    }


def test_extract_text_tags_supports_tag_class_id_and_custom_separator(soup):
    result = sniff_url._extract_text_tags(
        soup=soup,
        silent=True,
        body_tags_to_search={
            "h1": " ",
            "h2.subtitle": " | ",
            "section#details": " ",
        },
    )

    assert result == {
        "h1": "Main Title",
        "h2.subtitle": "First subtitle | Second subtitle",
        "section#details": "Details text",
    }


def test_extract_a_tags_expands_relative_urls_and_keeps_missing_href(soup):
    result = sniff_url._extract_a_tags(
        soup=soup,
        silent=True,
        url="https://example.com/jobs/123",
    )

    assert result == [
        {"text": "Relative Link", "href": "https://example.com/relative"},
        {"text": "External Link", "href": "https://external.example/path"},
        {"text": "No href", "href": None},
    ]


def test_complementary_report_adds_link_and_meta_counts(soup):
    report = sniff_url._complementary_report(
        {
            "a_links": [
                {"text": "First", "href": "https://example.com/first"},
                {"text": "Second", "href": "https://example.com/second"},
            ]
        },
        soup=soup,
        silent=True,
    )

    assert report["first-a-link"] == "https://example.com/first"
    assert report["total-a-links"] == 2
    assert report["total-meta-tags"] == 3


def test_complementary_report_handles_empty_links_and_meta():
    report = sniff_url._complementary_report(
        {"a_links": []},
        soup=BeautifulSoup("<html></html>", "html.parser"),
        silent=True,
    )

    assert report["first-a-link"] == ""
    assert report["total-a-links"] == 0
    assert report["total-meta-tags"] == 0


def test_sniff_url_extracts_configured_report_fields(monkeypatch):
    monkeypatch.setattr(sniff_url, "get_url", Mock(return_value=HTML))

    report = sniff_url.sniff_url(
        url="https://example.com/jobs/123",
        silent=True,
        sniffing_config={
            "metatags": {"og:title": "title", "description": "description"},
            "bodytags": {"h1": " ", "h2.subtitle": " / "},
        },
    )

    assert report["scrapped-url"] == "https://example.com/jobs/123"
    assert report["og:title"] == "Open Graph Title"
    assert report["description"] == "Plain description"
    assert report["h1"] == "Main Title"
    assert report["h2.subtitle"] == "First subtitle Second subtitle"
    assert report["first-a-link"] == "https://example.com/relative"
    assert report["total-a-links"] == 3
    assert json.loads(report["json"])["og:title"] == "Open Graph Title"


def test_sniff_url_uses_default_tags_when_config_is_empty(monkeypatch):
    monkeypatch.setattr(sniff_url, "get_url", Mock(return_value=HTML))

    report = sniff_url.sniff_url(
        url="https://example.com/jobs/123",
        silent=True,
        sniffing_config={},
    )

    assert report["description"] == "Plain description"
    assert report["og:title"] == "Open Graph Title"
    assert report["og:description"] == "Open Graph Description"
    assert report["h1"] == "Main Title"


def test_sniff_url_returns_timeout_report_when_request_times_out(monkeypatch):
    monkeypatch.setattr(
        sniff_url,
        "get_url",
        Mock(side_effect=requests.exceptions.ReadTimeout()),
    )

    report = sniff_url.sniff_url(
        url="https://example.com/jobs/123",
        silent=True,
        sniffing_config={"metatags": [], "bodytags": []},
    )

    assert "timeout" in report["error"]
    assert "example.com" in report["error"]
    assert report["scrapped-url"] == "https://example.com/jobs/123"
    assert report["a_links"] == []
    assert report["total-a-links"] == 0


def test_get_tags_calls_sniff_url_silently(monkeypatch):
    sniff = Mock(return_value={"ok": True})
    monkeypatch.setattr(sniff_url, "sniff_url", sniff)
    driver = Mock()

    result = sniff_url.get_tags(
        "https://example.com",
        sniffing_config={"bodytags": []},
        driver=driver,
    )

    assert result == {"ok": True}
    sniff.assert_called_once_with(
        url="https://example.com",
        silent=True,
        sniffing_config={"bodytags": []},
        driver=driver,
    )


def test_get_url_returns_cached_code_without_fetching(monkeypatch):
    cache = Mock()
    cache.get.return_value = "<html>cached</html>"
    monkeypatch.setattr(sniff_url, "cache", cache)
    monkeypatch.setattr(sniff_url.requests, "get", Mock())

    result = sniff_url.get_url("https://example.com")

    assert result == "<html>cached</html>"
    cache.get.assert_called_once_with(cache_id="sniff-urf:https://example.com")
    sniff_url.requests.get.assert_not_called()


def test_get_url_uses_provided_driver_and_caches_page_source(monkeypatch):
    cache = Mock()
    cache.get.return_value = None
    driver = Mock()
    driver.page_source = "<html>driver</html>"
    monkeypatch.setattr(sniff_url, "cache", cache)
    monkeypatch.setattr(sniff_url.config, "get_sniffing", Mock(return_value=3))
    monkeypatch.setattr(sniff_url.time, "sleep", Mock())
    monkeypatch.setattr(sniff_url.requests, "get", Mock())

    result = sniff_url.get_url("https://example.com", driver=driver)

    assert result == "<html>driver</html>"
    driver.get.assert_called_once_with("https://example.com")
    sniff_url.time.sleep.assert_called_once_with(3)
    driver.implicitly_wait.assert_called_once_with(3)
    cache.set.assert_called_once_with(
        content="<html>driver</html>",
        cache_id="sniff-urf:https://example.com",
    )
    sniff_url.requests.get.assert_not_called()


def test_get_url_creates_browser_when_config_requires_it(monkeypatch):
    cache = Mock()
    cache.get.return_value = None
    driver = Mock()
    driver.page_source = "<html>browser</html>"
    monkeypatch.setattr(sniff_url, "cache", cache)
    monkeypatch.setattr(sniff_url.browser, "get_driver", Mock(return_value=driver))
    monkeypatch.setattr(
        sniff_url.config,
        "get_sniffing",
        Mock(side_effect=[True, 1, 1]),
    )
    monkeypatch.setattr(sniff_url.time, "sleep", Mock())

    result = sniff_url.get_url("https://example.com")

    assert result == "<html>browser</html>"
    sniff_url.browser.get_driver.assert_called_once_with()
    assert sniff_url.config.get_sniffing.call_args_list == [
        call("use-browser"),
        call("browser-waiting-time"),
        call("browser-waiting-time"),
    ]


def test_get_url_reports_browser_startup_error_with_url(monkeypatch):
    cache = Mock()
    cache.get.return_value = None
    monkeypatch.setattr(sniff_url, "cache", cache)
    monkeypatch.setattr(sniff_url.config, "get_sniffing", Mock(return_value=True))
    monkeypatch.setattr(
        sniff_url.browser,
        "get_driver",
        Mock(side_effect=RuntimeError("Unable to start chrome browser: missing")),
    )

    with pytest.raises(RuntimeError) as exc_info:
        sniff_url.get_url("https://example.com")

    assert "browser startup error for https://example.com" in str(exc_info.value)
    assert "Unable to start chrome browser: missing" in str(exc_info.value)


def test_get_url_falls_back_to_requests_when_driver_fails(monkeypatch, capsys):
    cache = Mock()
    cache.get.return_value = None
    driver = Mock()
    driver.get.side_effect = RuntimeError("browser failed")
    response = Mock()
    response.text = "<html>requests</html>"
    monkeypatch.setattr(sniff_url, "cache", cache)
    monkeypatch.setattr(sniff_url.config, "get_sniffing", Mock(return_value=5))
    monkeypatch.setattr(sniff_url.requests, "get", Mock(return_value=response))

    result = sniff_url.get_url("https://example.com", driver=driver)

    assert result == "<html>requests</html>"
    sniff_url.requests.get.assert_called_once_with(
        url="https://example.com",
        timeout=5,
    )
    cache.set.assert_called_once_with(
        content="<html>requests</html>",
        cache_id="sniff-urf:https://example.com",
    )
    assert "error" in capsys.readouterr().out


def test_get_url_uses_requests_when_browser_is_disabled(monkeypatch):
    cache = Mock()
    cache.get.return_value = None
    response = Mock()
    response.text = "<html>requests</html>"
    monkeypatch.setattr(sniff_url, "cache", cache)
    monkeypatch.setattr(
        sniff_url.config,
        "get_sniffing",
        Mock(side_effect=[False, 10]),
    )
    monkeypatch.setattr(sniff_url.browser, "get_driver", Mock())
    monkeypatch.setattr(sniff_url.requests, "get", Mock(return_value=response))

    result = sniff_url.get_url("https://example.com")

    assert result == "<html>requests</html>"
    sniff_url.browser.get_driver.assert_not_called()
    sniff_url.requests.get.assert_called_once_with(
        url="https://example.com",
        timeout=10,
    )
    cache.set.assert_called_once_with(
        content="<html>requests</html>",
        cache_id="sniff-urf:https://example.com",
    )
