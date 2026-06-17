import glob
import sqlite3

import pandas as pd


def merge_dbs(get_db_path, get_db_dir, merge_url):
    production_db_file = get_db_path()
    db_number = -1
    db_dir = get_db_dir()
    list_of_files = glob.glob(db_dir + "/*.db")
    list_of_files.remove(production_db_file)
    if len(list_of_files) > 0:
        print("\nAvailable dbs:")
        for index, file in enumerate(list_of_files):
            print(index, ":", file)
        while db_number < 0 or db_number >= len(list_of_files):
            db_number = int(input("Choose the db to merge: "))

        print(list_of_files[db_number])
        source_conn = sqlite3.connect(list_of_files[db_number])
        df = pd.read_sql_query("SELECT * FROM urls", source_conn)
        for index, row in df.iterrows():
            merge_url(
                row["url"],
                f"merged from {list_of_files[db_number]}",
                row["last_touch"],
                row["created_at"],
                row["description"],
                row["json"],
            )


def merge_url(
    conn,
    clean_url,
    get_url_by_url,
    url,
    title,
    last_touch,
    created_at,
    description,
    json,
):
    url = clean_url(url)

    if title is not None:
        title = title.strip()

    if len(get_url_by_url(url)) == 0:
        c = conn.cursor()
        c.execute(
            "INSERT INTO urls (url, title, last_touch , created_at, history, ai_processed, description_links, description, json) VALUES (?, ?, ?, ?, 1, 0, 0, ? , ?)",
            (url, title, last_touch, created_at, description, json),
        )
        conn.commit()
