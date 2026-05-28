from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, call

import pandas as pd
import pytest

from ohmyscrapper.modules import scrap_urls


@pytest.fixture
def patched_url_manager(monkeypatch):
    methods = {
        "add_url": Mock(),
        "set_url_title": Mock(),
        "set_url_description": Mock(),
        "set_url_description_links": Mock(),
        "set_url_destiny": Mock(),
        "set_url_error": Mock(),
        "set_url_json": Mock(),
        "touch_url": Mock(),
        "get_untouched_urls": Mock(),
        "create_scraping_run": Mock(return_value=42),
        "get_scraping_run": Mock(
            return_value=pd.DataFrame(
                [
                    {
                        "id": 42,
                        "status": "running",
                        "total_urls": 0,
                        "completed_count": 0,
                        "skipped_count": 0,
                        "failure_count": 0,
                    }
                ]
            )
        ),
        "update_scraping_run_total": Mock(),
        "increment_scraping_run_counter": Mock(),
        "finish_scraping_run": Mock(),
    }
    for name, mock in methods.items():
        monkeypatch.setattr(scrap_urls.urls_manager, name, mock)
    return methods


def test_process_sniffed_url_updates_title_description_links_and_destiny(
    monkeypatch,
    patched_url_manager,
):
    put_urls_from_string = Mock(return_value=2)
    monkeypatch.setattr(
        scrap_urls.load_txt,
        "put_urls_from_string",
        put_urls_from_string,
    )
    url = {"url": "https://example.com/source", "url_type": "job"}
    url_report = {
        "og:title": "Backend Engineer",
        "description": "Apply at https://example.com/apply",
        "h1": "Remote",
        "first-a-link": "https://example.com/final",
        "total-a-links": 1,
        "a_links": [
            {"href": "https://example.com/child-1"},
            {"href": "https://example.com/child-2"},
        ],
    }
    sniffing_config = {
        "metatags": {
            "og:title": "title",
            "description": "description",
        },
        "bodytags": {"h1": "+description"},
        "atags": {
            "first-tag-as-url_destiny": 2,
            "load_links": True,
        },
    }

    scrap_urls.process_sniffed_url(url_report, url, sniffing_config)

    patched_url_manager["set_url_title"].assert_called_once_with(
        url="https://example.com/source",
        value="Backend Engineer",
    )
    patched_url_manager["set_url_description"].assert_called_once_with(
        url="https://example.com/source",
        value="Apply at https://example.com/apply Remote",
    )
    put_urls_from_string.assert_called_once_with(
        text_to_process="Apply at https://example.com/apply Remote",
        parent_url="https://example.com/source",
    )
    patched_url_manager["set_url_description_links"].assert_called_once_with(
        url="https://example.com/source",
        value=2,
    )
    assert patched_url_manager["add_url"].call_args_list == [
        call(
            url="https://example.com/child-1",
            parent_url="https://example.com/source",
        ),
        call(
            url="https://example.com/child-2",
            parent_url="https://example.com/source",
        ),
        call(url="https://example.com/final"),
    ]
    patched_url_manager["set_url_destiny"].assert_called_once_with(
        url="https://example.com/source",
        destiny="https://example.com/final",
    )
    patched_url_manager["set_url_error"].assert_not_called()


def test_process_sniffed_url_sets_warning_when_no_configured_fields_match(
    patched_url_manager,
):
    scrap_urls.process_sniffed_url(
        url_report={"json": "{}"},
        url={"url": "https://example.com/source", "url_type": "generic"},
        sniffing_config={"metatags": {"og:title": "title"}},
    )

    patched_url_manager["set_url_error"].assert_called_once_with(
        url="https://example.com/source",
        value="warning: no title, url_destiny or description was founded",
    )


