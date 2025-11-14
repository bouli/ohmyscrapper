import requests
from bs4 import BeautifulSoup


def check_url(url='https://www.linkedin.com/in/cesardesouzacardoso/'):
    print("checking url:", url)

    r = requests.get(url=url)
    soup = BeautifulSoup(r.text, 'html.parser')

    print("\n\n\n\n---- all <meta> tags ---\n")
    i = 0
    for meta_tag in soup.find_all("meta"):
        i = i + 1
        print("-- meta tag", i ,"--")
        print("name:", meta_tag.get("name"))
        print("property:", meta_tag.get("property"))
        print("content:", meta_tag.get("content"))
        print("---------------- \n")


    print("\n\n\n\n---- all <a> links ---")
    i = 0
    for a_tag in soup.find_all("a"):
        i = i + 1
        print("\n-- a link", i ,"-- ")
        print("target:", a_tag.get("target"))
        print("text:", a_tag.text)
        print("href:", a_tag.get("href"))
        print("-------------- ")


    print("\n\n\n----report---\n")
    if len(soup.find_all("meta", property="og:url")) == 0:
        print("no <meta property='og:url'>")
    else:
        print("<meta property='og:url'>:", soup.find("meta", property="og:url").get("content"))
    print('\nfirst <a> link:', soup.find('a').get('href'))

    print('\nnumber of <a> links:', len(soup.find_all('a')))
    print('number of <meta> tags:', len(soup.find_all('meta')))
    print("\n")
