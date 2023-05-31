
from duckduckgo_search import DDGS
from magic_google import MagicGoogle

query = "Liverpool"
search_result = DDGS().text(query, region="us-en", safesearch='Off', timelimit='y')
for search_item in search_result:
    print(search_item["body"])

search_result = DDGS().news(query, region="us-en", safesearch='Off', timelimit='y')
for search_item in search_result:
    print(search_item["body"])

PROXIES = None
# PROXIES = [{
#     'http': 'http://192.168.2.207:1080',
#     'https': 'http://192.168.2.207:1080'
# }]

magicgoogle = MagicGoogle(PROXIES)
for i in magicgoogle.search(query=query, num=5):
    print(i["url"])

