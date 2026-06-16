import os
import sqlite3
import time

import pandas as pd

from ohmyscrapper.core import config
from ohmyscrapper.models import db_schema, merge_store, scraping_runs_store, url_store


def get_db_dir():
    db_folder = config.get_dir("db")
    if not os.path.exists(db_folder):
        os.mkdir(db_folder)
    return db_folder


def get_db_path():
    db_file = config.get_db()
    return os.path.join(get_db_dir(), db_file)


def get_db_connection():
    connection = sqlite3.connect(get_db_path())
    db_schema.create_tables(connection)
    return connection


def use_connection(func):
    def provide_connection(*args, **kwargs):
        global conn
        with get_db_connection() as conn:
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError:
                update_db()
                return func(*args, **kwargs)

    return provide_connection


def create_tables(conn):
    db_schema.create_tables(conn)


def update_db():
    db_schema.update_db(conn)


def seeds(seeds=None):
    if seeds is None:
        seeds = {}

    for url_type, url_prefix in seeds.items():
        add_urls_valid_prefix(url_prefix, url_type)

    return True


@use_connection
def reset_seeds():
    sql = "DELETE FROM urls_valid_prefix WHERE 1 = 1"
    c = conn.cursor()
    c.execute(sql)
    conn.commit()


@use_connection
def add_urls_valid_prefix(url_prefix, url_type):

    df = pd.read_sql_query(
        "SELECT * FROM urls_valid_prefix WHERE url_prefix = ?",
        conn,
        params=(url_prefix,),
    )
    if len(df) == 0:
        c = conn.cursor()
        c.execute(
            "INSERT INTO urls_valid_prefix (url_prefix, url_type) VALUES (?, ?)",
            (url_prefix, url_type),
        )
        conn.commit()


@use_connection
def get_urls_valid_prefix_by_type(url_type):
    df = pd.read_sql_query(
        "SELECT * FROM urls_valid_prefix WHERE url_type = ?",
        conn,
        params=(url_type,),
    )
    return df


@use_connection
def get_urls_valid_prefix_by_id(id):
    df = pd.read_sql_query(
        "SELECT * FROM urls_valid_prefix WHERE id = ?",
        conn,
        params=(int(id),),
    )
    return df


# TODO: pagination required
@use_connection
def get_urls_valid_prefix(limit=0):
    if limit > 0:
        df = pd.read_sql_query(
            "SELECT * FROM urls_valid_prefix LIMIT ?",
            conn,
            params=(int(limit),),
        )
    else:
        df = pd.read_sql_query("SELECT * FROM urls_valid_prefix", conn)
    return df


# TODO: pagination required
@use_connection
def get_urls(limit=0):
    return url_store.get_urls(conn, limit=limit)


@use_connection
def create_scraping_run(command="scrap-urls", total_urls=0):
    return scraping_runs_store.create_scraping_run(
        conn, time, command=command, total_urls=total_urls
    )


@use_connection
def get_scraping_run(run_id):
    return scraping_runs_store.get_scraping_run(conn, run_id)


@use_connection
def get_scraping_runs(limit=0):
    return scraping_runs_store.get_scraping_runs(conn, limit=limit)


@use_connection
def get_recent_url_errors(limit=10):
    return url_store.get_recent_url_errors(conn, limit=limit)


@use_connection
def update_scraping_run_total(run_id, total_urls):
    scraping_runs_store.update_scraping_run_total(conn, time, run_id, total_urls)


@use_connection
def increment_scraping_run_counter(run_id, counter, amount=1):
    scraping_runs_store.increment_scraping_run_counter(
        conn, time, run_id, counter, amount=amount
    )


@use_connection
def finish_scraping_run(run_id, status="completed", error=None):
    scraping_runs_store.finish_scraping_run(
        conn, time, run_id, status=status, error=error
    )


@use_connection
def get_urls_report():
    return url_store.get_urls_report(conn)


@use_connection
def get_url_by_url(url):
    return url_store.get_url_by_url(conn, url)


@use_connection
def get_url_by_id(id):
    return url_store.get_url_by_id(conn, id)


@use_connection
def get_urls_by_url_type(url_type):
    return url_store.get_urls_by_url_type(conn, url_type)


