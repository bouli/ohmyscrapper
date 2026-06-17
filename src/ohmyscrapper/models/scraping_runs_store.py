import pandas as pd


def create_scraping_run(conn, time_module, command="scrap-urls", total_urls=0):
    now = int(time_module.time())
    c = conn.cursor()
    c.execute(
        "INSERT INTO scraping_runs (command, status, total_urls, completed_count, skipped_count, failure_count, started_at, updated_at) VALUES (?, ?, ?, 0, 0, 0, ?, ?)",
        (command, "running", int(total_urls), now, now),
    )
    conn.commit()
    return c.lastrowid


def get_scraping_run(conn, run_id):
    return pd.read_sql_query(
        "SELECT * FROM scraping_runs WHERE id = ?",
        conn,
        params=(int(run_id),),
    )


def get_scraping_runs(conn, limit=0):
    sql = "SELECT * FROM scraping_runs ORDER BY started_at DESC, id DESC"
    params = ()
    if limit > 0:
        sql += " LIMIT ?"
        params = (int(limit),)
    return pd.read_sql_query(sql, conn, params=params)


def update_scraping_run_total(conn, time_module, run_id, total_urls):
    c = conn.cursor()
    c.execute(
        "UPDATE scraping_runs SET total_urls = ?, updated_at = ? WHERE id = ?",
        (int(total_urls), int(time_module.time()), int(run_id)),
    )
    conn.commit()


def increment_scraping_run_counter(conn, time_module, run_id, counter, amount=1):
    valid_counters = {"completed_count", "skipped_count", "failure_count"}
    if counter not in valid_counters:
        raise ValueError(f"Unknown scraping run counter: {counter}")

    c = conn.cursor()
    c.execute(
        f"UPDATE scraping_runs SET {counter} = {counter} + ?, updated_at = ? WHERE id = ?",
        (int(amount), int(time_module.time()), int(run_id)),
    )
    conn.commit()


def finish_scraping_run(conn, time_module, run_id, status="completed", error=None):
    valid_statuses = {"completed", "failed", "interrupted"}
    if status not in valid_statuses:
        raise ValueError(f"Unknown scraping run status: {status}")

    now = int(time_module.time())
    c = conn.cursor()
    c.execute(
        "UPDATE scraping_runs SET status = ?, finished_at = ?, updated_at = ?, error = ? WHERE id = ?",
        (status, now, now, error, int(run_id)),
    )
    conn.commit()
