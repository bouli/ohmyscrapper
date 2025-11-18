import models.urls_manager as urls_manager
def show_urls(limit=0):
    print(urls_manager.get_urls(limit))
    return

def show_urls_valid_prefix(limit=0):
    print(urls_manager.get_urls_valid_prefix(limit))
    return

def show_url(url):
    print(urls_manager.get_url_by_url(url).T)
    return
