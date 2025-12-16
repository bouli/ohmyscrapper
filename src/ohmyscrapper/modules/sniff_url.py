import requests
from bs4 import BeautifulSoup
import json


def sniff_url(url="https://www.linkedin.com/in/cesardesouzacardoso/", silent=False):
    if not silent:
        print("checking url:", url)
    report_meta_tags = []
    tags_to_search = [
        "description",
        "og:url",
        "og:title",
        "og:description",
        "og:type",
        "lnkd:url",
    ]

    r = requests.get(url=url)
    soup = BeautifulSoup(r.text, "html.parser")

    if not silent:
        print("\n\n\n\n---- all <meta> tags ---\n")
    i = 0
    for meta_tag in soup.find_all("meta"):
        if (
            meta_tag.get("name") in tags_to_search
            or meta_tag.get("property") in tags_to_search
        ):
            report_meta_tags.append(meta_tag)
        i = i + 1
        if not silent:
            print("-- meta tag", i, "--")
            print("name:", meta_tag.get("name"))
            print("property:", meta_tag.get("property"))
            print("content:", meta_tag.get("content"))
            print("---------------- \n")

    if not silent:
        print("\n\n\n\n---- all <a> links ---")
        i = 0
        for a_tag in soup.find_all("a"):
            i = i + 1
            print("\n-- a link", i, "-- ")
            print("target:", a_tag.get("target"))
            print("text:", a_tag.text)
            print("href:", a_tag.get("href"))
            print("-------------- ")

    final_report = {}
    final_report["scrapped-url"] = url
    if len(soup.find_all("h1")) > 0:
        final_report["h1"] = soup.find("h1").text

    for report_meta_tag in report_meta_tags:
        if report_meta_tag.get("name") is not None:
            final_report[report_meta_tag.get("name")] = report_meta_tag.get("content")
        elif report_meta_tag.get("property") is not None:
            final_report[report_meta_tag.get("property")] = report_meta_tag.get(
                "content"
            )

    if len(soup.find_all("a")) > 0:
        final_report["first-a-link"] = soup.find("a").get("href")
        final_report["total-a-links"] = len(soup.find_all("a"))
    else:
        final_report["first-a-link"] = ""
        final_report["total-a-links"] = 0

    if len(soup.find_all("h2")) > 0:
        final_report["h2"] = soup.find("h2").text

    if len(soup.find_all("meta")) > 0:
        final_report["total-meta-tags"] = len(soup.find_all("meta"))
    else:
        final_report["total-meta-tags"] = 0

    final_report["json"] = json.dumps(final_report)
    if not silent:
        print("\n\n\n----report---\n")
        for key in final_report:
            print("* ", key, ":", final_report[key])

    return final_report


def get_tags(url):
    return sniff_url(url=url, silent=True)