def test_scrap_url_uses_generic_type_when_url_type_is_missing(
    monkeypatch,
    patched_url_manager,
):
    process_sniffed_url = Mock()
    sniffing_config = {"generic": {"bodytags": {"h1": "title"}}}
    url_report = {"h1": "Title", "json": '{"h1": "Title"}'}

    monkeypatch.setattr(
        scrap_urls.config,
        "get_url_sniffing",
        Mock(return_value=sniffing_config),
    )
    monkeypatch.setattr(scrap_urls.sniff_url, "get_tags", Mock(return_value=url_report))
    monkeypatch.setattr(scrap_urls, "process_sniffed_url", process_sniffed_url)

    url = {"url": "https://example.com/page", "url_type": None}
    driver = Mock()

    result = scrap_urls.scrap_url(url=url, driver=driver)

    assert result is True
    assert url["url_type"] == "generic"
    scrap_urls.sniff_url.get_tags.assert_called_once_with(
        url="https://example.com/page",
        sniffing_config=sniffing_config["generic"],
        driver=driver,
    )
    process_sniffed_url.assert_called_once_with(
        url_report=url_report,
        url=url,
        sniffing_config=sniffing_config["generic"],
        verbose=False,
    )
    patched_url_manager["set_url_json"].assert_called_once_with(
        url="https://example.com/page",
        value='{"h1": "Title"}',
    )
    patched_url_manager["touch_url"].assert_called_once_with(
        url="https://example.com/page"
    )


def test_scrap_url_appends_default_sniffing_config_for_unknown_type(
    monkeypatch,
    patched_url_manager,
):
    first_config = {}
    second_config = {"custom": {"bodytags": {"h1": "title"}}}
    append_url_sniffing = Mock()
    monkeypatch.setattr(
        scrap_urls.config,
        "get_url_sniffing",
        Mock(side_effect=[first_config, second_config]),
    )
    monkeypatch.setattr(
        scrap_urls.config,
        "append_url_sniffing",
        append_url_sniffing,
    )
    monkeypatch.setattr(
        scrap_urls.sniff_url,
        "get_tags",
        Mock(return_value={"h1": "Title", "json": "{}"}),
    )
    monkeypatch.setattr(scrap_urls, "process_sniffed_url", Mock())

    scrap_urls.scrap_url({"url": "https://example.com/page", "url_type": "custom"})

    append_url_sniffing.assert_called_once_with(
        {
            "custom": {
                "bodytags": {"h1": "title"},
                "metatags": {
                    "og:title": "title",
                    "og:description": "description",
                    "description": "description",
                },
            }
        }
    )


def test_scrap_url_records_error_and_touches_url_when_sniffing_fails(
    monkeypatch,
    patched_url_manager,
):
    monkeypatch.setattr(
        scrap_urls.config,
        "get_url_sniffing",
        Mock(return_value={"job": {"bodytags": {"h1": "title"}}}),
    )
    monkeypatch.setattr(
        scrap_urls.sniff_url,
        "get_tags",
        Mock(side_effect=RuntimeError("boom")),
    )

    result = scrap_urls.scrap_url(
        {"url": "https://example.com/page", "url_type": "job"},
        verbose=True,
    )

    assert result is False
    patched_url_manager["set_url_error"].assert_called_once_with(
        url="https://example.com/page",
        value="error on scrapping: boom",
    )
    patched_url_manager["touch_url"].assert_called_once_with(
        url="https://example.com/page"
    )


def test_get_scraping_policy_reads_configured_delay_and_retry_values(monkeypatch):
    values = {
        "request-delay-min": "2",
        "request-delay-max": "4",
        "retry-count": "3",
        "retry-backoff": "0.5",
    }
    monkeypatch.setattr(
        scrap_urls.config,
        "get_sniffing",
        Mock(side_effect=lambda param: values[param]),
    )
    monkeypatch.setattr(scrap_urls.random, "randint", Mock(return_value=3))

    policy = scrap_urls.get_scraping_policy()

    assert policy == {
        "request_delay_min": 2.0,
        "request_delay_max": 4.0,
        "retry_count": 3,
        "retry_backoff": 0.5,
    }
    assert scrap_urls.get_scraping_delay(policy) == 3
    scrap_urls.random.randint.assert_called_once_with(2, 4)


