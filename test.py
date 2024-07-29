
from urllib.request import Request, urlopen, urlretrieve
from PIL import Image

req = Request('https://img-cdn.hltv.org/teamlogo/JDASXOcCuy4917jsIRv-nR.png?ixlib=java-2.1.0&w=50&s=ee3031cb889a8aee621780863f0d249a')
req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36')
content = urlopen(req).read()
with open('gfg.webp', 'wb') as f:
    f.write(content)
img = Image.open("gfg.webp")
img.show()