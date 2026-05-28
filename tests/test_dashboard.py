import sqlite3
import sys
from unittest.mock import Mock

import pytest

import ohmyscrapper
from ohmyscrapper.models import urls_manager
from ohmyscrapper.modules import dashboard


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "local.db"
    monkeypatch.setattr(urls_manager, "get_db_path", lambda: str(path))
    monkeypatch.setattr(urls_manager.time, "time", lambda: 1700000000)
    return path


def test_dashboard_data_reads_persisted_runs_and_recent_url_errors(db_path):
    run_id = urls_manager.create_scraping_run(command="scrap-urls", total_urls=3)
    urls_manager.increment_scraping_run_counter(run_id, "completed_count")
    urls_manager.increment_scraping_run_counter(run_id, "failure_count")
    urls_manager.finish_scraping_run(run_id, status="completed")
    urls_manager.add_url("https://example.com/failing")
    urls_manager.set_url_error("https://example.com/failing", "error timeout")
    urls_manager.touch_url("https://example.com/failing")

    runs = dashboard.get_dashboard_runs(limit=5)
    run = dashboard.get_dashboard_run(run_id)
    errors = dashboard.get_dashboard_errors(limit=5)

    assert runs[0]["id"] == run_id
    assert run["status"] == "completed"
    assert run["completed_count"] == 1
    assert run["failure_count"] == 1
    assert errors[0]["url"] == "https://example.com/failing"
    assert errors[0]["error"] == "error timeout"


def test_dashboard_renders_recent_run_state_and_detail_errors(db_path):
    run_id = urls_manager.create_scraping_run(command="start", total_urls=4)
    urls_manager.increment_scraping_run_counter(run_id, "completed_count", amount=2)
    urls_manager.increment_scraping_run_counter(run_id, "skipped_count")
    urls_manager.increment_scraping_run_counter(run_id, "failure_count")
    urls_manager.add_url("https://example.com/broken")
    urls_manager.set_url_error("https://example.com/broken", "error blocked")
    urls_manager.touch_url("https://example.com/broken")

    index_html = dashboard.render_runs_page()
    detail_html = dashboard.render_run_detail_page(run_id)

    assert f"Run #{run_id}" in detail_html
    assert "start" in index_html
    assert "running" in index_html
    assert "4/4 (100%)" in index_html
    assert "Recent Scrape Errors" in detail_html
    assert "https://example.com/broken" in detail_html
    assert "error blocked" in detail_html


def test_get_recent_url_errors_orders_by_recent_touch(db_path):
    urls_manager.add_url("https://example.com/old")
    urls_manager.set_url_error("https://example.com/old", "error old")
    urls_manager.touch_url("https://example.com/old")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE urls SET last_touch = ? WHERE url = ?",
            (1699999999, "https://example.com/old"),
        )

    urls_manager.add_url("https://example.com/new")
    urls_manager.set_url_error("https://example.com/new", "error new")
    urls_manager.touch_url("https://example.com/new")

    errors = urls_manager.get_recent_url_errors(limit=1)

    assert errors.iloc[0]["url"] == "https://example.com/new"


def test_dashboard_command_starts_server_with_host_and_port(monkeypatch):
    start_dashboard = Mock()
    monkeypatch.setattr(ohmyscrapper, "update", Mock())
    monkeypatch.setattr(ohmyscrapper, "start_dashboard", start_dashboard)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ohmyscrapper", "dashboard", "--host", "0.0.0.0", "--port", "9999"],
    )

    ohmyscrapper.main()

    start_dashboard.assert_called_once_with(host="0.0.0.0", port=9999)
