import os

from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems

import multiprocessing
import time
from TwitterAPI import TwitterAPI, TwitterRestPager
from elasticsearch import Elasticsearch

from yaml import load, dump


CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN_KEY = ''
ACCESS_TOKEN_SECRET = ''

SEARCH_TERM = 'docker'

es = Elasticsearch(os.environ["ES_URL"])

def worker():
    api = TwitterAPI(CONSUMER_KEY,
                     CONSUMER_SECRET,
                     ACCESS_TOKEN_KEY,
                     ACCESS_TOKEN_SECRET)

    pager = TwitterRestPager.TwitterRestPager(api, 'search/tweets', {'q': SEARCH_TERM})
    for item in pager.get_iterator():
        if 'text' in item:
            tweet = {}
            tweet['coordinates'] = item['coordinates']
            tweet['created_at'] = item['created_at']
            tweet['place'] = item['place']
            tweet['username'] = item['user']['name']
            tweet['handle'] = item['user']['screen_name']
            tweet['lang'] = item['lang']
            tweet['timezone'] = item['user']['timezone']
            tweet['followers'] = item['user']['followers_count']
            tweet['location'] = item['user']['location']
            tweet['retweeted'] = item['retweeted']
            tweet['text'] = item['text']
            es.index(index="tweets", doc_type="tweet", body=tweet)
    return

def wsgi_handler(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    stats = es.indices.stats(index="tweets", human=True)
    num_tweets = stats["_all"]["primaries"]["docs"]["count"]
    ENV = [bytes("%30s %s <br/>" % (key,os.environ[key]), "UTF-8") for  key in os.environ.keys()]
    return [bytes("Tweets = %s <br/><br/>" % (num_tweets, ), "UTF-8")] + ENV

class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def webapp():
    StandaloneApplication(wsgi_handler, {'bind': ':8080'}).run()

if __name__ == '__main__':
    api_key = open('/etc/secret-volume/app-secret')
    data = load(api_key)
    api_key.close()
    print(data)
    os.environ['secret'] = str(data)

    es.indices.create(index='tweets', ignore=400)
    jobs = []
    p1 = multiprocessing.Process(target=worker)
    jobs.append(p1)
    p1.start()
    p2 = multiprocessing.Process(target=webapp)
    jobs.append(p2)
    p2.start()
