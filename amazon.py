import urllib, urllib2
import base64
import hmac
import time
from lxml import etree
from hashlib import sha256 as sha256
import cyclone.httpclient
from twisted.internet import defer

class AmazonLookup:

  action = 'GET'
  server = "webservices.amazon.com"
  path = "/onca/xml"

  def __init__(self, APIKey, APISecret, barcode):
    if len(barcode) == 12:
      self.barcode_type = 'UPC'
    elif len(barcode) == 13:
      self.barcode_type = 'EAN'
    else:
      raise InvalidBarcodeError
      
    self.AWS_ACCESS_KEY_ID = APIKey
    self.hmac = hmac.new(APISecret, digestmod=sha256)
    self.barcode = barcode

  @defer.inlineCallbacks
  def barcodeSearch(self):
    url = self.buildSignedLookupURL()
    title = yield self.makeRequestAndGetTitle(url)
    defer.returnValue(title)
    
  def buildSignedLookupURL(self):
    # sorted tuple of tuples for passing to urlencode
    params = tuple(sorted(
        (('AWSAccessKeyId', self.AWS_ACCESS_KEY_ID),
        ('IdType', self.barcode_type),
        ('ItemId', self.barcode),
        ('Operation', 'ItemLookup'),
        ('Service', 'AWSECommerceService'),
        ('SearchIndex', 'Music'),
        ('Timestamp', time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
        ('Version', '2009-11-02') ),
        key=lambda item: item[0]))

    paramString = urllib.urlencode(params)
    url = "http://" + AmazonLookup.server + AmazonLookup.path + "?" + paramString
    
    # Add the method and path and sign it
    self.hmac.update(AmazonLookup.action + "\n" +
            AmazonLookup.server + "\n" +
            AmazonLookup.path + "\n" +
            paramString)
    url += "&Signature=" + \
      urllib.quote(base64.encodestring(self.hmac.digest()).strip())

    return url
  
  @defer.inlineCallbacks
  def makeRequestAndGetTitle(self, url):
    resp = yield cyclone.httpclient.fetch(url)
    #print resp.read()
    tree = etree.fromstring(resp.body)
    NSMAP = {'atom': 'http://webservices.amazon.com/AWSECommerceService/2009-11-01'}
    try:
      title = tree.xpath('//atom:ItemAttributes/atom:Title/text()', namespaces=NSMAP)[0]
      artist = tree.xpath('//atom:ItemAttributes/atom:Artist/text()', namespaces=NSMAP)[0]
    except IndexError, e:
      artist = tree.xpath('//atom:ItemAttributes/atom:Creator/text()', namespaces=NSMAP)[0]
    results = {'title' : title, 'artist': artist}
    defer.returnValue(results)  
  