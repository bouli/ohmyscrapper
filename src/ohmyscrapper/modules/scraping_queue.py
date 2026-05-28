from ohmyscrapper.core import config
from ohmyscrapper.models import urls_manager
from ohmyscrapper.modules import scrap_urls

try:
    from celery import Celery
except ImportError:
    Celery = None


DEFAULT_QUEUE_CONFIG = {
    "broker-url": "redis://localhost:6379/0",
    "result-backend": "redis://localhost:6379/0",
    "task-name": "ohmyscrapper.scrap_urls",
}


def get_queue_config(param):
    try:
        value = config.get_queue(param)
    except Exception:
        value = DEFAULT_QUEUE_CONFIG[param]
    if value is None or isinstance(value, bool):
        return DEFAULT_QUEUE_CONFIG[param]
    return value


def create_celery_app():
    if Celery is None:
        raise RuntimeError(
            "Queue mode requires Celery. Install OhMyScrapper with the queue extra."
        )

    app = Celery(
        "ohmyscrapper",
        broker=get_queue_config("broker-url"),
        backend=get_queue_config("result-backend"),
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
    )
    return app


celery_app = create_celery_app() if Celery is not None else None


def _scraping_options(
    recursive=False,
    ignore_valid_prefix=False,
    randomize=False,
    only_parents=True,
    verbose=False,
    run_command="scrap-urls:queue",
):
    return {
        "recursive": bool(recursive),
        "ignore_valid_prefix": bool(ignore_valid_prefix),
        "randomize": bool(randomize),
        "only_parents": bool(only_parents),
        "verbose": bool(verbose),
        "run_command": run_command,
    }


def run_scraping_worker(run_id, options=None):
    if options is None:
        options = {}
    options = _scraping_options(**options)
    scrap_urls.scrap_urls(
        recursive=options["recursive"],
        ignore_valid_prefix=options["ignore_valid_prefix"],
        randomize=options["randomize"],
        only_parents=options["only_parents"],
        verbose=options["verbose"],
        run_id=run_id,
        run_command=options["run_command"],
    )
    return {"run_id": run_id}


if celery_app is not None:

    @celery_app.task(name=get_queue_config("task-name"))
    def scrape_urls_task(run_id, options=None):
        return run_scraping_worker(run_id, options)

else:

    class _MissingCeleryTask:
        def delay(self, *args, **kwargs):
            raise RuntimeError(
                "Queue mode requires Celery. Install OhMyScrapper with the queue extra."
            )

    scrape_urls_task = _MissingCeleryTask()


def enqueue_scraping_run(
    recursive=False,
    ignore_valid_prefix=False,
    randomize=False,
    only_parents=True,
    verbose=False,
    run_command="scrap-urls:queue",
):
    options = _scraping_options(
        recursive=recursive,
        ignore_valid_prefix=ignore_valid_prefix,
        randomize=randomize,
        only_parents=only_parents,
        verbose=verbose,
        run_command=run_command,
    )
    run_id = urls_manager.create_scraping_run(command=run_command)
    task = scrape_urls_task.delay(run_id, options)
    return {
        "run_id": run_id,
        "task_id": getattr(task, "id", None),
    }
