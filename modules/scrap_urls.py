import requests
from bs4 import BeautifulSoup
import models.urls_manager as urls_manager


def process_linkedin_redirect(soup, url):
    print('linkedin_redirect')
    if len(soup.find_all('a')) < 5:
        url_destiny = soup.find('a').get('href')
    else:
        if len(soup.find_all("meta", property="og:url")) > 0:
            url_destiny = soup.find("meta", property="og:url").get("content")
        else:
            print("no url for:", url['url'])
            return

    print(url['url'],">>", url_destiny)
    urls_manager.set_url_destiny(url['url'], url_destiny)
    urls_manager.add_url(url_destiny)

def process_linkedin_feed(soup, url):
    print('linkedin_feed')
    url_destiny = soup.find("meta", property="og:url").get("content")

    print(url['url'],">>", url_destiny)
    urls_manager.set_url_destiny(url['url'], url_destiny)
    urls_manager.add_url(url_destiny)

def scrap_url(url):
    #prefixes
    df = urls_manager.get_urls_valid_prefix()
    url_valid_prefixes = df.set_index(df.id).T.to_dict()

    print(url_valid_prefixes[url['urls_valid_prefix_id']]['url_type']+ ":", url['url'])
    if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] != 'linkedin_redirect':
        return

    r = requests.get(url=url['url'])
    soup = BeautifulSoup(r.text, 'html.parser')

    #linkedin_redirect - linkedin (https://lnkd.in/)
    if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] == 'linkedin_redirect':
        process_linkedin_redirect(soup, url)

    #linkedin_feed - linkedin (https://%.linkedin.com/feed/)
    if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] == 'linkedin_feed':
        process_linkedin_feed(soup, url)




    for meta_tag in soup.find_all("meta"):
        #linkedin_feed - linkedin (https://www.linkedin.com/feed/)
        #redirect to og:url

        #linkedin_redirect - linkedin (https://lnkd.in/)
        if False and meta_tag.get("property") == 'og:description' and meta_tag.get("content") == "This link will take you to a page that’s not on LinkedIn":
            for link in soup.find_all('a'):
                print("link:"+link.get('href'))
            print("------- \n")

        #linkedin_job - linkedin (https://www.linkedin.com/jobs/)
        if False and meta_tag.get("property") == 'og:type' and meta_tag.get("content") == "website":
            #meta_tag.get("property") == 'og:title'
            #meta_tag.get("property") == 'lnkd:url'
            print(meta_tag.get("content"))
            print(meta_tag.get("property"))
            print("------- \n")

        #linkedin_post - linkedin (https://www.linkedin.com/posts/)
        #og:description


        if False:
            print("content:" , meta_tag.get("content"))
            print("property:" , meta_tag.get("property"))
            print("------- \n")
            #og:description
            #og:title
            #og:type
            #og:url


def scrap_urls():
    urls = urls_manager.get_untouched_urls()
    for index, url in urls.iterrows():
        scrap_url(url)
