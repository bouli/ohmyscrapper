import ohmyscrapper.models.urls_manager as urls_manager
import ohmyscrapper.modules.sniff_url as sniff_url
import ohmyscrapper.modules.load_txt as load_txt
import ohmyscrapper.modules.classify_urls as classify_urls
from ohmyscrapper.core import config

import time
import random


def scrap_url(url, verbose=False):
    if url["url_type"] is None:
        url["url_type"] = "generic"

    if verbose:
        print("\n\n", url["url_type"] + ":", url["url"])

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

        url_report = sniff_url.get_tags(
            url=url["url"], sniffing_config=sniffing_config[url_type]
        )
    except Exception as e:
        urls_manager.set_url_error(url=url["url"], value="error on scrapping")
        urls_manager.touch_url(url=url["url"])
        if verbose:
            print("\n\n!!! ERROR FOR:", url["url"])
            print(
                "\n\n!!! you can check the URL using the command sniff-url",
                url["url"],
                "\n\n",
            )
        return

    process_sniffed_url(
        url_report=url_report,
        url=url,
        sniffing_config=sniffing_config[url_type],
        verbose=verbose,
    )

    urls_manager.set_url_json(url=url["url"], value=url_report["json"])
    urls_manager.touch_url(url=url["url"])

    return


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
            value="error: no title, url_destiny or description was founded",
        )


def isNaN(num):
    return num != num


def scrap_urls(
    recursive=False,
    ignore_valid_prefix=False,
    randomize=False,
    only_parents=True,
    verbose=False,
    n_urls=0,
):
    limit = 10
    classify_urls.classify_urls()
    urls = urls_manager.get_untouched_urls(
        ignore_valid_prefix=ignore_valid_prefix,
        randomize=randomize,
        only_parents=only_parents,
        limit=limit,
    )
    if len(urls) == 0:
        print("📭 no urls to scrap")
        if n_urls > 0:
            print(f"-- 🗃️ {n_urls} scraped urls in total...")
            print("scrapping is over...")
        return
    for index, url in urls.iterrows():
        wait = random.randint(1, 3)
        print(
            "🐶 Scrapper is sleeping for", wait, "seconds before scraping next url..."
        )
        time.sleep(wait)

        print("🐕 Scrapper is sniffing the url...")
        scrap_url(url=url, verbose=verbose)

    n_urls = n_urls + len(urls)
    print(f"-- 🗃️ {n_urls} scraped urls...")
    classify_urls.classify_urls()
    if recursive:
        wait = random.randint(5, 10)
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
        )
    else:
        print("scrapping is over...")
