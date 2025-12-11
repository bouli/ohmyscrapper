import os
from urlextract import URLExtract
import ohmyscrapper.models.urls_manager as urls_manager


def load_txt(file_name="input/_chat.txt"):

    if not os.path.exists("input"):
        os.mkdir("input")

    urls_manager.create_tables()
    urls_manager.seeds()
    # make it recursive for all files
    text_file_content = open(file_name, "r").read()

    put_urls_from_string(text_file_content)

    # move_it_to_processed
    print("--------------------")
    print(file_name, "processed")


def put_urls_from_string(text_to_process, parent_id=None):
    if isinstance(text_to_process, str):
        extractor = URLExtract()
        for url in extractor.find_urls(text_to_process):
            urls_manager.add_url(url, parent_id=parent_id)
            print(url, "added")

        return len(extractor.find_urls(text_to_process))
    else:
        return 0