@use_connection
def get_urls_by_url_type_for_ai_process(limit=10):
    return url_store.get_urls_by_url_type_for_ai_process(conn, limit=limit)


@use_connection
def get_url_like_unclassified(like_condition):
    return url_store.get_url_like_unclassified(conn, like_condition)


@use_connection
def add_url(url, title=None, parent_url=None):
    return url_store.add_url(conn, time, url, title=title, parent_url=parent_url)


@use_connection
def add_ai_log(instructions, response, model, prompt_file, prompt_name):
    c = conn.cursor()

    c.execute(
        "INSERT INTO ai_log (instructions, response, model, prompt_file, prompt_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (instructions, response, model, prompt_file, prompt_name, int(time.time())),
    )
    conn.commit()


@use_connection
def get_ai_log():
    df = pd.read_sql_query("SELECT * FROM ai_log", conn)
    return df


@use_connection
def set_url_destiny(url, destiny):
    url = clean_url(url)
    destiny = clean_url(destiny)
    c = conn.cursor()
    c.execute("UPDATE urls SET url_destiny = ? WHERE url = ?", (destiny, url))
    c.execute(
        "UPDATE urls SET parent_url = ? WHERE url = ?",
        (str(url), destiny),
    )

    conn.commit()


@use_connection
def set_url_title(url, value):
    value = str(value).strip()
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET title = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_title_by_id(id, value):
    id = int(id)
    value = str(value).strip()

    c = conn.cursor()
    c.execute("UPDATE urls SET title = ? WHERE id = ?", (value, id))
    conn.commit()


@use_connection
def set_url_ai_processed_by_id(id, json_str):
    id = int(id)
    value = 1
    value = str(value).strip()
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET ai_processed = ? , json_ai = ? WHERE id = ?",
        (value, json_str, id),
    )
    conn.commit()


@use_connection
def set_url_empty_ai_processed_by_id(id, json_str="empty result"):
    id = int(id)
    value = 1
    value = str(value).strip()
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET ai_processed = ? , json_ai = ? WHERE ai_processed = 0 AND id = ?",
        (value, json_str, id),
    )
    conn.commit()


@use_connection
def set_url_ai_processed_by_url(url, json_str):
    value = 1
    value = str(value).strip()
    url = clean_url(url)
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET ai_processed = ?, json_ai = ? WHERE url = ?",
        (value, json_str, url),
    )
    conn.commit()


@use_connection
def set_url_description(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET description = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_description_links(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET description_links = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_json(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET json = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_error(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET error = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_type_by_id(url_id, url_type):
    url_store.set_url_type_by_id(conn, url_id, url_type)


def clean_url(url):
    return url_store.clean_url(url)


@use_connection
def get_untouched_urls(
    limit=10, randomize=True, ignore_valid_prefix=False, only_parents=True
):
    return url_store.get_untouched_urls(
        conn,
        limit=limit,
        randomize=randomize,
        ignore_valid_prefix=ignore_valid_prefix,
        only_parents=only_parents,
    )


@use_connection
def touch_url(url):
    url_store.touch_url(conn, time, url)


@use_connection
def untouch_url(url):
    url_store.untouch_url(conn, url)


@use_connection
def untouch_all_urls():
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET last_touch = NULL, url_type = NULL, error = NULL WHERE history = 0"
    )
    conn.commit()


@use_connection
def untouch_all_urls_with_errors(include_warnings=False):
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET last_touch = NULL, url_type = NULL, error = NULL WHERE history = 0 AND error LIKE ?",
        ("error%",),
    )
    if include_warnings:
        c.execute(
            "UPDATE urls SET last_touch = NULL, url_type = NULL, error = NULL WHERE history = 0 AND error LIKE ?",
            ("warning%",),
        )

    conn.commit()


@use_connection
def set_all_urls_as_history():
    c = conn.cursor()
    c.execute("UPDATE urls SET history = 1")
    conn.commit()


def merge_dbs() -> None:
    merge_store.merge_dbs(get_db_path, get_db_dir, merge_url)


@use_connection
def merge_url(url, title, last_touch, created_at, description, json):
    merge_store.merge_url(
        conn,
        clean_url,
        get_url_by_url,
        url,
        title,
        last_touch,
        created_at,
        description,
        json,
    )
