import random
import time

import ohmyscrapper.models.urls_manager as urls_manager
import ohmyscrapper.modules.browser as browser
import ohmyscrapper.modules.classify_urls as classify_urls
import ohmyscrapper.modules.load_txt as load_txt
import ohmyscrapper.modules.sniff_url as sniff_url
from ohmyscrapper.core import config


DEFAULT_SCRAPING_POLICY = {
    "request-delay-min": 1,
    "request-delay-max": 3,
    "retry-count": 0,
    "retry-backoff": 0,
}

_proxy_rotation_index = 0


def _get_sniffing_policy_number(param, default, cast=float):
    try:
        value = config.get_sniffing(param)
    except Exception:
        return default

    if value is None or isinstance(value, bool):
        return default

    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid sniffing.{param}: {value!r}") from exc


def get_scraping_policy():
    retry_count = _get_sniffing_policy_number(
        "retry-count",
        DEFAULT_SCRAPING_POLICY["retry-count"],
        int,
    )
    request_delay_min = _get_sniffing_policy_number(
        "request-delay-min",
        DEFAULT_SCRAPING_POLICY["request-delay-min"],
    )
    request_delay_max = _get_sniffing_policy_number(
        "request-delay-max",
        DEFAULT_SCRAPING_POLICY["request-delay-max"],
    )
    retry_backoff = _get_sniffing_policy_number(
        "retry-backoff",
        DEFAULT_SCRAPING_POLICY["retry-backoff"],
    )

    if request_delay_min < 0:
        raise ValueError("Invalid sniffing.request-delay-min: must be >= 0")
    if request_delay_max < 0:
        raise ValueError("Invalid sniffing.request-delay-max: must be >= 0")
    if request_delay_max < request_delay_min:
        raise ValueError(
            "Invalid sniffing request delay policy: request-delay-max must be >= request-delay-min"
        )
    if retry_count < 0:
        raise ValueError("Invalid sniffing.retry-count: must be >= 0")
    if retry_backoff < 0:
        raise ValueError("Invalid sniffing.retry-backoff: must be >= 0")

    return {
        "request_delay_min": request_delay_min,
        "request_delay_max": request_delay_max,
        "retry_count": retry_count,
        "retry_backoff": retry_backoff,
    }


def get_scraping_delay(policy=None):
    if policy is None:
        policy = get_scraping_policy()

    delay_min = policy["request_delay_min"]
    delay_max = policy["request_delay_max"]

    if delay_min == delay_max:
        return delay_min

    if float(delay_min).is_integer() and float(delay_max).is_integer():
        return random.randint(int(delay_min), int(delay_max))

    return random.uniform(delay_min, delay_max)


def get_proxy_pool():
    try:
        proxies = config.get_sniffing("proxies")
    except Exception:
        return []

    if proxies is None or isinstance(proxies, bool):
        return []
    if isinstance(proxies, str):
        return [item.strip() for item in proxies.split(",") if item.strip()]
    if isinstance(proxies, (list, tuple)):
        return [str(item).strip() for item in proxies if str(item).strip()]

    return [str(proxies).strip()] if str(proxies).strip() else []


def get_next_proxy(proxy_pool=None):
    global _proxy_rotation_index

    if proxy_pool is None:
        proxy_pool = get_proxy_pool()
    if len(proxy_pool) == 0:
        return None

    proxy = proxy_pool[_proxy_rotation_index % len(proxy_pool)]
    _proxy_rotation_index += 1
    return proxy


