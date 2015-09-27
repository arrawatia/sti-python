from TwitterAPI import TwitterAPI, TwitterRestPager
from elasticsearch import Elasticsearch
import json

CONSUMER_KEY = 'RAnytlvuGtSwPZggY6u5dSjKR'
CONSUMER_SECRET = 'zSRxICAPZngI7f5CjNXOoWfdYJCHnorowrndSLFNwEJgl4yHQW'
ACCESS_TOKEN_KEY = '23294783-zXL9G9k4sWY0RjigunHK8m3GOHpgwh2Xg0Lvvssop'
ACCESS_TOKEN_SECRET = 'VjMExv0hOZuCDCrrw2RDX0Hfo6AlyEb4p7l8jPDsaWRAq'




SEARCH_TERM = 'docker'




api = TwitterAPI(CONSUMER_KEY,
                 CONSUMER_SECRET,
                 ACCESS_TOKEN_KEY,
                 ACCESS_TOKEN_SECRET)

pager = TwitterRestPager.TwitterRestPager(api, 'search/tweets', {'q': SEARCH_TERM})

es = Elasticsearch()
es.indices.create(index='tweets', ignore=400)


for item in pager.get_iterator():
    if 'text' in item:
        es.index(index="tweets", doc_type="tweet", body=item)
    else:
        es.index(index="tweets", doc_type="message", body=item)

    stats = es.indices.stats(index="tweets", human=True)
    print(stats["_all"]["primaries"]["docs"]["count"])