def test_scrap_url_retries_retryable_failure_and_succeeds(
    monkeypatch,
    patched_url_manager,
):
    sniffing_config = {"job": {"bodytags": {"h1": "title"}}}
    url_report = {"h1": "Title", "json": '{"h1": "Title"}'}
    monkeypatch.setattr(
        scrap_urls.config,
        "get_url_sniffing",
        Mock(return_value=sniffing_config),
    )
    monkeypatch.setattr(
        scrap_urls.config,
        "get_sniffing",
        Mock(
            side_effect=lambda param: {
                "request-delay-min": 1,
                "request-delay-max": 3,
                "retry-count": 1,
                "retry-backoff": 0.5,
            }[param]
        ),
    )
    monkeypatch.setattr(
        scrap_urls.sniff_url,
        "get_tags",
        Mock(side_effect=[RuntimeError("temporary"), url_report]),
    )
    monkeypatch.setattr(scrap_urls, "process_sniffed_url", Mock())
    monkeypatch.setattr(scrap_urls.time, "sleep", Mock())

    result = scrap_urls.scrap_url({"url": "https://example.com/page", "url_type": "job"})

    assert result is True
    assert scrap_urls.sniff_url.get_tags.call_count == 2
    scrap_urls.time.sleep.assert_called_once_with(0.5)
    patched_url_manager["set_url_error"].assert_not_called()
    patched_url_manager["set_url_json"].assert_called_once_with(
        url="https://example.com/page",
        value='{"h1": "Title"}',
    )


def test_scrap_url_records_final_error_after_retry_exhaustion(
    monkeypatch,
    patched_url_manager,
):
    monkeypatch.setattr(
        scrap_urls.config,
        "get_url_sniffing",
        Mock(return_value={"job": {"bodytags": {"h1": "title"}}}),
    )
    monkeypatch.setattr(
        scrap_urls.config,
        "get_sniffing",
        Mock(
            side_effect=lambda param: {
                "request-delay-min": 1,
                "request-delay-max": 3,
                "retry-count": 2,
                "retry-backoff": 0.25,
            }[param]
        ),
    )
    monkeypatch.setattr(
        scrap_urls.sniff_url,
        "get_tags",
        Mock(
            side_effect=[
                RuntimeError("temporary"),
                RuntimeError("still temporary"),
                RuntimeError("dead"),
            ]
        ),
    )
    monkeypatch.setattr(scrap_urls.time, "sleep", Mock())

    result = scrap_urls.scrap_url({"url": "https://example.com/page", "url_type": "job"})

    assert result is False
    assert scrap_urls.sniff_url.get_tags.call_count == 3
    assert scrap_urls.time.sleep.call_args_list == [call(0.25), call(0.5)]
    patched_url_manager["set_url_error"].assert_called_once_with(
        url="https://example.com/page",
        value="error on scrapping: dead",
    )
    patched_url_manager["touch_url"].assert_called_once_with(
        url="https://example.com/page"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (float("nan"), True),
        (1.0, False),
        ("text", False),
    ],
)
def test_is_nan(value, expected):
    assert scrap_urls.isNaN(value) is expected


def test_format_scraping_progress_includes_persisted_counters():
    assert (
        scrap_urls.format_scraping_progress(
            {
                "id": 7,
                "status": "running",
                "total_urls": 4,
                "processed_count": 3,
                "completed_count": 2,
                "skipped_count": 1,
                "failure_count": 0,
            }
        )
        == "-- progress run #7 [running]: 3/4 processed (75%) completed=2 skipped=1 failed=0"
    )


def test_get_scraping_run_progress_reads_persisted_state(patched_url_manager):
    patched_url_manager["get_scraping_run"].return_value = pd.DataFrame(
        [
            {
                "id": 42,
                "status": "running",
                "total_urls": 5,
                "completed_count": 2,
                "skipped_count": 1,
                "failure_count": 1,
            }
        ]
    )

    assert scrap_urls.get_scraping_run_progress(42) == {
        "id": 42,
        "status": "running",
        "total_urls": 5,
        "completed_count": 2,
        "skipped_count": 1,
        "failure_count": 1,
        "processed_count": 4,
    }


def test_scrap_urls_returns_when_there_are_no_urls(monkeypatch, patched_url_manager):
    classify = Mock()
    monkeypatch.setattr(scrap_urls.classify_urls, "classify_urls", classify)
    patched_url_manager["get_untouched_urls"].return_value = pd.DataFrame()

    result = scrap_urls.scrap_urls(n_urls=3)

    assert result is None
    classify.assert_called_once_with()
    patched_url_manager["get_untouched_urls"].assert_called_once_with(
        ignore_valid_prefix=False,
        randomize=False,
        only_parents=True,
        limit=10,
    )
    patched_url_manager["create_scraping_run"].assert_called_once_with(
        command="scrap-urls"
    )
    patched_url_manager["update_scraping_run_total"].assert_called_once_with(42, 3)
    patched_url_manager["finish_scraping_run"].assert_called_once_with(
        42,
        status="completed",
    )


