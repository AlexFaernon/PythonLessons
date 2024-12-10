from bs4 import BeautifulSoup
import requests


def run():
    url = ("https://rp5.ru/%D0%9F%D0%BE%D0%B3%D0%BE%D0%B4%D0%B0_%D0%B2_%D0%9A%D0%B0%D0%BC%D0%B5%D0%BD%D1%81%D0%BA%D0"
           "%B5-%D0%A3%D1%80%D0%B0%D0%BB%D1%8C%D1%81%D0%BA%D0%BE%D0%BC")
    response = requests.get(url)
    bs = BeautifulSoup(response.text, "lxml")
    return bs.find('div', id='archiveString').text
