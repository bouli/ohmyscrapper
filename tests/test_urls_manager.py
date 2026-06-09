import sqlite3

import pytest

from ohmyscrapper.models import urls_manager


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "local.db"
    monkeypatch.setattr(urls_manager, "get_db_path", lambda: str(path))
    monkeypatch.setattr(urls_manager.time, "time", lambda: 1234567890)
    return path


def first_row(df):
    assert len(df) == 1
    return df.iloc[0]


@pytest.mark.parametrize(
    ("raw_url", "expected"),
    [
        (
            "example.com/jobs?keep=1&utm_source=news#section",
            "https://example.com/jobs?keep=1",
        ),
        ("http://example.com/path", "https://example.com/path"),
        ("https://example.com/path?utm_campaign=x", "https://example.com/path"),
        ("example.com/it's-open", "https://example.com/its-open"),
    ],
)
def test_clean_url_normalizes_scheme_tracking_fragments_and_quotes(raw_url, expected):
    assert urls_manager.clean_url(raw_url) == expected


def test_get_db_connection_creates_expected_tables(db_path):
    with urls_manager.get_db_connection() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert db_path.exists()
    assert {"urls", "ai_log", "urls_valid_prefix", "scraping_runs"} <= tables


def test_scraping_run_lifecycle_persists_status_and_counters(db_path):
    run_id = urls_manager.create_scraping_run(command="start", total_urls=3)

    urls_manager.increment_scraping_run_counter(run_id, "completed_count")
    urls_manager.increment_scraping_run_counter(run_id, "failure_count", amount=2)
    urls_manager.update_scraping_run_total(run_id, 5)
    urls_manager.finish_scraping_run(run_id, status="completed")

    run = first_row(urls_manager.get_scraping_run(run_id))
    runs = urls_manager.get_scraping_runs(limit=1)

    assert len(runs) == 1
    assert run["id"] == run_id
    assert run["command"] == "start"
    assert run["status"] == "completed"
    assert run["total_urls"] == 5
    assert run["completed_count"] == 1
    assert run["skipped_count"] == 0
    assert run["failure_count"] == 2
    assert run["started_at"] == 1234567890
    assert run["updated_at"] == 1234567890
    assert run["finished_at"] == 1234567890


def test_scraping_run_validates_status_and_counter_names(db_path):
    run_id = urls_manager.create_scraping_run()

    with pytest.raises(ValueError, match="Unknown scraping run counter"):
        urls_manager.increment_scraping_run_counter(run_id, "unknown")

    with pytest.raises(ValueError, match="Unknown scraping run status"):
        urls_manager.finish_scraping_run(run_id, status="running")


def test_add_url_normalizes_trims_title_and_ignores_duplicates(db_path):
    urls_manager.add_url(
        "http://example.com/jobs?utm_source=news#heading",
        title="  Backend Engineer  ",
    )
    urls_manager.add_url("https://example.com/jobs")
    urls_manager.add_url("/relative/path")

    urls = urls_manager.get_urls()
    row = first_row(urls)

    assert len(urls) == 1
    assert row["url"] == "https://example.com/jobs"
    assert row["title"] == "Backend Engineer"
    assert row["parent_url"] is None
    assert row["created_at"] == 1234567890
    assert urls_manager.add_url("/relative/path") is None


def test_get_urls_supports_limit_after_ordering(db_path):
    urls_manager.add_url("https://example.com/old")
    urls_manager.add_url("https://example.com/new")

    limited = urls_manager.get_urls(limit=1)

    assert len(limited) == 1
    assert limited.iloc[0]["url"] in {
        "https://example.com/old",
        "https://example.com/new",
    }


def test_url_valid_prefix_seed_lifecycle(db_path):
    seeds = {
        "job": "https://%.example.com/jobs/%",
        "company": "https://%.example.com/company/%",
    }

    assert urls_manager.seeds(seeds) is True
    urls_manager.seeds(seeds)

    prefixes = urls_manager.get_urls_valid_prefix()
    job_prefix = first_row(urls_manager.get_urls_valid_prefix_by_type("job"))
    by_id = first_row(urls_manager.get_urls_valid_prefix_by_id(job_prefix["id"]))

    assert len(prefixes) == 2
    assert urls_manager.get_urls_valid_prefix(limit=1).shape[0] == 1
    assert job_prefix["url_prefix"] == "https://%.example.com/jobs/%"
    assert by_id["url_type"] == "job"

    urls_manager.reset_seeds()

    assert urls_manager.get_urls_valid_prefix().empty


def test_url_manager_queries_handle_sql_sensitive_values(db_path):
    url_type = "engineer's role"
    url_prefix = "https://example.com/jobs/O'Reilly/%"
    url = "https://example.com/sql-sensitive"

    urls_manager.add_urls_valid_prefix(url_prefix, url_type)
    prefix = first_row(urls_manager.get_urls_valid_prefix_by_type(url_type))
    urls_manager.add_url(url)
    row_id = first_row(urls_manager.get_url_by_url(url))["id"]
    urls_manager.set_url_type_by_id(row_id, url_type)

    assert prefix["url_prefix"] == url_prefix
    assert first_row(urls_manager.get_urls_valid_prefix_by_id(prefix["id"]))[
        "url_type"
    ] == url_type
    assert first_row(urls_manager.get_urls_by_url_type(url_type))["url"] == url


