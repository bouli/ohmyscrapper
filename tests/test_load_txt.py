from unittest.mock import Mock, call

import pytest

from ohmyscrapper.modules import load_txt


@pytest.fixture
def input_dir(tmp_path, monkeypatch):
    folder = tmp_path / "input"
    folder.mkdir()
    monkeypatch.setattr(load_txt.config, "get_dir", Mock(return_value=str(folder)))
    return folder


@pytest.fixture
def patched_url_manager(monkeypatch):
    seeds = Mock()
    add_url = Mock()
    untouch_url = Mock()

    monkeypatch.setattr(load_txt.urls_manager, "seeds", seeds)
    monkeypatch.setattr(load_txt.urls_manager, "add_url", add_url)
    monkeypatch.setattr(load_txt.urls_manager, "untouch_url", untouch_url)

    return {
        "seeds": seeds,
        "add_url": add_url,
        "untouch_url": untouch_url,
    }


def test_increment_file_name_appends_file_content(tmp_path):
    text_file = tmp_path / "jobs.txt"
    text_file.write_text(" https://example.com/job ", encoding="utf-8")

    result = load_txt._increment_file_name("prefix", str(text_file))

    assert result == "prefix\n https://example.com/job "


def test_put_urls_from_string_extracts_urls_and_preserves_parent(
    monkeypatch,
    capsys,
):
    add_url = Mock()
    monkeypatch.setattr(load_txt.urls_manager, "add_url", add_url)

    count = load_txt.put_urls_from_string(
        "Read https://example.com/jobs and https://example.org/company today.",
        parent_url="https://example.com/source",
        verbose=True,
    )

    assert count == 2
    assert add_url.call_args_list == [
        call(url="https://example.com/jobs", parent_url="https://example.com/source"),
        call(
            url="https://example.org/company",
            parent_url="https://example.com/source",
        ),
    ]
    assert "https://example.com/jobs added" in capsys.readouterr().out


@pytest.mark.parametrize("value", [None, 42, ["https://example.com"]])
def test_put_urls_from_string_ignores_non_strings(monkeypatch, value):
    add_url = Mock()
    monkeypatch.setattr(load_txt.urls_manager, "add_url", add_url)

    assert load_txt.put_urls_from_string(value) == 0
    add_url.assert_not_called()


def test_load_txt_reads_single_file_and_loads_found_urls(
    input_dir,
    patched_url_manager,
):
    text_file = input_dir / "jobs.txt"
    text_file.write_text("Apply at https://example.com/jobs/123", encoding="utf-8")

    load_txt.load_txt(file_name=str(text_file))

    patched_url_manager["seeds"].assert_called_once_with()
    patched_url_manager["add_url"].assert_called_once_with(
        url="https://example.com/jobs/123",
        parent_url=None,
    )
    patched_url_manager["untouch_url"].assert_not_called()


def test_load_txt_treats_url_input_as_content_and_untouches_it(
    input_dir,
    patched_url_manager,
):
    url = "https://example.com/jobs/123"

    load_txt.load_txt(file_name=url)

    patched_url_manager["seeds"].assert_called_once_with()
    patched_url_manager["untouch_url"].assert_called_once_with(url=url)
    patched_url_manager["add_url"].assert_called_once_with(url=url, parent_url=None)


def test_load_txt_returns_when_named_file_is_missing(
    input_dir,
    patched_url_manager,
    capsys,
):
    missing_file = input_dir / "missing.txt"

    result = load_txt.load_txt(file_name=str(missing_file))

    assert result is None
    patched_url_manager["seeds"].assert_called_once_with()
    patched_url_manager["add_url"].assert_not_called()
    assert f"file `{missing_file}` not found" in capsys.readouterr().out


def test_load_txt_reads_default_directory_when_file_name_is_none(
    input_dir,
    patched_url_manager,
):
    (input_dir / "jobs.txt").write_text(
        "Apply at https://example.com/jobs/123",
        encoding="utf-8",
    )

    load_txt.load_txt(file_name=None)

    patched_url_manager["add_url"].assert_called_once_with(
        url="https://example.com/jobs/123",
        parent_url=None,
    )


def test_load_txt_returns_when_directory_has_no_text_files(
    input_dir,
    patched_url_manager,
    capsys,
):
    (input_dir / "notes.md").write_text("https://example.com/jobs", encoding="utf-8")

    result = load_txt.load_txt(file_name=str(input_dir))

    assert result is None
    patched_url_manager["seeds"].assert_called_once_with()
    patched_url_manager["add_url"].assert_not_called()
    assert "No text files found" in capsys.readouterr().out


def test_load_txt_allows_user_to_pick_one_file_from_directory(
    input_dir,
    patched_url_manager,
    monkeypatch,
):
    (input_dir / "first.txt").write_text("https://example.com/first", encoding="utf-8")
    (input_dir / "second.txt").write_text(
        "https://example.com/second",
        encoding="utf-8",
    )
    monkeypatch.setattr("builtins.input", Mock(return_value="1"))

    load_txt.load_txt(file_name=str(input_dir))

    patched_url_manager["add_url"].assert_called_once_with(
        url="https://example.com/second",
        parent_url=None,
    )


def test_load_txt_can_process_all_text_files_from_directory(
    input_dir,
    patched_url_manager,
    monkeypatch,
):
    (input_dir / "first.txt").write_text("https://example.com/first", encoding="utf-8")
    (input_dir / "second.txt").write_text(
        "https://example.com/second",
        encoding="utf-8",
    )
    monkeypatch.setattr("builtins.input", Mock(return_value="*"))

    load_txt.load_txt(file_name=str(input_dir))

    assert patched_url_manager["add_url"].call_args_list == [
        call(url="https://example.com/first", parent_url=None),
        call(url="https://example.com/second", parent_url=None),
    ]


def test_load_txt_can_quit_file_selection_without_processing(
    input_dir,
    patched_url_manager,
    monkeypatch,
):
    (input_dir / "first.txt").write_text("https://example.com/first", encoding="utf-8")
    (input_dir / "second.txt").write_text(
        "https://example.com/second",
        encoding="utf-8",
    )
    monkeypatch.setattr("builtins.input", Mock(return_value="q"))

    result = load_txt.load_txt(file_name=str(input_dir))

    assert result is None
    patched_url_manager["add_url"].assert_not_called()
