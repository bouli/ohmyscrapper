import ohmyscrapper.models.urls_manager as urls_manager


def untouch_all():
    urls_manager.untouch_all_urls()
    print("🙌 urls have been untouched")
    return


def untouch_all_urls_with_errors():
    urls_manager.untouch_all_urls_with_errors()
    print("🙌 urls with errors have been untouched")
    return