def test_url_field_setters_update_existing_rows(db_path):
    url = "https://example.com/job"
    urls_manager.add_url(url)
    row_id = first_row(urls_manager.get_url_by_url(url))["id"]

    urls_manager.set_url_title(url, "  Senior Engineer  ")
    urls_manager.set_url_description(url, "Role description")
    urls_manager.set_url_description_links(url, 3)
    urls_manager.set_url_json(url, '{"ok": true}')
    urls_manager.set_url_error(url, "error on scraping")
    urls_manager.set_url_type_by_id(row_id, "job")

    row = first_row(urls_manager.get_url_by_id(row_id))

    assert row["title"] == "Senior Engineer"
    assert row["description"] == "Role description"
    assert row["description_links"] == 3
    assert row["json"] == '{"ok": true}'
    assert row["error"] == "error on scraping"
    assert row["url_type"] == "job"

    urls_manager.set_url_title_by_id(row_id, "  Staff Engineer  ")

    assert first_row(urls_manager.get_url_by_url(url))["title"] == "Staff Engineer"


def test_url_destiny_links_destination_back_to_source(db_path):
    source = "https://example.com/redirect"
    destiny = "https://example.com/final"
    urls_manager.add_url(source)
    urls_manager.add_url(destiny)

    urls_manager.set_url_destiny(source, destiny)

    source_row = first_row(urls_manager.get_url_by_url(source))
    destiny_row = first_row(urls_manager.get_url_by_url(destiny))

    assert source_row["url_destiny"] == destiny
    assert destiny_row["parent_url"] == source


def test_touch_and_untouch_reset_processing_state(db_path):
    url = "https://example.com/job"
    urls_manager.add_url(url)
    row_id = first_row(urls_manager.get_url_by_url(url))["id"]
    urls_manager.set_url_type_by_id(row_id, "job")
    urls_manager.set_url_error(url, "error on scraping")

    urls_manager.touch_url(url)

    assert first_row(urls_manager.get_url_by_url(url))["last_touch"] == 1234567890

    urls_manager.untouch_url(url)
    row = first_row(urls_manager.get_url_by_url(url))

    assert row["last_touch"] is None
    assert row["url_type"] is None
    assert row["error"] is None


def test_untouched_urls_filters_by_type_parent_history_and_touch_state(db_path):
    urls_manager.add_url("https://example.com/parent")
    urls_manager.add_url(
        "https://example.com/child",
        parent_url="https://example.com/parent",
    )
    urls_manager.add_url("https://example.com/untyped")

    parent = first_row(urls_manager.get_url_by_url("https://example.com/parent"))
    child = first_row(urls_manager.get_url_by_url("https://example.com/child"))
    urls_manager.set_url_type_by_id(parent["id"], "job")
    urls_manager.set_url_type_by_id(child["id"], "job")

    parent_only = urls_manager.get_untouched_urls(randomize=False, only_parents=True)
    all_typed = urls_manager.get_untouched_urls(randomize=False, only_parents=False)
    including_untyped = urls_manager.get_untouched_urls(
        randomize=False,
        ignore_valid_prefix=True,
        only_parents=True,
    )

    assert parent_only["url"].tolist() == ["https://example.com/parent"]
    assert set(all_typed["url"]) == {
        "https://example.com/parent",
        "https://example.com/child",
    }
    assert set(including_untyped["url"]) == {
        "https://example.com/parent",
        "https://example.com/untyped",
    }

    urls_manager.touch_url("https://example.com/parent")

    assert urls_manager.get_untouched_urls(randomize=False, only_parents=True).empty


def test_bulk_untouch_operations_reset_active_urls_only(db_path):
    urls_manager.add_url("https://example.com/active-error")
    urls_manager.add_url("https://example.com/active-warning")
    urls_manager.add_url("https://example.com/history-error")

    for url in [
        "https://example.com/active-error",
        "https://example.com/active-warning",
        "https://example.com/history-error",
    ]:
        row_id = first_row(urls_manager.get_url_by_url(url))["id"]
        urls_manager.set_url_type_by_id(row_id, "job")
        urls_manager.touch_url(url)

    urls_manager.set_url_error("https://example.com/active-error", "error timeout")
    urls_manager.set_url_error("https://example.com/active-warning", "warning empty")
    urls_manager.set_url_error("https://example.com/history-error", "error old")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE urls SET history = 1 WHERE url = ?",
            ("https://example.com/history-error",),
        )

    urls_manager.untouch_all_urls_with_errors()

    active_error = first_row(
        urls_manager.get_url_by_url("https://example.com/active-error")
    )
    active_warning = first_row(
        urls_manager.get_url_by_url("https://example.com/active-warning")
    )
    history_error = first_row(
        urls_manager.get_url_by_url("https://example.com/history-error")
    )

    assert active_error["last_touch"] is None
    assert active_error["url_type"] is None
    assert active_error["error"] is None
    assert active_warning["last_touch"] == 1234567890
    assert history_error["last_touch"] == 1234567890

    urls_manager.untouch_all_urls()

    assert first_row(
        urls_manager.get_url_by_url("https://example.com/active-warning")
    )["last_touch"] is None
    assert first_row(
        urls_manager.get_url_by_url("https://example.com/history-error")
    )["last_touch"] == 1234567890


