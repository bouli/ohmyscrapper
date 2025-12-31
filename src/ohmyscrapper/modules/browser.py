from selenium import webdriver
from ohmyscrapper.core.config import get_sniffing


def get_driver():
    if get_sniffing("use-browser") == "safari":
        from selenium.webdriver.safari.options import Options

        options = Options()
        driver = webdriver.Safari(options=options)
    elif get_sniffing("use-browser") == "firefox":
        from selenium.webdriver.firefox.options import Options

        options = Options()
        driver = webdriver.Firefox(options=options)
    elif get_sniffing("use-browser") == "ie":
        from selenium.webdriver.ie.options import Options

        options = Options()
        driver = webdriver.Ie(options=options)
    else:  # default: chrome
        from selenium.webdriver.chrome.options import Options

        options = Options()
        driver = webdriver.Chrome(options=options)

    return driver
