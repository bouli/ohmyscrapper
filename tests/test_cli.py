import io
import sys
from contextlib import redirect_stdout
from unittest.mock import Mock, call

import pytest

import ohmyscrapper


def run_cli(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["ohmyscrapper", *args])
    ohmyscrapper.main()


def patch_attr(monkeypatch, obj, name, replacement=None):
    if replacement is None:
        replacement = Mock()
    monkeypatch.setattr(obj, name, replacement)
    return replacement


def run_cli_with_common_patches(monkeypatch, *args):
    update = patch_attr(monkeypatch, ohmyscrapper, "update")

    run_cli(monkeypatch, *args)

    update.assert_called_once_with()


def test_version_prints_package_version(monkeypatch):
    output = io.StringIO()
    update = patch_attr(monkeypatch, ohmyscrapper, "update")
    monkeypatch.setattr(sys, "argv", ["ohmyscrapper", "--version"])

    with redirect_stdout(output):
        with pytest.raises(SystemExit) as exit_context:
            ohmyscrapper.main()

    assert exit_context.value.code == 0
    assert output.getvalue().strip() == "ohmyscrapper v0.10.2"
    update.assert_called_once_with()


def test_classify_urls_command_forwards_recursive_flag(monkeypatch):
    classify_urls = patch_attr(monkeypatch, ohmyscrapper, "classify_urls")

    run_cli_with_common_patches(monkeypatch, "classify-urls", "--recursive")

    classify_urls.assert_called_once_with(True)


def test_load_command_forwards_input_and_verbose_flags(monkeypatch):
    load_txt = patch_attr(monkeypatch, ohmyscrapper, "load_txt")

    run_cli_with_common_patches(monkeypatch, "load", "-input", "jobs.txt", "--verbose")

    load_txt.assert_called_once_with(file_name="jobs.txt", verbose=True)


def test_seed_command_can_export_instead_of_seeding(monkeypatch):
    export = patch_attr(monkeypatch, ohmyscrapper, "export_url_types_to_file")
    seed = patch_attr(monkeypatch, ohmyscrapper, "seed")

    run_cli_with_common_patches(monkeypatch, "seed", "--export")

    export.assert_called_once_with()
    seed.assert_not_called()


def test_seed_command_forwards_reset_flag(monkeypatch):
    seed = patch_attr(monkeypatch, ohmyscrapper, "seed")

    run_cli_with_common_patches(monkeypatch, "seed", "--reset")

    seed.assert_called_once_with(True)


@pytest.mark.parametrize(
    ("command", "handler_name"),
    [
        ("untouch-all", "untouch_all"),
        ("report", "export_report"),
        ("merge_dbs", "merge_dbs"),
    ],
)
def test_simple_commands_call_their_handlers(
    monkeypatch, command, handler_name
):
    handler = patch_attr(monkeypatch, ohmyscrapper, handler_name)

    run_cli_with_common_patches(monkeypatch, command)

    handler.assert_called_once_with()


def test_untouch_errors_command_excludes_warnings_by_default(monkeypatch):
    untouch_all_urls_with_errors = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "untouch_all_urls_with_errors",
    )

    run_cli_with_common_patches(monkeypatch, "untouch-errors")

    untouch_all_urls_with_errors.assert_called_once_with(include_warnings=False)


def test_untouch_errors_command_can_include_warnings(monkeypatch):
    untouch_all_urls_with_errors = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "untouch_all_urls_with_errors",
    )

    run_cli_with_common_patches(monkeypatch, "untouch-errors", "--include-warnings")

    untouch_all_urls_with_errors.assert_called_once_with(include_warnings=True)


def test_sniff_url_command_builds_sniffing_config(monkeypatch):
    sniff_url = patch_attr(monkeypatch, ohmyscrapper, "sniff_url")

    run_cli_with_common_patches(
        monkeypatch,
        "sniff-url",
        "https://example.com",
        "--metatags",
        "description,og:title",
        "--bodytags",
        "h1,h2",
    )

    sniff_url.assert_called_once_with(
        "https://example.com",
        sniffing_config={
            "metatags": ["description", "og:title"],
            "bodytags": ["h1", "h2"],
        },
    )


def test_scrap_urls_command_loads_optional_input_then_scrapes(monkeypatch):
    load_txt = patch_attr(monkeypatch, ohmyscrapper, "load_txt")
    scrap_urls = patch_attr(monkeypatch, ohmyscrapper, "scrap_urls")

    run_cli_with_common_patches(
        monkeypatch,
        "scrap-urls",
        "-input",
        "jobs.txt",
        "--recursive",
        "--ignore-type",
        "--randomize",
        "--only-parents",
        "--verbose",
    )

    load_txt.assert_called_once_with(file_name="jobs.txt", verbose=True)
    scrap_urls.assert_called_once_with(
        recursive=True,
        ignore_valid_prefix=True,
        randomize=True,
        only_parents=True,
        verbose=True,
    )


def test_scrap_urls_command_can_enqueue_work(monkeypatch):
    load_txt = patch_attr(monkeypatch, ohmyscrapper, "load_txt")
    scrap_urls = patch_attr(monkeypatch, ohmyscrapper, "scrap_urls")
    enqueue_scraping_run = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "enqueue_scraping_run",
        Mock(return_value={"run_id": 12, "task_id": "task-12"}),
    )

    run_cli_with_common_patches(
        monkeypatch,
        "scrap-urls",
        "-input",
        "jobs.txt",
        "--queue",
        "--recursive",
        "--ignore-type",
        "--randomize",
        "--only-parents",
        "--verbose",
    )

    load_txt.assert_called_once_with(file_name="jobs.txt", verbose=True)
    enqueue_scraping_run.assert_called_once_with(
        recursive=True,
        ignore_valid_prefix=True,
        randomize=True,
        only_parents=True,
        verbose=True,
    )
    scrap_urls.assert_not_called()


