import requests
from bs4 import BeautifulSoup
def crawl_quotes(url):
    content = requests.get(url).text
    soup = BeautifulSoup(content, features="html.parser")
    result = []
    for textelement in soup.find_all(text=True):
        textelement.extract()
        #print(soup.find_all('li'))
        #print(textelement)

    #elements = soup.find_all('li', string='\"')
    result = soup.find_all("li", {"class": ""})
    for e in result:
        print(e.getText)
        #for element in elements:
     #   print(element)

crawl_quotes('https://de.wikiquote.org/wiki/Karl_Marx')