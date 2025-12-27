import yaml
import os

def get_dir(param="ohmyscrapper"):
    parent_param = 'default_dirs'

    if param == "ohmyscrapper":
        folder = "./" + param
    else:
        folder = get_param(parent_param, param)
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder

def get_files(param):
    parent_param = 'default_files'
    return get_param(parent_param, param)

def get_db(param="db_file"):
    if param == 'folder':
        return get_dir(param='db')
    return get_param(parent_param = 'db', param=param)

def get_ai(param):
    return get_param(parent_param = 'ai', param=param)

def load_config(force_default=False):
    config_file_name = "config.yaml"
    config_params = create_and_read_config_file(file_name=config_file_name, force_default=force_default)

    if config_params is None or "default_dirs" not in config_params:
        config_params = load_config(force_default=True)

    return config_params

def create_and_read_config_file(file_name, force_default=False):
    customize_folder = "ohmyscrapper"
    if not os.path.exists(customize_folder):
        os.mkdir(customize_folder)

    config_file = os.path.join(customize_folder, file_name)
    if force_default or not os.path.exists(config_file):
        with open(config_file, "+w") as f:
            config_params = get_default_file(default_file=file_name)
            f.write(yaml.safe_dump(config_params))
    else:
        with open(config_file, "r") as f:
            config_params = yaml.safe_load(f.read())
    return config_params

def get_param(parent_param, param):
    default_dirs = load_config()[parent_param]
    if param in default_dirs:
        return default_dirs[param]
    else:
        raise Exception(f"{param} do not exist in your params {parent_param}.")

def get_default_file(default_file):
    default_files_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'default_files')
    default_file = os.path.join(default_files_dir, default_file)
    with open(default_file, "r") as f:
        return yaml.safe_load(f.read())


def update():
    legacy_folder = "./customize"
    new_folder = "./ohmyscrapper"
    if os.path.exists(legacy_folder) and not os.path.exists(new_folder):
        yes_no = input("We detected a legacy folder system for your OhMyScrapper, would you like to update? \n" \
        "If you don't update, a new version will be used and your legacy folder will be ignored. \n" \
        "[Y] for yes or  any other thing to ignore: ")
        if yes_no == "Y":
            os.rename(legacy_folder,new_folder)
        print(" You are up-to-date! =)")
        print("")
