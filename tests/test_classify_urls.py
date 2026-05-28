from unittest.mock import Mock, call

import pandas as pd
import pytest

from ohmyscrapper.modules import classify_urls


def test_classify_urls_assigns_types_to_matching_unclassified_urls(monkeypatch):
    prefixes = pd.DataFrame(
        [
            {"url_prefix": "https://example.com/jobs/%", "url_type": "job"},
            {"url_prefix": "https://example.com/company/%", "url_type": "company"},
        ]
    )
    unclassified_by_prefix = {
        "https://example.com/jobs/%": pd.DataFrame(
            [{"id": 10}, {"id": 11}],
        ),
        "https://example.com/company/%": pd.DataFrame(
            [{"id": 20}],
        ),
    }
    set_url_type_by_id = Mock()

    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_urls_valid_prefix",
        Mock(return_value=prefixes),
    )
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_url_like_unclassified",
        Mock(side_effect=lambda like_condition: unclassified_by_prefix[like_condition]),
    )
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "set_url_type_by_id",
        set_url_type_by_id,
    )

    classify_urls.classify_urls()

    classify_urls.urls_manager.get_urls_valid_prefix.assert_called_once_with()
    assert classify_urls.urls_manager.get_url_like_unclassified.call_args_list == [
        call(like_condition="https://example.com/jobs/%"),
        call(like_condition="https://example.com/company/%"),
    ]
    assert set_url_type_by_id.call_args_list == [
        call(url_id=10, url_type="job"),
        call(url_id=11, url_type="job"),
        call(url_id=20, url_type="company"),
    ]


def test_classify_urls_seeds_when_no_prefixes_exist_then_retries(monkeypatch):
    empty_prefixes = pd.DataFrame(columns=["url_prefix", "url_type"])
    prefixes = pd.DataFrame(
        [{"url_prefix": "https://example.com/jobs/%", "url_type": "job"}]
    )
    matching_urls = pd.DataFrame([{"id": 42}])
    seed = Mock()
    set_url_type_by_id = Mock()

    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_urls_valid_prefix",
        Mock(side_effect=[empty_prefixes, prefixes]),
    )
    monkeypatch.setattr(classify_urls.seed, "seed", seed)
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_url_like_unclassified",
        Mock(return_value=matching_urls),
    )
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "set_url_type_by_id",
        set_url_type_by_id,
    )

    classify_urls.classify_urls()

    seed.assert_called_once_with()
    assert classify_urls.urls_manager.get_urls_valid_prefix.call_count == 2
    set_url_type_by_id.assert_called_once_with(url_id=42, url_type="job")


def test_classify_urls_does_not_update_when_no_unclassified_urls_match(monkeypatch):
    prefixes = pd.DataFrame(
        [{"url_prefix": "https://example.com/jobs/%", "url_type": "job"}]
    )
    set_url_type_by_id = Mock()

    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_urls_valid_prefix",
        Mock(return_value=prefixes),
    )
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_url_like_unclassified",
        Mock(return_value=pd.DataFrame(columns=["id"])),
    )
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "set_url_type_by_id",
        set_url_type_by_id,
    )

    classify_urls.classify_urls()

    set_url_type_by_id.assert_not_called()


def test_classify_urls_recursive_mode_sleeps_between_rounds(monkeypatch):
    prefixes = pd.DataFrame(
        [{"url_prefix": "https://example.com/jobs/%", "url_type": "job"}]
    )
    sleep = Mock(side_effect=RuntimeError("stop recursive loop"))

    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_urls_valid_prefix",
        Mock(return_value=prefixes),
    )
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "get_url_like_unclassified",
        Mock(return_value=pd.DataFrame(columns=["id"])),
    )
    monkeypatch.setattr(
        classify_urls.urls_manager,
        "set_url_type_by_id",
        Mock(),
    )
    monkeypatch.setattr(classify_urls.time, "sleep", sleep)

    with pytest.raises(RuntimeError, match="stop recursive loop"):
        classify_urls.classify_urls(recursive=True)

    sleep.assert_called_once_with(10)
