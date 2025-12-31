from selenium import webdriver
from selenium.webdriver.chrome.options import Options
def get_driver():
    chrome_options = Options()
    return webdriver.Chrome(options=chrome_options)
