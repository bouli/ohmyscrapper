import ohmyscrapper.models.urls_manager as urls_manager
import pandas as pd
import time


def classify_urls(recursive=False):
    urls_manager.seeds()
    df = urls_manager.get_urls_valid_prefix()

    keep_alive = True
    while keep_alive:
        print("waking up!")
        for index, row_prefix in df.iterrows():
            df_urls = urls_manager.get_url_like_unclassified(row_prefix["url_prefix"])
            for index, row_urls in df_urls.iterrows():
                urls_manager.set_url_type_by_id(row_urls["id"], row_prefix["url_type"])

        if not recursive:
            print("ending...")
            keep_alive = False
        else:
            print("sleeping...")
            time.sleep(10)