def scrap_url(url, verbose=False, driver=None, proxy=None):
    if url["url_type"] is None:
        url["url_type"] = "generic"

    if verbose:
        print("\n\n", url["url_type"] + ":", url["url"])

    policy = get_scraping_policy()
    retry_count = policy["retry_count"]
    last_error = None
    if proxy is None:
        proxy = get_next_proxy()

    for attempt in range(retry_count + 1):
        try:
            url_type = url["url_type"]
            sniffing_config = config.get_url_sniffing()

            if url_type not in sniffing_config:
                default_type_sniffing = {
                    "bodytags": {"h1": "title"},
                    "metatags": {
                        "og:title": "title",
                        "og:description": "description",
                        "description": "description",
                    },
                }
                config.append_url_sniffing({url_type: default_type_sniffing})
                sniffing_config = config.get_url_sniffing()

            sniff_kwargs = {
                "url": url["url"],
                "sniffing_config": sniffing_config[url_type],
                "driver": driver,
            }
            if proxy is not None:
                sniff_kwargs["proxy"] = proxy
            url_report = sniff_url.get_tags(**sniff_kwargs)
            break
        except Exception as e:
            last_error = e
            if attempt < retry_count:
                wait = policy["retry_backoff"] * (attempt + 1)
                if verbose:
                    print(
                        f"\n\n!!! retrying {url['url']} after scrape error: {e}"
                    )
                if wait > 0:
                    time.sleep(wait)
                continue

            urls_manager.set_url_error(
                url=url["url"],
                value=f"error on scrapping: {last_error}",
            )
            urls_manager.touch_url(url=url["url"])
            if verbose:
                print("\n\n!!! ERROR FOR:", url["url"])
                print(
                    "\n\n!!! you can check the URL using the command sniff-url",
                    url["url"],
                    "\n\n",
                )
            return False

    process_sniffed_url(
        url_report=url_report,
        url=url,
        sniffing_config=sniffing_config[url_type],
        verbose=verbose,
    )

    urls_manager.set_url_json(url=url["url"], value=url_report["json"])
    urls_manager.touch_url(url=url["url"])

    return True


def process_sniffed_url(url_report, url, sniffing_config, verbose=False):
    if verbose:
        print(url["url_type"])
        print(url["url"])
    changed = False

    db_fields = {}
    db_fields["title"] = None
    db_fields["description"] = None
    db_fields["url_destiny"] = None

    if "metatags" in sniffing_config.keys():
        for tag, bd_field in sniffing_config["metatags"].items():
            if tag in url_report.keys():
                if bd_field[:1] == "+":
                    if db_fields[bd_field[1:]] is None:
                        db_fields[bd_field[1:]] = ""
                    db_fields[bd_field[1:]] = (
                        db_fields[bd_field[1:]] + " " + url_report[tag]
                    )
                else:
                    db_fields[bd_field] = url_report[tag]

    if "bodytags" in sniffing_config.keys():
        for tag, bd_field in sniffing_config["bodytags"].items():
            if tag in url_report.keys():
                if bd_field[:1] == "+":
                    if db_fields[bd_field[1:]] is None:
                        db_fields[bd_field[1:]] = ""
                    db_fields[bd_field[1:]] = (
                        db_fields[bd_field[1:]] + " " + url_report[tag]
                    )
                else:
                    db_fields[bd_field] = url_report[tag]

    if (
        "atags" in sniffing_config.keys()
        and "first-tag-as-url_destiny" in sniffing_config["atags"].keys()
    ):
        if (
            url_report["total-a-links"]
            < sniffing_config["atags"]["first-tag-as-url_destiny"]
        ):
            if "first-a-link" in url_report.keys():
                db_fields["url_destiny"] = url_report["first-a-link"]
    if (
        "atags" in sniffing_config.keys()
        and "load_links" in sniffing_config["atags"].keys()
    ):
        for a_link in url_report["a_links"]:
            urls_manager.add_url(url=a_link["href"], parent_url=url["url"])

    if db_fields["title"] is not None:
        urls_manager.set_url_title(url=url["url"], value=db_fields["title"])
        changed = True

    if db_fields["description"] is not None:
        urls_manager.set_url_description(url=url["url"], value=db_fields["description"])
        description_links = load_txt.put_urls_from_string(
            text_to_process=db_fields["description"], parent_url=url["url"]
        )
        urls_manager.set_url_description_links(url=url["url"], value=description_links)

        changed = True

    if db_fields["url_destiny"] is not None:
        urls_manager.add_url(url=db_fields["url_destiny"])
        urls_manager.set_url_destiny(url=url["url"], destiny=db_fields["url_destiny"])
        changed = True

    if not changed:
        urls_manager.set_url_error(
            url=url["url"],
            value="warning: no title, url_destiny or description was founded",
        )


def isNaN(num):
    return num != num


def get_scraping_run_progress(run_id):
    run = urls_manager.get_scraping_run(run_id)
    if len(run) == 0:
        return None

    row = run.iloc[0]
    completed_count = int(row["completed_count"])
    skipped_count = int(row["skipped_count"])
    failure_count = int(row["failure_count"])

    return {
        "id": int(row["id"]),
        "status": row["status"],
        "total_urls": int(row["total_urls"]),
        "completed_count": completed_count,
        "skipped_count": skipped_count,
        "failure_count": failure_count,
        "processed_count": completed_count + skipped_count + failure_count,
    }


