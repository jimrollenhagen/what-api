import sys
import json
import cyclone.escape
import cyclone.httpclient
import cyclone.web
from twisted.python import log
from twisted.internet import defer, reactor

from config import Config as c
from amazon import AmazonLookup
from whatcd import *

class IndexHandler(cyclone.web.RequestHandler):
  @defer.inlineCallbacks
  def get(self):
    self.write("Hello world!")

class BarcodeHandler(cyclone.web.RequestHandler):
  @defer.inlineCallbacks
  @cyclone.web.asynchronous
  def get(self, barcode):
    a = AmazonLookup(c.AWS_key, c.AWS_secret, barcode)
    d = yield a.barcodeSearch()
    self.finish(d)

class WhatHandler(cyclone.web.RequestHandler):
  #@defer.inlineCallbacks
  @cyclone.web.asynchronous
  def get(self):
    self.set_header("Content-Type", "application/json")
    scraper = WhatTorrentScraper(username=c.username,
      password=c.password,
      cookie=c.cookie)
    options = {}
    for arg in self.request.arguments:
      options[arg] = self.request.arguments[arg][0]
    d = scraper.search(options)
    #self.finish(cyclone.escape.json_encode({'options':options,'results':d}))
    self.finish(json.dumps({'options':options,'results':d}, sort_keys=False, indent=2))
    
class Application(cyclone.web.Application):
  def __init__(self):
    handlers = [
      (r"/", IndexHandler),
      (r"/barcode/([0-9]+)", BarcodeHandler),
      (r"/what/torrents/search", WhatHandler),
    ]
    
    settings = {
      "static_path": "./static",
      "template_path": "./template",
    }
    
    cyclone.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
  log.startLogging(sys.stdout)
  reactor.listenTCP(c.port, Application(), interface=c.host)
  reactor.run()