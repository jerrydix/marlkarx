import re

import requests
from bs4 import BeautifulSoup
def crawl_quotes(url):
    content = requests.get(url).text
    soup = BeautifulSoup(content, features="html.parser")
    final_result = []
    for textelement in soup.find_all("li", text=True):
        textelement.extract()
    result = soup.find_all("li")

    for e in result:
        if not e.text == "" and not e.text[0].isdigit():
            final_result.append(e.text)

    finish = False
    quotes = []
    for e in final_result:
        x = re.search('\"(.*)\"', e)
        if x is not None and x.group(1).startswith('Die Analysen'):
            finish = True
        if x is not None and not finish:
            quotes.append(x.group(1))

    return quotes




crawl_quotes('https://de.wikiquote.org/wiki/Karl_Marx')