import requests
from bs4 import BeautifulSoup


def check_url(url='https://www.linkedin.com/in/cesardesouzacardoso/'):
    print("checking url:", url)
    print("----all meta tags---")
    r = requests.get(url=url)
    soup = BeautifulSoup(r.text, 'html.parser')

    for meta_tag in soup.find_all("meta"):
        print("property:", meta_tag.get("property"))
        print("content:", meta_tag.get("content"))
        print("------- \n")

    print("----linkedin url---")

    if len(soup.find_all("meta", property="og:url")) == 0:
        print("no linkedin url")

    for meta_tag in soup.find_all("meta", property="og:url"):
        print("property:", meta_tag.get("property"))
        print("content:", meta_tag.get("content"))
        print("------- \n")

    print("----total links---")
    print('# of links', len(soup.find_all('a')))
