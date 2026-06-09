import sqlite3


def create_tables(conn):
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, url_type STRING, parent_url TEXT, url TEXT UNIQUE, url_destiny TEXT, title TEXT, error TEXT, description TEXT, description_links INTEGER DEFAULT 0, json TEXT, json_ai TEXT, ai_processed INTEGER DEFAULT 0, history INTEGER DEFAULT 0, last_touch DATETIME, created_at DATETIME)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS ai_log (id INTEGER PRIMARY KEY, instructions STRING, response STRING, model STRING, prompt_file STRING, prompt_name STRING, created_at DATETIME)"
    )

    c.execute(
        "CREATE TABLE IF NOT EXISTS urls_valid_prefix (id INTEGER PRIMARY KEY, url_prefix TEXT UNIQUE, url_type TEXT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS scraping_runs (id INTEGER PRIMARY KEY, command TEXT, status TEXT, total_urls INTEGER DEFAULT 0, completed_count INTEGER DEFAULT 0, skipped_count INTEGER DEFAULT 0, failure_count INTEGER DEFAULT 0, started_at DATETIME, finished_at DATETIME, updated_at DATETIME, error TEXT)"
    )
    conn.commit()


def update_db(conn):
    try:
        c = conn.cursor()
        c.execute("ALTER TABLE urls RENAME COLUMN h1 TO title")
    except sqlite3.OperationalError:
        pass
