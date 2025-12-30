import ohmyscrapper.models.urls_manager as urls_manager
from ohmyscrapper.core import config


def seed(reset=False):
    if reset:
        urls_manager.reset_seeds()

    if not config.url_types_file_exists():
        db_url_types = urls_manager.get_urls_valid_prefix()
        if len(db_url_types) > 0:
            export_url_types_to_file()
            print("🪹 you have a new `url_types.yaml` based on your db! =)")
            return

    seeds = get_url_types_from_file()

    if len(seeds) > 0:
        urls_manager.seeds(seeds=seeds)
        print("🫒 db seeded")
    return


def get_url_types_from_file():
    url_types_from_file = config.get_url_types()
    if url_types_from_file is None:
        url_types_from_file = {}
    return url_types_from_file


def export_url_types_to_file():
    url_types = urls_manager.get_urls_valid_prefix()
    yaml_url_types = {}
    for index, url_type in url_types.iterrows():
        yaml_url_types[url_type["url_type"]] = url_type["url_prefix"]
    config.append_url_types(yaml_url_types)
