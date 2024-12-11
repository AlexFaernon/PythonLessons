from bs4 import BeautifulSoup
import requests


def run():
    url = "https://www.banki.ru/products/currency/usd/"
    response = requests.get(url)
    bs = BeautifulSoup(response.text, "lxml")
    result = []
    for i in bs.find('div', class_='Flexbox__sc-1yjv98p-0 feZtEw').children:
        result.append(i.text.replace('₽', 'Р'))

    return ' '.join(result)