def test_scrap_urls_scrapes_rows_without_browser_when_config_disables_it(
    monkeypatch,
    patched_url_manager,
):
    urls = pd.DataFrame(
        [
            {"url": "https://example.com/one", "url_type": "job"},
            {"url": "https://example.com/two", "url_type": "company"},
        ]
    )
    classify = Mock()
    scrap_url = Mock()
    monkeypatch.setattr(scrap_urls.classify_urls, "classify_urls", classify)
    patched_url_manager["get_untouched_urls"].return_value = urls
    monkeypatch.setattr(scrap_urls.random, "randint", Mock(return_value=1))
    monkeypatch.setattr(scrap_urls.time, "sleep", Mock())
    monkeypatch.setattr(scrap_urls.config, "get_sniffing", Mock(return_value=False))
    monkeypatch.setattr(scrap_urls.browser, "get_driver", Mock())
    monkeypatch.setattr(scrap_urls, "scrap_url", scrap_url)

    scrap_urls.scrap_urls(ignore_valid_prefix=True, randomize=True, verbose=True)

    assert classify.call_args_list == [call(), call()]
    patched_url_manager["get_untouched_urls"].assert_called_once_with(
        ignore_valid_prefix=True,
        randomize=True,
        only_parents=True,
        limit=10,
    )
    assert scrap_urls.time.sleep.call_args_list == [call(1), call(1)]
    scrap_urls.browser.get_driver.assert_not_called()
    assert scrap_url.call_count == 2
    assert scrap_url.call_args_list[0].kwargs["url"].equals(urls.iloc[0])
    assert scrap_url.call_args_list[0].kwargs["verbose"] is True
    assert scrap_url.call_args_list[0].kwargs["driver"] is None
    assert scrap_url.call_args_list[1].kwargs["url"].equals(urls.iloc[1])
    assert scrap_url.call_args_list[1].kwargs["verbose"] is True
    assert scrap_url.call_args_list[1].kwargs["driver"] is None
    assert patched_url_manager["increment_scraping_run_counter"].call_args_list == [
        call(42, "completed_count"),
        call(42, "completed_count"),
    ]
    patched_url_manager["finish_scraping_run"].assert_called_once_with(
        42,
        status="completed",
    )


def test_scrap_urls_creates_browser_once_when_enabled(monkeypatch, patched_url_manager):
    urls = pd.DataFrame(
        [
            {"url": "https://example.com/one", "url_type": "job"},
            {"url": "https://example.com/two", "url_type": "company"},
        ]
    )
    driver = Mock(name="driver")
    scrap_url = Mock()
    monkeypatch.setattr(scrap_urls.classify_urls, "classify_urls", Mock())
    patched_url_manager["get_untouched_urls"].return_value = urls
    monkeypatch.setattr(scrap_urls.random, "randint", Mock(return_value=1))
    monkeypatch.setattr(scrap_urls.time, "sleep", Mock())
    monkeypatch.setattr(scrap_urls.config, "get_sniffing", Mock(return_value=True))
    monkeypatch.setattr(scrap_urls.browser, "get_driver", Mock(return_value=driver))
    monkeypatch.setattr(scrap_urls, "scrap_url", scrap_url)

    scrap_urls.scrap_urls()

    scrap_urls.browser.get_driver.assert_called_once_with()
    assert scrap_url.call_count == 2
    assert scrap_url.call_args_list[0].kwargs["url"].equals(urls.iloc[0])
    assert scrap_url.call_args_list[0].kwargs["verbose"] is False
    assert scrap_url.call_args_list[0].kwargs["driver"] is driver
    assert scrap_url.call_args_list[1].kwargs["url"].equals(urls.iloc[1])
    assert scrap_url.call_args_list[1].kwargs["verbose"] is False
    assert scrap_url.call_args_list[1].kwargs["driver"] is driver


