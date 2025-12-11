import ohmyscrapper.models.urls_manager as urls_manager


def seed():
    urls_manager.seeds()
    print("db seeded")
    return
