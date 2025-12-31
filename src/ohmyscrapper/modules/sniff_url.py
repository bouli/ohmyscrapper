import requests
from bs4 import BeautifulSoup
import json
from ohmyscrapper.core import config
import ohmyscrapper.modules.browser as browser
import time


def sniff_url(
    url="https://www.linkedin.com/in/cesardesouzacardoso/",
    silent=False,
    sniffing_config={},
    driver=None,
):
    final_report = {}
    if "metatags" in sniffing_config:
        metatags_to_search = sniffing_config["metatags"]
    else:
        metatags_to_search = [
            "description",
            "og:url",
            "og:title",
            "og:description",
            "og:type",
            "lnkd:url",
        ]

    if "bodytags" in sniffing_config:
        body_tags_to_search = sniffing_config["bodytags"]
    else:
        body_tags_to_search = {
            "h1": "",
            "h2": "",
        }

    if type(metatags_to_search) is dict:
        metatags_to_search = list(metatags_to_search.keys())

    # force clean concatenate without any separator
    if type(body_tags_to_search) is dict:
        body_tags_to_search = list(body_tags_to_search.keys())

    if type(body_tags_to_search) is list:
        body_tags_to_search = dict.fromkeys(body_tags_to_search, " ")

    if not silent:
        print("checking url:", url)

    try:
        r = get_url(url=url, driver=driver)
        soup = BeautifulSoup(r, "html.parser")
    except requests.exceptions.ReadTimeout:
        url_domain = url.split("/")[2]
        final_report["error"] = (
            f"!!! timeout (10 seconds) while checking the url with domain: `{url_domain}` !!!"
        )

        print(f"\n\n{final_report['error']}\n\n")
        soup = BeautifulSoup("", "html.parser")

    final_report["scrapped-url"] = url
    if len(metatags_to_search) > 0:
        final_report.update(
            _extract_meta_tags(
                soup=soup, silent=silent, metatags_to_search=metatags_to_search
            )
        )

    if len(body_tags_to_search) > 0:
        final_report.update(
            _extract_text_tags(
                soup=soup, silent=silent, body_tags_to_search=body_tags_to_search
            )
        )
    final_report["a_links"] = _extract_a_tags(soup=soup, silent=silent, url=url)
    final_report = _complementary_report(final_report, soup, silent).copy()
    final_report["json"] = json.dumps(final_report)

    return final_report


def _extract_a_tags(soup, silent, url=None):
    a_links = []
    if not silent:
        print("\n\n\n\n---- all <a> links ---")

    i = 0
    for a_tag in soup.find_all("a"):
        i = i + 1

        href = a_tag.get("href")
        if url is not None and href[:1] == "/":
            domain = url.split("//")[0] + "//" + url.split("//")[1].split("/")[0]
            href = domain + href

        a_links.append({"text": a_tag.text, "href": href})
        if not silent:
            print("\n-- <a> link", i, "-- ")
            print("target:", a_tag.get("target"))
            print("text:", str(a_tag.text).strip())
            print("href:", href)
            print("-------------- ")
    return a_links


def _extract_meta_tags(soup, silent, metatags_to_search):
    valid_meta_tags = {}
    if not silent:
        print("\n\n\n\n---- all <meta> tags ---\n")
    i = 0
    for meta_tag in soup.find_all("meta"):
        if (
            meta_tag.get("name") in metatags_to_search
            or meta_tag.get("property") in metatags_to_search
        ):
            if meta_tag.get("name") is not None:
                valid_meta_tags[meta_tag.get("name")] = meta_tag.get("content")
            elif meta_tag.get("property") is not None:
                valid_meta_tags[meta_tag.get("property")] = meta_tag.get("content")
        i = i + 1
        if not silent:
            print("-- meta tag", i, "--")
            print("name:", meta_tag.get("name"))
            print("property:", meta_tag.get("property"))
            print("content:", meta_tag.get("content"))
            print("---------------- \n")
    return valid_meta_tags


def _extract_text_tags(soup, silent, body_tags_to_search):
    valid_text_tags = {}
    if not silent:
        print("\n\n\n\n---- all <text> tags ---\n")
    i = 0
    for text_tag, separator in body_tags_to_search.items():
        tag = text_tag
        tag_class = None
        tag_id = None

        if len(text_tag.split(".")) > 1:
            tag = text_tag.split(".")[0]
            tag_class = text_tag.split(".")[1]

        if len(text_tag.split("#")) > 1:
            tag = text_tag.split("#")[0]
            tag_id = text_tag.split("#")[1]

        if len(soup.find_all(tag, class_=tag_class, id=tag_id)) > 0:
            valid_text_tags[text_tag] = []
            for obj_tag in soup.find_all(tag, class_=tag_class, id=tag_id):
                valid_text_tags[text_tag].append(obj_tag.text.strip())
            valid_text_tags[text_tag] = separator.join(valid_text_tags[text_tag])
            i = i + 1
            if not silent:
                print("-- text tag", i, "--")
                print("name:", text_tag)
                print("separator:", separator)
                print("texts:", valid_text_tags[text_tag])
                print("---------------- \n")
    return valid_text_tags


def _complementary_report(final_report, soup, silent):

    if len(final_report["a_links"]) > 0:
        final_report["first-a-link"] = final_report["a_links"][0]["href"]
        final_report["total-a-links"] = len(final_report["a_links"])
    else:
        final_report["first-a-link"] = ""
        final_report["total-a-links"] = 0

    if len(soup.find_all("meta")) > 0:
        final_report["total-meta-tags"] = len(soup.find_all("meta"))
    else:
        final_report["total-meta-tags"] = 0
    if not silent:
        print("\n\n\n----report---\n")
        for key in final_report:
            if key != "a_links":
                print("* ", key, ":", final_report[key])

    return final_report


def get_tags(url, sniffing_config={}, driver=None):
    return sniff_url(
        url=url, silent=True, sniffing_config=sniffing_config, driver=driver
    )


def get_url(url, driver=None):
    if driver is None and config.get_sniffing("use-browser"):
        driver = browser.get_driver()

    if driver is not None:
        try:
            driver.get(url)
            time.sleep(config.get_sniffing("browser-waiting-time"))
            driver.implicitly_wait(config.get_sniffing("browser-waiting-time"))
            return driver.page_source
        except:
            print("error")
            pass
    return requests.get(url=url, timeout=config.get_sniffing("timeout")).text