def test_scrap_urls_recursive_mode_waits_and_calls_next_round(
    monkeypatch,
    patched_url_manager,
):
    urls = pd.DataFrame([{"url": "https://example.com/one", "url_type": "job"}])
    driver = Mock(name="driver")

    classify = Mock()
    monkeypatch.setattr(scrap_urls.classify_urls, "classify_urls", classify)
    patched_url_manager["get_untouched_urls"].side_effect = [urls, pd.DataFrame()]
    monkeypatch.setattr(scrap_urls.random, "randint", Mock(side_effect=[1, 5]))
    monkeypatch.setattr(scrap_urls.time, "sleep", Mock())
    monkeypatch.setattr(
        scrap_urls.config,
        "get_sniffing",
        Mock(
            side_effect=lambda param: {
                "round-sleeping": 20,
                "request-delay-min": 1,
                "request-delay-max": 3,
                "retry-count": 0,
                "retry-backoff": 0,
            }[param]
        ),
    )
    monkeypatch.setattr(scrap_urls, "scrap_url", Mock())

    scrap_urls.scrap_urls(
        recursive=True,
        ignore_valid_prefix=True,
        randomize=True,
        only_parents=False,
        verbose=True,
        n_urls=4,
        driver=driver,
    )

    assert scrap_urls.time.sleep.call_args_list == [call(1), call(5)]
    assert classify.call_args_list == [call(), call(), call()]
    assert patched_url_manager["get_untouched_urls"].call_args_list == [
        call(
            ignore_valid_prefix=True,
            randomize=True,
            only_parents=False,
            limit=10,
        ),
        call(
            ignore_valid_prefix=True,
            randomize=True,
            only_parents=False,
            limit=10,
        ),
    ]
    patched_url_manager["finish_scraping_run"].assert_called_once_with(
        42,
        status="completed",
    )


def test_scrap_urls_counts_failed_scrapes(monkeypatch, patched_url_manager):
    urls = pd.DataFrame([{"url": "https://example.com/one", "url_type": "job"}])
    monkeypatch.setattr(scrap_urls.classify_urls, "classify_urls", Mock())
    patched_url_manager["get_untouched_urls"].return_value = urls
    monkeypatch.setattr(scrap_urls.random, "randint", Mock(return_value=1))
    monkeypatch.setattr(scrap_urls.time, "sleep", Mock())
    monkeypatch.setattr(scrap_urls.config, "get_sniffing", Mock(return_value=False))
    monkeypatch.setattr(scrap_urls, "scrap_url", Mock(return_value=False))

    scrap_urls.scrap_urls()

    patched_url_manager["increment_scraping_run_counter"].assert_called_once_with(
        42,
        "failure_count",
    )
    patched_url_manager["finish_scraping_run"].assert_called_once_with(
        42,
        status="completed",
    )


def test_scrap_urls_prints_progress_from_run_counters(monkeypatch, patched_url_manager):
    urls = pd.DataFrame([{"url": "https://example.com/one", "url_type": "job"}])
    patched_url_manager["get_scraping_run"].side_effect = [
        pd.DataFrame(
            [
                {
                    "id": 42,
                    "status": "running",
                    "total_urls": 1,
                    "completed_count": 0,
                    "skipped_count": 0,
                    "failure_count": 0,
                }
            ]
        ),
        pd.DataFrame(
            [
                {
                    "id": 42,
                    "status": "running",
                    "total_urls": 1,
                    "completed_count": 1,
                    "skipped_count": 0,
                    "failure_count": 0,
                }
            ]
        ),
    ]
    monkeypatch.setattr(scrap_urls.classify_urls, "classify_urls", Mock())
    patched_url_manager["get_untouched_urls"].return_value = urls
    monkeypatch.setattr(scrap_urls.random, "randint", Mock(return_value=1))
    monkeypatch.setattr(scrap_urls.time, "sleep", Mock())
    monkeypatch.setattr(scrap_urls.config, "get_sniffing", Mock(return_value=False))
    monkeypatch.setattr(scrap_urls, "scrap_url", Mock(return_value=True))

    output = StringIO()
    with redirect_stdout(output):
        scrap_urls.scrap_urls()

    assert "-- progress run #42 [running]: 0/1 processed (0%)" in output.getvalue()
    assert (
        "-- progress run #42 [running]: 1/1 processed (100%) completed=1 skipped=0 failed=0"
        in output.getvalue()
    )
