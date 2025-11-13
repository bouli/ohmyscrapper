import models.urls_manager as urls_manager
import pandas as pd
import time



def classify_urls(recursive=False):
    urls_manager.seeds()
    df = pd.read_sql_query("SELECT * FROM urls_valid_prefix", urls_manager.conn)

    keep_alive = True
    while keep_alive:
        print('waking up!')
        for index, row in df.iterrows():
            sql_query = "SELECT * FROM urls WHERE url LIKE '" + row['url_prefix'] + "' AND urls_valid_prefix_id IS NULL"
            df_urls = pd.read_sql_query(sql_query, urls_manager.conn)
            for index, row_urls in df_urls.iterrows():
                sql_query = "UPDATE urls SET urls_valid_prefix_id = " + str(row['id']) + " WHERE id = " + str(row_urls['id'])
                print(sql_query)
                urls_manager.conn.cursor().execute(sql_query)
                urls_manager.conn.commit()

        if not recursive:
            print('ending...')
            keep_alive = False
        else:
            print('sleeping...')
            time.sleep(10)
