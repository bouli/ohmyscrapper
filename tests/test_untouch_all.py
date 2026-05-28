from unittest.mock import Mock

from ohmyscrapper.modules import untouch_all


def test_untouch_all_delegates_to_urls_manager(monkeypatch, capsys):
    untouch_all_urls = Mock()
    monkeypatch.setattr(
        untouch_all.urls_manager,
        "untouch_all_urls",
        untouch_all_urls,
    )

    result = untouch_all.untouch_all()

    assert result is None
    untouch_all_urls.assert_called_once_with()
    assert "urls have been untouched" in capsys.readouterr().out


def test_untouch_all_urls_with_errors_delegates_to_urls_manager(
    monkeypatch,
    capsys,
):
    untouch_all_urls_with_errors = Mock()
    monkeypatch.setattr(
        untouch_all.urls_manager,
        "untouch_all_urls_with_errors",
        untouch_all_urls_with_errors,
    )

    result = untouch_all.untouch_all_urls_with_errors()

    assert result is None
    untouch_all_urls_with_errors.assert_called_once_with()
    assert "urls with errors have been untouched" in capsys.readouterr().out