def format_scraping_progress(progress):
    total_urls = progress["total_urls"]
    processed_count = progress["processed_count"]
    percentage = 0
    if total_urls > 0:
        percentage = min(100, int((processed_count / total_urls) * 100))

    return (
        f"-- progress run #{progress['id']} [{progress['status']}]: "
        f"{processed_count}/{total_urls} processed ({percentage}%) "
        f"completed={progress['completed_count']} "
        f"skipped={progress['skipped_count']} "
        f"failed={progress['failure_count']}"
    )


def print_scraping_progress(run_id):
    progress = get_scraping_run_progress(run_id)
    if progress is not None:
        print(format_scraping_progress(progress))


def scrap_urls(
    recursive=False,
    ignore_valid_prefix=False,
    randomize=False,
    only_parents=True,
    verbose=False,
    n_urls=0,
    driver=None,
    run_id=None,
    run_command="scrap-urls",
):
    created_run = run_id is None
    if created_run:
        run_id = urls_manager.create_scraping_run(command=run_command)

    try:
        limit = 10
        classify_urls.classify_urls()
        urls = urls_manager.get_untouched_urls(
            ignore_valid_prefix=ignore_valid_prefix,
            randomize=randomize,
            only_parents=only_parents,
            limit=limit,
        )
        urls_manager.update_scraping_run_total(run_id, n_urls + len(urls))
        print_scraping_progress(run_id)

        if len(urls) == 0:
            print("📭 no urls to scrap")
            if n_urls > 0:
                print(f"-- 🗃️ {n_urls} scraped urls in total...")
            urls_manager.finish_scraping_run(run_id, status="completed")
            print("scrapping is over...")
            return

        policy = get_scraping_policy()
        proxy_pool = get_proxy_pool()
        browser_pool = None
        if driver is None and config.get_sniffing("use-browser"):
            browser_pool = browser.BrowserPool()
        try:
            for index, url in urls.iterrows():
                proxy = get_next_proxy(proxy_pool)
                wait = get_scraping_delay(policy)
                print(
                    "🐶 Scrapper is sleeping for",
                    wait,
                    "seconds before scraping next url...",
                )
                if wait > 0:
                    time.sleep(wait)

                print("🐕 Scrapper is sniffing the url...")

                active_driver = driver
                borrowed_driver = False
                if browser_pool is not None:
                    try:
                        active_driver = browser_pool.acquire(proxy=proxy)
                        borrowed_driver = True
                    except Exception as e:
                        urls_manager.set_url_error(
                            url=url["url"],
                            value=f"browser startup error for {url['url']}: {e}",
                        )
                        urls_manager.touch_url(url=url["url"])
                        urls_manager.increment_scraping_run_counter(
                            run_id, "failure_count"
                        )
                        print(f"!!! browser startup error for {url['url']}: {e}")
                        print_scraping_progress(run_id)
                        continue
                try:
                    scraped = scrap_url(
                        url=url, verbose=verbose, driver=active_driver, proxy=proxy
                    )
                    if scraped:
                        urls_manager.increment_scraping_run_counter(
                            run_id, "completed_count"
                        )
                    else:
                        urls_manager.increment_scraping_run_counter(
                            run_id, "failure_count"
                        )
                    print_scraping_progress(run_id)
                finally:
                    if borrowed_driver:
                        browser_pool.release(active_driver, proxy=proxy)
        finally:
            if browser_pool is not None:
                browser_pool.close_all()

        n_urls = n_urls + len(urls)
        print(f"-- 🗃️ {n_urls} scraped urls...")
        classify_urls.classify_urls()
        if recursive:
            wait = random.randint(
                int(config.get_sniffing("round-sleeping") / 2),
                int(config.get_sniffing("round-sleeping")),
            )
            print(
                f"🐶 Scrapper is sleeping for {wait} seconds before next round of {limit} urls"
            )
            time.sleep(wait)
            scrap_urls(
                recursive=recursive,
                ignore_valid_prefix=ignore_valid_prefix,
                randomize=randomize,
                only_parents=only_parents,
                verbose=verbose,
                n_urls=n_urls,
                driver=driver,
                run_id=run_id,
                run_command=run_command,
            )
        else:
            urls_manager.finish_scraping_run(run_id, status="completed")
            print("scrapping is over...")
    except KeyboardInterrupt:
        urls_manager.finish_scraping_run(
            run_id,
            status="interrupted",
            error="Scraping interrupted by user",
        )
        raise
    except Exception as e:
        urls_manager.finish_scraping_run(run_id, status="failed", error=str(e))
        raise
