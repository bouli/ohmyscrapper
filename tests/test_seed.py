from unittest.mock import Mock

import pandas as pd

from ohmyscrapper.modules import seed


def test_get_url_types_from_file_returns_empty_dict_when_config_is_empty(monkeypatch):
    monkeypatch.setattr(seed.config, "get_url_types", Mock(return_value=None))

    assert seed.get_url_types_from_file() == {}


def test_get_url_types_from_file_returns_configured_url_types(monkeypatch):
    url_types = {"job": "https://example.com/jobs/%"}
    monkeypatch.setattr(seed.config, "get_url_types", Mock(return_value=url_types))

    assert seed.get_url_types_from_file() == url_types


def test_seed_resets_existing_prefixes_when_requested(monkeypatch):
    reset_seeds = Mock()
    seeds = Mock()
    url_types = {"job": "https://example.com/jobs/%"}

    monkeypatch.setattr(seed.urls_manager, "reset_seeds", reset_seeds)
    monkeypatch.setattr(seed.config, "url_types_file_exists", Mock(return_value=True))
    monkeypatch.setattr(seed, "get_url_types_from_file", Mock(return_value=url_types))
    monkeypatch.setattr(seed.urls_manager, "seeds", seeds)

    result = seed.seed(reset=True)

    assert result is None
    reset_seeds.assert_called_once_with()
    seeds.assert_called_once_with(seeds=url_types)


def test_seed_exports_db_prefixes_when_url_types_file_is_missing(monkeypatch):
    db_url_types = pd.DataFrame(
        [{"url_type": "job", "url_prefix": "https://example.com/jobs/%"}]
    )
    export_url_types_to_file = Mock()
    seeds = Mock()

    monkeypatch.setattr(seed.config, "url_types_file_exists", Mock(return_value=False))
    monkeypatch.setattr(
        seed.urls_manager,
        "get_urls_valid_prefix",
        Mock(return_value=db_url_types),
    )
    monkeypatch.setattr(seed, "export_url_types_to_file", export_url_types_to_file)
    monkeypatch.setattr(seed.urls_manager, "seeds", seeds)

    result = seed.seed()

    assert result is None
    export_url_types_to_file.assert_called_once_with()
    seeds.assert_not_called()


def test_seed_reads_url_types_file_when_missing_file_has_no_db_prefixes(monkeypatch):
    url_types = {"company": "https://example.com/company/%"}
    seeds = Mock()

    monkeypatch.setattr(seed.config, "url_types_file_exists", Mock(return_value=False))
    monkeypatch.setattr(
        seed.urls_manager,
        "get_urls_valid_prefix",
        Mock(return_value=pd.DataFrame()),
    )
    monkeypatch.setattr(seed, "get_url_types_from_file", Mock(return_value=url_types))
    monkeypatch.setattr(seed.urls_manager, "seeds", seeds)

    seed.seed()

    seeds.assert_called_once_with(seeds=url_types)


def test_seed_does_not_seed_when_url_types_file_is_empty(monkeypatch):
    seeds = Mock()

    monkeypatch.setattr(seed.config, "url_types_file_exists", Mock(return_value=True))
    monkeypatch.setattr(seed, "get_url_types_from_file", Mock(return_value={}))
    monkeypatch.setattr(seed.urls_manager, "seeds", seeds)

    seed.seed()

    seeds.assert_not_called()


def test_export_url_types_to_file_writes_prefixes_as_yaml_mapping(monkeypatch):
    append_url_types = Mock()
    monkeypatch.setattr(
        seed.urls_manager,
        "get_urls_valid_prefix",
        Mock(
            return_value=pd.DataFrame(
                [
                    {
                        "url_type": "job",
                        "url_prefix": "https://example.com/jobs/%",
                    },
                    {
                        "url_type": "company",
                        "url_prefix": "https://example.com/company/%",
                    },
                ]
            )
        ),
    )
    monkeypatch.setattr(seed.config, "append_url_types", append_url_types)

    result = seed.export_url_types_to_file()

    assert result is None
    append_url_types.assert_called_once_with(
        {
            "job": "https://example.com/jobs/%",
            "company": "https://example.com/company/%",
        }
    )