def test_untouch_errors_can_include_active_warnings(db_path):
    urls_manager.add_url("https://example.com/active-error")
    urls_manager.add_url("https://example.com/active-warning")

    for url in [
        "https://example.com/active-error",
        "https://example.com/active-warning",
    ]:
        row_id = first_row(urls_manager.get_url_by_url(url))["id"]
        urls_manager.set_url_type_by_id(row_id, "job")
        urls_manager.touch_url(url)

    urls_manager.set_url_error("https://example.com/active-error", "error timeout")
    urls_manager.set_url_error("https://example.com/active-warning", "warning empty")

    urls_manager.untouch_all_urls_with_errors(include_warnings=True)

    active_error = first_row(
        urls_manager.get_url_by_url("https://example.com/active-error")
    )
    active_warning = first_row(
        urls_manager.get_url_by_url("https://example.com/active-warning")
    )

    assert active_error["last_touch"] is None
    assert active_error["url_type"] is None
    assert active_error["error"] is None
    assert active_warning["last_touch"] is None
    assert active_warning["url_type"] is None
    assert active_warning["error"] is None


def test_get_urls_report_excludes_parent_and_inherits_parent_title(db_path):
    parent = "https://example.com/company"
    child = "https://example.com/job"
    urls_manager.add_url(parent, title="Example Company")
    urls_manager.add_url(child, parent_url=parent)
    child_id = first_row(urls_manager.get_url_by_url(child))["id"]
    urls_manager.set_url_type_by_id(child_id, "job")

    report = urls_manager.get_urls_report()
    row = first_row(report)

    assert row["url"] == child
    assert row["title"] == "Example Company"
    assert row["parent_url"] == parent
    assert row["parent_title"] == "Example Company"


def test_ai_log_and_processing_flags(db_path):
    urls_manager.add_url("https://example.com/with-title", title="Title")
    urls_manager.add_url("https://example.com/with-description")
    urls_manager.add_url("https://example.com/without-content")
    description_id = first_row(
        urls_manager.get_url_by_url("https://example.com/with-description")
    )["id"]
    title_id = first_row(
        urls_manager.get_url_by_url("https://example.com/with-title")
    )["id"]
    urls_manager.set_url_description(
        "https://example.com/with-description", "Description"
    )

    to_process = urls_manager.get_urls_by_url_type_for_ai_process(limit=10)

    assert set(to_process["url"]) == {
        "https://example.com/with-title",
        "https://example.com/with-description",
    }

    urls_manager.set_url_ai_processed_by_id(title_id, '{"title": true}')
    urls_manager.set_url_empty_ai_processed_by_id(description_id)
    urls_manager.set_url_ai_processed_by_url(
        "https://example.com/without-content",
        '{"manually": true}',
    )
    urls_manager.add_ai_log("instructions", "response", "model", "prompt.md", "prompt")

    assert urls_manager.get_urls_by_url_type_for_ai_process(limit=10).empty
    assert (
        first_row(urls_manager.get_url_by_id(title_id))["json_ai"]
        == '{"title": true}'
    )
    assert (
        first_row(urls_manager.get_url_by_id(description_id))["json_ai"]
        == "empty result"
    )

    ai_log = first_row(urls_manager.get_ai_log())

    assert ai_log["instructions"] == "instructions"
    assert ai_log["response"] == "response"
    assert ai_log["model"] == "model"
    assert ai_log["prompt_file"] == "prompt.md"
    assert ai_log["prompt_name"] == "prompt"
    assert ai_log["created_at"] == 1234567890


def test_set_all_urls_as_history_and_merge_url(db_path):
    urls_manager.add_url("https://example.com/current")
    urls_manager.merge_url(
        "http://example.com/merged",
        "  merged title  ",
        last_touch=10,
        created_at=5,
        description="merged description",
        json='{"merged": true}',
    )
    urls_manager.merge_url(
        "https://example.com/merged",
        "duplicate ignored",
        last_touch=99,
        created_at=99,
        description="duplicate",
        json="{}",
    )

    merged = first_row(urls_manager.get_url_by_url("https://example.com/merged"))

    assert len(urls_manager.get_urls()) == 2
    assert merged["title"] == "merged title"
    assert merged["history"] == 1
    assert merged["last_touch"] == 10
    assert merged["created_at"] == 5
    assert merged["description"] == "merged description"
    assert merged["json"] == '{"merged": true}'

    urls_manager.set_all_urls_as_history()

    assert set(urls_manager.get_urls()["history"]) == {1}
