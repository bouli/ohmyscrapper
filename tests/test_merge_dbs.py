from unittest.mock import Mock

from ohmyscrapper.modules import merge_dbs


def test_merge_dbs_delegates_to_urls_manager(monkeypatch):
    urls_manager_merge_dbs = Mock()
    monkeypatch.setattr(
        merge_dbs.urls_manager,
        "merge_dbs",
        urls_manager_merge_dbs,
    )

    result = merge_dbs.merge_dbs()

    assert result is None
    urls_manager_merge_dbs.assert_called_once_with()
