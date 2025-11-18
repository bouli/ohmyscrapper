import sqlite3
import os
import pandas as pd
import time
from urllib.parse import urlparse, urlunparse

def get_db_path():
    if not os.path.exists("db"):
        os.mkdir("db")
    return "db/local.db"

def get_db_connection():
    return sqlite3.connect(get_db_path())

#TODO: check if it makes sense
conn = get_db_connection()

def create_tables():

    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, urls_valid_prefix_id INTEGER, url TEXT UNIQUE, url_destiny TEXT, h1 TEXT, description TEXT, last_touch DATETIME, created_at DATETIME)")
    #c.execute("DROP TABLE IF EXISTS urls_valid_prefix")

    c.execute("CREATE TABLE IF NOT EXISTS urls_valid_prefix (id INTEGER PRIMARY KEY, url_prefix TEXT UNIQUE, url_type TEXT)")

    return pd.read_sql_query("SELECT * FROM urls LIMIT 100", conn)

#TODO: not sure this should be something. depends on the project
def seeds():

    add_urls_valid_prefix("https://%.linkedin.com/posts/%", "linkedin_post")
    add_urls_valid_prefix("https://lnkd.in/%", "linkedin_redirect")
    add_urls_valid_prefix("https://%.linkedin.com/jobs/view/%", "linkedin_job")
    add_urls_valid_prefix("https://%.linkedin.com/feed/%", "linkedin_feed")

    #add_urls_valid_prefix("%.pdf", "pdf")
    #add_url('https://imazon.org.br/categorias/artigos-cientificos/')

    return True

def add_urls_valid_prefix(url_prefix, url_type):
    conn = get_db_connection()

    df = pd.read_sql_query(f"SELECT * FROM urls_valid_prefix WHERE url_prefix = '{url_prefix}'", conn)
    if len(df) == 0:
        c = conn.cursor()
        c.execute("INSERT INTO urls_valid_prefix (url_prefix, url_type) VALUES (?, ?)", (url_prefix, url_type))
        conn.commit()

def get_urls_valid_prefix_by_type(url_type):
    df = pd.read_sql_query(f"SELECT * FROM urls_valid_prefix WHERE url_type = '{url_type}'", conn)
    return df

#TODO: pagination required
def get_urls_valid_prefix(limit = 0):
    if limit > 0:
        df = pd.read_sql_query(f"SELECT * FROM urls_valid_prefix LIMIT {limit}", conn)
    else:
        df = pd.read_sql_query(f"SELECT * FROM urls_valid_prefix", conn)
    return df

#TODO: pagination required
def get_urls(limit = 0):
    if limit > 0:
        df = pd.read_sql_query(f"SELECT * FROM urls LIMIT {limit}", conn)
    else:
        df = pd.read_sql_query(f"SELECT * FROM urls", conn)
    return df

def get_url_by_url(url):
    url = clean_url(url)
    df = pd.read_sql_query(f"SELECT * FROM urls WHERE url = '{url}'", conn)

    return df

def get_url_like_unclassified(like_condition):
    df = pd.read_sql_query(f"SELECT * FROM urls WHERE url LIKE '{like_condition}' AND urls_valid_prefix_id IS NULL", conn)
    return df

def add_url(url, h1 = None):
    url = clean_url(url)
    c = conn.cursor()

    if len(get_url_by_url(url)) == 0:
        c.execute("INSERT INTO urls (url, h1, created_at) VALUES (?, ?, ?)", (url, h1, int(time.time())))
        conn.commit()

    return get_url_by_url(url)


def set_url_destiny(url, destiny):
    url = clean_url(url)
    destiny = clean_url(destiny)
    c = conn.cursor()
    c.execute("UPDATE urls SET url_destiny = ? WHERE url = ?", (destiny, url))
    conn.commit()

def set_url_h1(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET h1 = ? WHERE url = ?", (value, url))
    conn.commit()

def set_url_description(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET description = ? WHERE url = ?", (value, url))
    conn.commit()

def set_url_prefix_by_id(url_id, prefix_id):
    c = conn.cursor()
    c.execute("UPDATE urls SET urls_valid_prefix_id = ? WHERE url = ?", (prefix_id, url_id))
    conn.commit()


def clean_url(url):
    url = url.split('#')[0]
    old_query = urlparse(url).query.split('&')
    new_query = []
    for i in old_query:
        if i[0:4] != 'utm_':
            new_query.append(i)

    url = urlunparse(urlparse(url). _replace(query='&'.join(new_query))).replace("'", '')
    return url


def get_untouched_urls(limit = 10, random = True):
    if random:
        df = pd.read_sql_query(f"SELECT * FROM urls WHERE urls_valid_prefix_id IS NOT NULL AND last_touch IS NULL ORDER BY RANDOM() LIMIT {limit}", conn)
    else:
        df = pd.read_sql_query(f"SELECT * FROM urls WHERE urls_valid_prefix_id IS NOT NULL AND last_touch IS NULL ORDER BY created_at DESC LIMIT {limit}", conn)
    return df


def touch_url(url):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET last_touch = ? WHERE url = ?", (int(time.time()), url))
    conn.commit()

def untouch_url(url):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET last_touch = NULL WHERE url = ?", (url))
    conn.commit()

def untouch_all_urls():
    c = conn.cursor()
    c.execute("UPDATE urls SET last_touch = NULL")
    conn.commit()
