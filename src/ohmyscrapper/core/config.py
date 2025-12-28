import os
from ohmyscrapper.core import config_files

default_app_dir = "ohmyscrapper"


def get_dir(param="ohmyscrapper"):
    parent_param = "default_dirs"

    if param == default_app_dir:
        folder = "./" + param
    else:
        folder = config_files.get_param(
            parent_param=parent_param, param=param, default_app_dir=default_app_dir
        )
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder


def get_files(param):
    parent_param = "default_files"
    return config_files.get_param(
        parent_param=parent_param, param=param, default_app_dir=default_app_dir
    )


def get_db(param="db_file"):
    if param == "folder":
        return get_dir(param="db")
    return config_files.get_param(
        parent_param="db", param=param, default_app_dir=default_app_dir
    )


def get_ai(param):
    return config_files.get_param(
        parent_param="ai", param=param, default_app_dir=default_app_dir
    )


def load_config(force_default=False):
    config_file_name = "config.yaml"
    config_params = config_files.create_and_read_config_file(
        file_name=config_file_name,
        default_app_dir=default_app_dir,
        force_default=force_default,
    )

    if config_params is None or "default_dirs" not in config_params:
        config_params = load_config(force_default=True)

    return config_params


def url_types_file_exists():
    url_types_file = get_files("url_types")
    return config_files.config_file_exists(
        url_types_file, default_app_dir=default_app_dir
    )


def get_url_types():
    url_types_file = get_files("url_types")
    return config_files.create_and_read_config_file(
        url_types_file, default_app_dir=default_app_dir
    )


def get_url_sniffing():
    file = get_files("url_sniffing")
    return config_files.create_and_read_config_file(
        file, default_app_dir=default_app_dir
    )


def append_url_sniffing(data):
    file = get_files("url_sniffing")
    _append_config_file(data, file)


def append_url_types(url_types):
    url_types_file = get_files("url_types")
    _append_config_file(url_types, url_types_file)


def overwrite_config_file(data, file_name):
    config_files.overwrite_config_file(data, file_name, default_app_dir=default_app_dir)


def _append_config_file(data, file_name):
    config_files.append_config_file(data, file_name, default_app_dir=default_app_dir)


def update():
    legacy_folder = "./customize"
    new_folder = "./ohmyscrapper"
    if os.path.exists(legacy_folder) and not os.path.exists(new_folder):
        yes_no = input(
            "We detected a legacy folder system for your OhMyScrapper, would you like to update? \n"
            "If you don't update, a new version will be used and your legacy folder will be ignored. \n"
            "[Y] for yes or  any other thing to ignore: "
        )
        if yes_no == "Y":
            os.rename(legacy_folder, new_folder)
        print(" You are up-to-date! =)")
        print("")
