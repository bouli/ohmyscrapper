from unittest.mock import Mock, call

import pandas as pd

from ohmyscrapper.modules import show


def urls_dataframe():
    return pd.DataFrame(
        [
            {
                "id": 1,
                "url": "https://example.com/job",
                "title": "Engineer",
                "description": "Line 1\nLine 2",
                "json": '{"ok": true}',
            }
        ]
    )


def test_export_urls_writes_csv_and_html_preview(tmp_path, monkeypatch):
    monkeypatch.setattr(show.config, "get_dir", Mock(return_value=str(tmp_path)))
    get_urls = Mock(return_value=urls_dataframe())
    monkeypatch.setattr(show.urls_manager, "get_urls", get_urls)

    show.export_urls(limit=5, csv_file="urls.csv")

    csv_file = tmp_path / "urls.csv"
    preview_file = tmp_path / "urls.csv-preview.html"

    get_urls.assert_called_once_with(limit=5)
    assert csv_file.exists()
    assert preview_file.exists()
    assert "Line 1\nLine 2" in csv_file.read_text(encoding="utf-8")
    assert "Line 1 Line 2" in preview_file.read_text(encoding="utf-8")


def test_export_urls_simplify_drops_description_and_json(tmp_path, monkeypatch):
    monkeypatch.setattr(show.config, "get_dir", Mock(return_value=str(tmp_path)))
    monkeypatch.setattr(
        show.urls_manager,
        "get_urls",
        Mock(return_value=urls_dataframe()),
    )

    show.export_urls(csv_file="simplified.csv", simplify=True)

    csv_content = (tmp_path / "simplified.csv").read_text(encoding="utf-8")
    preview_content = (tmp_path / "simplified.csv-preview.html").read_text(
        encoding="utf-8"
    )

    assert "description" not in csv_content
    assert "json" not in csv_content
    assert "description" not in preview_content
    assert "json" not in preview_content


def test_export_report_writes_and_cleans_csv_and_html(tmp_path, monkeypatch):
    report = pd.DataFrame(
        [
            {
                "id": 1,
                "url": "https://example.com/job",
                "title": "Engineer -  - Remote",
                "description": "Line 1\nLine 2",
            }
        ]
    )
    monkeypatch.setattr(show.config, "get_dir", Mock(return_value=str(tmp_path)))
    get_urls_report = Mock(return_value=report)
    monkeypatch.setattr(show.urls_manager, "get_urls_report", get_urls_report)

    show.export_report(csv_file="report.csv")

    csv_file = tmp_path / "report.csv"
    preview_file = tmp_path / "report.csv-preview.html"

    get_urls_report.assert_called_once_with()
    assert "Engineer - Remote" in csv_file.read_text(encoding="utf-8")
    assert "Line 1 Line 2" in preview_file.read_text(encoding="utf-8")


def test_clear_file_removes_known_export_artifacts(tmp_path):
    output_file = tmp_path / "report.html"
    output_file.write_text("A -  - B -<td>C", encoding="utf-8")

    show._clear_file(str(output_file))

    assert output_file.read_text(encoding="utf-8") == "A - B<td>C"


def test_show_table_builds_rich_table(monkeypatch):
    printed = Mock()
    console = Mock()
    console.print = printed
    monkeypatch.setattr(show, "Console", Mock(return_value=console))

    show.show_table(pd.DataFrame([{"id": 1, "title": "Engineer"}]))

    printed.assert_called_once()
    table = printed.call_args.args[0]
    assert [column.header for column in table.columns] == ["id", "title"]


def test_show_urls_prints_first_page_and_quits(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "id": index,
                "url": f"https://example.com/{index}",
                "json": "{}",
                "description": "description",
            }
            for index in range(20)
        ]
    )
    show_table = Mock()
    monkeypatch.setattr(show.urls_manager, "get_urls", Mock(return_value=df))
    monkeypatch.setattr(show, "show_table", show_table)
    monkeypatch.setattr("builtins.input", Mock(return_value="q"))

    result = show.show_urls(limit=20)

    assert result is None
    show.urls_manager.get_urls.assert_called_once_with(limit=20)
    show_table.assert_called_once()
    shown_page = show_table.call_args.args[0]
    assert len(shown_page) == 15
    assert "json" not in shown_page.columns
    assert "description" not in shown_page.columns


def test_show_urls_accepts_numeric_page_jump(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "id": index,
                "url": f"https://example.com/{index}",
                "json": "{}",
                "description": "description",
            }
            for index in range(20)
        ]
    )
    recursive_show_urls = Mock()
    original_show_urls = show.show_urls
    monkeypatch.setattr(show.urls_manager, "get_urls", Mock(return_value=df))
    monkeypatch.setattr(show, "show_table", Mock())
    monkeypatch.setattr("builtins.input", Mock(return_value="2"))
    monkeypatch.setattr(show, "show_urls", recursive_show_urls)

    original_show_urls(limit=20)

    recursive_show_urls.assert_called_once_with(limit=20, jump_to_page=1)


def test_show_urls_reports_invalid_page_number(monkeypatch, capsys):
    df = pd.DataFrame(
        [
            {
                "id": index,
                "url": f"https://example.com/{index}",
                "json": "{}",
                "description": "description",
            }
            for index in range(5)
        ]
    )
    monkeypatch.setattr(show.urls_manager, "get_urls", Mock(return_value=df))
    monkeypatch.setattr(show, "show_table", Mock())
    monkeypatch.setattr("builtins.input", Mock(side_effect=["9"]))

    show.show_urls()

    assert "This page does not exist" in capsys.readouterr().out


def test_show_urls_valid_prefix_prints_dataframe(monkeypatch, capsys):
    prefixes = pd.DataFrame([{"url_type": "job", "url_prefix": "https://%"}])
    monkeypatch.setattr(
        show.urls_manager,
        "get_urls_valid_prefix",
        Mock(return_value=prefixes),
    )

    result = show.show_urls_valid_prefix(limit=3)

    assert result is None
    show.urls_manager.get_urls_valid_prefix.assert_called_once_with(limit=3)
    assert "url_type" in capsys.readouterr().out


def test_show_url_prints_transposed_url_row(monkeypatch, capsys):
    row = pd.DataFrame([{"url": "https://example.com/job", "title": "Engineer"}])
    monkeypatch.setattr(
        show.urls_manager,
        "get_url_by_url",
        Mock(return_value=row),
    )

    result = show.show_url("https://example.com/job")

    assert result is None
    show.urls_manager.get_url_by_url.assert_called_once_with(
        url="https://example.com/job"
    )
    assert "Engineer" in capsys.readouterr().out
