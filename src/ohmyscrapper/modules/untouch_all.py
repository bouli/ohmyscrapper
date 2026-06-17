import ohmyscrapper.models.urls_manager as urls_manager


def untouch_all():
    urls_manager.untouch_all_urls()
    print("🙌 urls have been untouched")
    return


def untouch_all_urls_with_errors(include_warnings=False):
    urls_manager.untouch_all_urls_with_errors(include_warnings=include_warnings)
    print("🙌 urls with errors have been untouched")
    return