@pytest.mark.parametrize(
    ("args", "handler_name", "expected_args"),
    [
        (("show", "--prefixes", "--limit", "3"), "show_urls_valid_prefix", (3,)),
        (
            ("show", "-url", "https://example.com"),
            "show_url",
            ("https://example.com",),
        ),
        (("show", "--limit", "5"), "show_urls", (5,)),
    ],
)
def test_show_command_routes_to_prefixes_url_or_table(
    monkeypatch, args, handler_name, expected_args
):
    handler = patch_attr(monkeypatch, ohmyscrapper, handler_name)

    run_cli_with_common_patches(monkeypatch, *args)

    handler.assert_called_once_with(*expected_args)


def test_export_command_forwards_limit_file_and_simplify(monkeypatch):
    export_urls = patch_attr(monkeypatch, ohmyscrapper, "export_urls")

    run_cli_with_common_patches(
        monkeypatch,
        "export",
        "--limit",
        "7",
        "--file",
        "custom.csv",
        "--simplify",
    )

    export_urls.assert_called_once_with(limit=7, csv_file="custom.csv", simplify=True)


def test_ai_command_processes_current_urls(monkeypatch):
    process_with_ai = patch_attr(monkeypatch, ohmyscrapper, "process_with_ai")

    run_cli_with_common_patches(monkeypatch, "ai", "--i-am-rich")

    process_with_ai.assert_called_once_with(bypass_budget_control=True)


def test_ai_command_can_reprocess_history(monkeypatch):
    reprocess = patch_attr(monkeypatch, ohmyscrapper, "reprocess_ai_history")
    process_with_ai = patch_attr(monkeypatch, ohmyscrapper, "process_with_ai")

    run_cli_with_common_patches(monkeypatch, "ai", "--history")

    reprocess.assert_called_once_with()
    process_with_ai.assert_not_called()


def test_start_command_runs_full_pipeline_with_ai_when_requested(monkeypatch):
    events = Mock()

    patch_attr(
        monkeypatch,
        ohmyscrapper,
        "seed",
        Mock(side_effect=lambda: events("seed")),
    )
    load_txt = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "load_txt",
        Mock(side_effect=lambda **kwargs: events("load", kwargs)),
    )
    scrap_urls = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "scrap_urls",
        Mock(side_effect=lambda **kwargs: events("scrap", kwargs)),
    )
    process_with_ai = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "process_with_ai",
        Mock(side_effect=lambda **kwargs: events("ai", kwargs)),
    )
    export_urls = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "export_urls",
        Mock(side_effect=lambda **kwargs: events("export", kwargs)),
    )
    export_report = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "export_report",
        Mock(side_effect=lambda: events("report")),
    )

    run_cli_with_common_patches(
        monkeypatch,
        "start",
        "-input",
        "jobs.txt",
        "--ai",
        "--i-am-rich",
    )

    load_txt.assert_called_once_with(file_name="jobs.txt")
    scrap_urls.assert_called_once_with(
        recursive=True,
        ignore_valid_prefix=True,
        randomize=False,
        only_parents=False,
        run_command="start",
    )
    process_with_ai.assert_called_once_with(bypass_budget_control=True)
    assert export_urls.call_args_list == [
        call(),
        call(csv_file="urls-simplified.csv", simplify=True),
    ]
    export_report.assert_called_once_with()
    assert events.call_args_list == [
        call("seed"),
        call("load", {"file_name": "jobs.txt"}),
        call(
            "scrap",
            {
                "recursive": True,
                "ignore_valid_prefix": True,
                "randomize": False,
                "only_parents": False,
                "run_command": "start",
            },
        ),
        call("ai", {"bypass_budget_control": True}),
        call("export", {}),
        call("export", {"csv_file": "urls-simplified.csv", "simplify": True}),
        call("report"),
    ]


def test_start_command_uses_default_load_and_skips_ai_by_default(monkeypatch):
    patch_attr(monkeypatch, ohmyscrapper, "seed")
    load_txt = patch_attr(monkeypatch, ohmyscrapper, "load_txt")
    patch_attr(monkeypatch, ohmyscrapper, "scrap_urls")
    process_with_ai = patch_attr(monkeypatch, ohmyscrapper, "process_with_ai")
    patch_attr(monkeypatch, ohmyscrapper, "export_urls")
    patch_attr(monkeypatch, ohmyscrapper, "export_report")

    run_cli_with_common_patches(monkeypatch, "start")

    load_txt.assert_called_once_with()
    process_with_ai.assert_not_called()


def test_cleancache_command_cleans_configured_cache(monkeypatch):
    cache = Mock()
    cache_factory = patch_attr(
        monkeypatch,
        ohmyscrapper,
        "unforgettable",
        Mock(return_value=cache),
    )
    patch_attr(
        monkeypatch,
        ohmyscrapper.config,
        "get_dir",
        Mock(return_value="cache-dir"),
    )

    run_cli_with_common_patches(monkeypatch, "cleancache")

    cache_factory.assert_called_once_with(cache_folder="cache-dir")
    cache.clean.assert_called_once_with()
