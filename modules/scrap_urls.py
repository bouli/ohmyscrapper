import models.urls_manager as urls_manager
import modules.sniff_url as sniff_url
import modules.load_txt as load_txt
import modules.classify_urls as classify_urls

import time
import random



def process_linkedin_redirect(url_report, url):
    print('linkedin_redirect')

    if url_report['total-a-links'] < 5:
        url_destiny = url_report['first-a-link']
    else:
        if "og:url" in url_report.keys():
            url_destiny = url_report['og:url']
        else:
            print("no url for:", url['url'])
            return

    print(url['url'],">>", url_destiny)
    urls_manager.add_url(url_destiny)
    urls_manager.set_url_destiny(url['url'], url_destiny)

def process_linkedin_feed(url_report, url):
    print('linkedin_feed')
    url_destiny = url_report["og:url"]

    print(url['url'],">>", url_destiny)
    urls_manager.add_url(url_destiny)
    urls_manager.set_url_destiny(url['url'], url_destiny)

def process_linkedin_job(url_report, url):
    print('linkedin_job')

    print(url['url'],": ", url_report['h1'])

    urls_manager.set_url_h1(url['url'], url_report['h1'])

    if "description" in url_report.keys():
        urls_manager.set_url_description(url['url'], url_report['description'])
    elif "og:description" in url_report.keys():
        urls_manager.set_url_description(url['url'], url_report['og:description'])

def process_linkedin_post(url_report, url):
    print('linkedin_post')

    print(url['url'],": ", url_report['h1'])

    if('h1' in url_report.keys()):
        urls_manager.set_url_h1(url['url'], url_report['h1'])
    else:
        if('og:title' in url_report.keys()):
            urls_manager.set_url_h1(url['url'], url_report['og:title'])
    description = None
    if "description" in url_report.keys():
        description = url_report['description']
    elif "og:description" in url_report.keys():
        description = url_report['og:description']


    urls_manager.set_url_description(url['url'], description)
    description_links = load_txt.put_urls_from_string(description, url['id'])
    urls_manager.set_url_description_links(url['url'], description_links)


def scrap_url(url):
    #TODO: Use get_urls_valid_prefix_by_id()
    df = urls_manager.get_urls_valid_prefix()
    url_valid_prefixes = df.set_index(df.id).T.to_dict()

    #TODO: Need to change this
    if not isinstance(url['urls_valid_prefix_id'], int):
        url['urls_valid_prefix_id'] = 0

    url_valid_prefixes[0] = {'url_type': 'generic'}

    print("\n\n", url_valid_prefixes[url['urls_valid_prefix_id']]['url_type']+ ":", url['url'])
    #if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] != 'linkedin_redirect':
    #    return
    try:
        url_report = sniff_url.get_tags(url['url'])
    except Exception as e:
        urls_manager.set_url_error(url['url'], "errpr")
        urls_manager.touch_url(url['url'])
        print("\n\n!!! ERROR FOR:", url['url'])
        print("\n\n!!! you can check the URL using the command sniff-url", url['url'], "\n\n")
        return

    #linkedin_redirect - linkedin (https://lnkd.in/)
    if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] == 'linkedin_redirect':
        process_linkedin_redirect(url_report, url)

    #linkedin_feed - linkedin (https://%.linkedin.com/feed/)
    if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] == 'linkedin_feed':
        process_linkedin_feed(url_report, url)

     #linkedin_job - linkedin (https://www.linkedin.com/jobs/)
    if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] == 'linkedin_job':
        process_linkedin_job(url_report, url)

    #linkedin_job - linkedin (https://www.linkedin.com/jobs/)
    if url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] == 'linkedin_post' or url_valid_prefixes[url['urls_valid_prefix_id']]['url_type'] == 'generic':
        process_linkedin_post(url_report, url)

    urls_manager.set_url_json(url['url'], url_report['json'])
    urls_manager.touch_url(url['url'])



def scrap_urls(recursive=False, ignore_valid_prefix=False):
    urls = urls_manager.get_untouched_urls(ignore_valid_prefix=ignore_valid_prefix)
    for index, url in urls.iterrows():
        scrap_url(url)

        wait = random.randint(1, 4)
        print('sleeping for', wait, 'seconds')
        time.sleep(wait)

    classify_urls.classify_urls()
    if recursive:
        wait = random.randint(5, 10)
        print('sleeping for', wait, 'seconds before next round')
        time.sleep(wait)
        scrap_urls(recursive)
    else:
        print('ending...')
