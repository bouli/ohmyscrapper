from types import SimpleNamespace
from unittest.mock import Mock

from ohmyscrapper.modules import scraping_queue


def test_enqueue_scraping_run_creates_run_and_delays_task(monkeypatch):
    create_run = Mock(return_value=42)
    task = SimpleNamespace(id="task-42")
    delayed_task = SimpleNamespace(delay=Mock(return_value=task))
    monkeypatch.setattr(scraping_queue.urls_manager, "create_scraping_run", create_run)
    monkeypatch.setattr(scraping_queue, "scrape_urls_task", delayed_task)

    result = scraping_queue.enqueue_scraping_run(
        recursive=True,
        ignore_valid_prefix=True,
        randomize=True,
        only_parents=False,
        verbose=True,
    )

    create_run.assert_called_once_with(command="scrap-urls:queue")
    delayed_task.delay.assert_called_once_with(
        42,
        {
            "recursive": True,
            "ignore_valid_prefix": True,
            "randomize": True,
            "only_parents": False,
            "verbose": True,
            "run_command": "scrap-urls:queue",
        },
    )
    assert result == {"run_id": 42, "task_id": "task-42"}


def test_run_scraping_worker_uses_persisted_run_id(monkeypatch):
    scrap_urls = Mock()
    monkeypatch.setattr(scraping_queue.scrap_urls, "scrap_urls", scrap_urls)

    result = scraping_queue.run_scraping_worker(
        7,
        {
            "recursive": True,
            "ignore_valid_prefix": True,
            "randomize": True,
            "only_parents": False,
            "verbose": True,
        },
    )

    scrap_urls.assert_called_once_with(
        recursive=True,
        ignore_valid_prefix=True,
        randomize=True,
        only_parents=False,
        verbose=True,
        run_id=7,
        run_command="scrap-urls:queue",
    )
    assert result == {"run_id": 7}


def test_missing_celery_task_reports_optional_dependency():
    task = scraping_queue._MissingCeleryTask()

    try:
        task.delay(1, {})
    except RuntimeError as exc:
        assert "requires Celery" in str(exc)
    else:
        raise AssertionError("Missing Celery task should raise RuntimeError")
