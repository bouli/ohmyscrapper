from urllib.parse import urlparse, urlunparse

import pandas as pd


def clean_url(url):
    if url[0:7] == "http://":
        url = "https://" + url[7:]

    if url[0:8] != "https://":
        url = "https://" + url
    url = url.split("#")[0]
    old_query = urlparse(url).query.split("&")
    new_query = []
    for i in old_query:
        if i[0:4] != "utm_":
            new_query.append(i)

    url = urlunparse(urlparse(url)._replace(query="&".join(new_query))).replace("'", "")
    return url


def get_url_by_url(conn, url):
    url = clean_url(url)
    return pd.read_sql_query(
        "SELECT * FROM urls WHERE url = ?",
        conn,
        params=(url,),
    )


def get_url_by_id(conn, id):
    return pd.read_sql_query(
        "SELECT * FROM urls WHERE id = ?",
        conn,
        params=(int(id),),
    )


def get_urls(conn, limit=0):
    sql = "SELECT * FROM urls ORDER BY history ASC, url_type DESC, last_touch DESC"
    params = ()
    if limit > 0:
        sql += " LIMIT ?"
        params = (int(limit),)

    return pd.read_sql_query(sql, conn, params=params)


def add_url(conn, time_module, url, title=None, parent_url=None):
    if url[:1] == "/":
        return None
    url = clean_url(url)

    if title is not None:
        title = title.strip()

    if parent_url is not None:
        parent_url = str(parent_url)

    if len(get_url_by_url(conn, url)) == 0:
        c = conn.cursor()
        c.execute(
            "INSERT INTO urls (url, title, parent_url, created_at, ai_processed, description_links, history) VALUES (?, ?, ?, ?, 0, 0, 0)",
            (url, title, parent_url, int(time_module.time())),
        )
        conn.commit()

    return get_url_by_url(conn, url)


def get_urls_by_url_type(conn, url_type):
    return pd.read_sql_query(
        "SELECT * FROM urls WHERE history = 0 AND url_type = ?",
        conn,
        params=(url_type,),
    )


def get_urls_by_url_type_for_ai_process(conn, limit=10):
    return pd.read_sql_query(
        "SELECT * FROM urls WHERE history = 0 AND (title IS NOT NULL OR description IS NOT NULL) AND ai_processed = 0 LIMIT ?",
        conn,
        params=(int(limit),),
    )


def get_url_like_unclassified(conn, like_condition):
    return pd.read_sql_query(
        "SELECT * FROM urls WHERE history = 0 AND url LIKE ? AND url_type IS NULL",
        conn,
        params=(like_condition,),
    )


def get_recent_url_errors(conn, limit=10):
    sql = """
    SELECT id, url, url_type, title, error, last_touch, created_at
    FROM urls
    WHERE history = 0 AND error IS NOT NULL AND error != ''
    ORDER BY COALESCE(last_touch, created_at, 0) DESC, id DESC
    """
    params = ()
    if limit > 0:
        sql += " LIMIT ?"
        params = (int(limit),)
    return pd.read_sql_query(sql, conn, params=params)


def set_url_type_by_id(conn, url_id, url_type):
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET url_type = ?, last_touch = NULL WHERE id = ?",
        (url_type, int(url_id)),
    )
    conn.commit()


def touch_url(conn, time_module, url):
    url = clean_url(url)
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET last_touch = ? WHERE url = ?",
        (int(time_module.time()), url),
    )
    conn.commit()


def untouch_url(conn, url):
    url = str(clean_url(url).strip())
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET last_touch = NULL, url_type = NULL, error = NULL WHERE url = ?",
        (url,),
    )
    conn.commit()


def get_untouched_urls(
    conn,
    limit=10,
    randomize=True,
    ignore_valid_prefix=False,
    only_parents=True,
):
    where_sql = ""
    if not ignore_valid_prefix:
        where_sql += " AND url_type IS NOT NULL "

    if only_parents:
        where_sql += " AND (parent_url = '' OR parent_url IS NULL) "

    if randomize:
        random_sql = " RANDOM() "
    else:
        random_sql = " created_at DESC "
    sql = f"SELECT * FROM urls WHERE 1 = 1 AND history = 0 {where_sql} AND last_touch IS NULL ORDER BY {random_sql} LIMIT ?"
    return pd.read_sql_query(sql, conn, params=(int(limit),))


def get_urls_report(conn):
    sql = """
    WITH parent_url AS (
        SELECT parent_url FROM urls WHERE parent_url IS NOT NULL AND parent_url != '' GROUP BY parent_url
    ),
    parents AS (
        SELECT
            u.id,
            u.url,
            u.title
            FROM urls u
                INNER JOIN parent_url p
                    ON u.url = p.parent_url
    )
    SELECT
        u.id,
        u.url_type,
        u.url,
        COALESCE(u.title, p.title) as title,
        p.url as parent_url,
        p.title as parent_title
        FROM urls u
        LEFT JOIN parents p
            ON u.parent_url = p.url
        WHERE
            u.history = 0
            AND u.url NOT IN (SELECT url FROM parents)
        ORDER BY url_type DESC
    """
    return pd.read_sql_query(sql, conn)
