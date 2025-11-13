from urlextract import URLExtract
import models.urls_manager as urls_manager


def load_txt(file_name="input/_chat.txt"):
    urls_manager.create_tables()
    urls_manager.seeds()
    #make it recursive for all files
    text_file_content = open(file_name, "r").read()
    extractor = URLExtract()

    for url in extractor.find_urls(text_file_content):
        urls_manager.add_url(url)
        print(url , 'added')
    #move_it_to_processed
    print("--------------------")
    print(file_name, 'processed')
