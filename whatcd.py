import errors
import os
import urllib, urllib2
import cookielib
import re
from lxml import html

class WhatScraper:

  loginURL = 'https://ssl.what.cd/login.php'
  userAgent = 'WhatAPI [ridejkcl]'

  def __init__(self, username, password, cookie):
    self.username = username
    self.password = password
    self.cookieFile = cookie

    self.setUpCookiesAndUserAgent()

  def setUpCookiesAndUserAgent(self):
    
    cookieJar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [('User-Agent', WhatScraper.userAgent)]
    urllib2.install_opener(opener)

    self.loadCookiesFromFile(cookieJar)
    
    try:
      self.authenticate()
    except errors.AuthError:
      self.getFreshCookies()

  def loadCookiesFromFile(self, cookieJar):
    try:
      cookieJar.load(self.cookieFile)
    except IOError:
      self.authenticate()
      cookieJar.save(self.cookieFile)
      
  def getFreshCookies(self):
    cookieJar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener.addheaders = [('User-Agent', WhatScraper.userAgent)]
    urllib2.install_opener(opener)
    self.authenticate()
    cookieJar.save(self.cookieFile)

  def authenticate(self):
    data = urllib.urlencode({'username': self.username,
                 'password': self.password,
                 'keeplogged': '1',
                 'login': 'Login'})
    request = urllib2.Request(WhatScraper.loginURL, data)
    response = urllib2.urlopen(request)
    self.checkIfAuthenticated(response)

  def checkIfAuthenticated(self, response):
    page = html.parse(response).getroot()
    #print(html.tostring(page))
    if (page.xpath('head/title/text()')[0] == 'Login :: What.CD'):
      raise errors.AuthError('Login page returned, not logged in')

  def hasClass(self, element, testClass):
    return testClass in element.attrib['class'].split(' ')

class WhatTorrentScraper(WhatScraper):

  def search(self, searchParams):

    baseURL = 'https://ssl.what.cd/torrents.php?'
    searchParams['action'] = 'advanced'
    searchURL = baseURL + urllib.urlencode(searchParams)
    torrentPage = urllib2.urlopen(searchURL)

    return self.parseSearchPage(torrentPage)

  def parseSearchPage(self, torrentPage):

    pageHTML = html.parse(torrentPage).getroot()
    data = {}
    data['groups'] = []
    data['torrents'] = []

    # Get the table
    try:
      torrentTable = self.getTorrentTable(pageHTML)
    except KeyError:
      return []

    for tableRow in torrentTable:
      if self.isNotMusic(tableRow):
        pass
      elif self.isGroup(tableRow):
        newGroup = self.produceNewGroup(tableRow)
        data['groups'].append(newGroup)
      elif self.isEdition(tableRow):
        newEdition = self.produceNewEdition(tableRow)
        editionList = data['groups'][-1]['editions']
        editionList.append(newEdition)
      else:
        newFormat = self.produceNewFormat(tableRow)
        formatList = data['groups'][-1]['editions'][-1]['formats']
        formatList.append(newFormat['torrentID'])
        data['torrents'].append(newFormat)

    return data

  def getTorrentTable(self, pageHTML):
    torrentTable = pageHTML.get_element_by_id('torrent_table')
    # ignore the table header
    del torrentTable[0]
    return torrentTable

  def isNotMusic(self, tableRow):
    return self.hasClass(tableRow, 'torrent')

  def isGroup(self, tableRow):
    return self.hasClass(tableRow, 'group')

  def isEdition(self, tableRow):
    return len(tableRow.find_class('edition_info')) == 1

  def produceNewGroup(self, tableRow):
    newGroup = {}

    # return the text contents of all links in the 3rd td into an array
    linktext = tableRow.xpath('td[3]/a/text()')
    # get the urls of all the links in the title row
    urls = tableRow.xpath('td[3]/a/@href')

    # If the title of the first link is View Torrent then it is VA
    if self.isVA(tableRow):
      artist = 'Various Artists'
      artistID = '0'
      # first link has album name and ID
      album = linktext[0]
      albumID = urls[0].split('=')[-1]
    else:
      # first link has artist info, second has album info
      artist = linktext[0]
      artistID = urls[0].split('=')[-1]
      album = linktext[1]
      albumID = urls[1].split('=')[-1]

    # 3rd td element has year in 3rd from last textnode
    year = tableRow.xpath('td[3]/child::text()')[-3].strip(' \n\t\r[]')

    # 'tags' element has tag links, link text has tags
    tags = tableRow.find_class('tags')[0].xpath('a/text()')

    newGroup['artist'] = artist
    newGroup['artistID'] = artistID
    newGroup['album'] = album
    newGroup['albumID'] = albumID
    newGroup['year'] = year
    newGroup['tags'] = tags
    newGroup['editions'] = []

    return newGroup

  def produceNewEdition(self, tableRow):
    newEdition = {}
    editionInfo = tableRow.find_class('edition_info')[0].xpath('strong/text()')[0]
    newEdition['edition_info'] = editionInfo
    newEdition['formats'] = []
    return newEdition

  def produceNewFormat(self, tableRow):
    newFormat = {}

    # here I just have the xpath that points directly to each bit of torrentData
    newFormat['quality'] = tableRow.xpath('td[1]/a[1]/text()')[0]
    newFormat['torrentID'] = tableRow.xpath('td[1]/a[1]/@href')[0].split('=')[-1]
    newFormat['files'] = tableRow.xpath('td[2]/text()')[0]
    newFormat['uploaded'] = tableRow.xpath('td[3]/span[1]/text()')[0]
    newFormat['size'] = tableRow.xpath('td[4]/text()')[0]
    try:
      newFormat['snatches'] = tableRow.xpath('td[5]/text()')[0]
    except IndexError:
      newFormat['snatches'] = 0
    try:
      newFormat['seeders'] = tableRow.xpath('td[6]/text()')[0]
    except IndexError:
      newFormat['seeders'] = 0
    try:
      newFormat['leechers'] = tableRow.xpath('td[7]/text()')[0]
    except IndexError:
      newFormat['leechers'] = 0

    return newFormat

  def isVA(self, tableRow):
    return 'View Torrent' in tableRow.xpath('td[3]/a[1]/@title')

class WhatRequestScraper(WhatScraper):

  def search(self, searchParams):

    baseURL = 'https://ssl.what.cd/requests.php?'
    searchParams['submit'] = 'true'
    searchParams['filter_cat[1]'] = '1' # music only
    searchURL = baseURL + urllib.urlencode(searchParams)
    requestPage = urllib2.urlopen(searchURL)

    return self.parseSearchPage(requestPage)

  def parseSearchPage(self, requestPage):

    pageHTML = html.parse(requestPage).getroot()
    requestData = []

    # Get the table
    try:
      requestTable = self.getRequestTable(pageHTML)
    except KeyError:
      return ['error']

    if (self.isEmpty(requestTable)):
      return ['no results']

    for tableRow in requestTable:
      requestData.append(self.produceNewRequest(tableRow))

    return requestData

  def isEmpty(self, requestTable):
    return len(requestTable.xpath('tr[1]/td')) == 1

  def getRequestTable(self, pageHTML):
    #requestTable = pageHTML.find_class('border')[1]
    requestTable = pageHTML.get_element_by_id('request_table')
    # ignore the table header
    del requestTable[0]
    return requestTable

  def produceNewRequest(self, tableRow):
    newRequest = {}

    # return the text contents of all links in the 1st td into an array
    links = tableRow.xpath('td[1]/a')

    # check if row is VA
    if (self.isVA(links)):
      artist = 'Various Artists'
      artistID = '0'
      request = links[0].text
      requestID = links[0].get('href').split('=')[-1]

    else:
      artist = links[0].text
      artistID = links[0].get('href').split('=')[-1]
      # look for last link for case of <artist> with <another artist> - <request>
      request = links[-1].text
      requestID = links[-1].get('href').split('=')[-1]

    albumAndYear = re.search(r'(.*?) \[(\d*)\]', request)
    album = albumAndYear.group(1)
    year = albumAndYear.group(2)

    # 'tags' element has tag links, link text has tags
    tags = tableRow.find_class('tags')[0].xpath('a/text()')

    '''
    <td> 
      <form id="form_116019"> 
        <span id="vote_count_116019">1</span> 
        <input type="hidden" id="requestid_116019" name="requestid" value="116019" /> 
        <input type="hidden" id="auth" name="auth" value="8b846e19c500b88bc9c5ff8f4ed0f040" /> 
        &nbsp;&nbsp; <a href="javascript:Vote(0, 116019)"><strong>(+)</strong></a> 
      </form>
    </td>
    
    ['__class__', '__contains__', '__copy__', '__deepcopy__', '__delattr__', '__delitem__', '__dict__', '__doc__', '__format__', '__getattribute__', '__getitem__', '__hash__', '__init__', '__iter__', '__len__', '__module__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_action__del', '_action__get', '_action__set', '_fields__get', '_fields__set', '_init', '_label__del', '_label__get', '_label__set', '_method__get', '_method__set', '_name', 'action', 'addnext', 'addprevious', 'append', 'attrib', 'base', 'base_url', 'body', 'clear', 'cssselect', 'drop_tag', 'drop_tree', 'extend', 'fields', 'find', 'find_class', 'find_rel_links', 'findall', 'findtext', 'form_values', 'forms', 'get', 'get_element_by_id', 'getchildren', 'getiterator', 'getnext', 'getparent', 'getprevious', 'getroottree', 'head', 'index', 'inputs', 'insert', 'items', 'iter', 'iterancestors', 'iterchildren', 'iterdescendants', 'iterfind', 'iterlinks', 'itersiblings', 'itertext', 'keys', 'label', 'make_links_absolute', 'makeelement', 'method', 'nsmap', 'prefix', 'remove', 'replace', 'resolve_base_href', 'rewrite_links', 'set', 'sourceline', 'tag', 'tail', 'text', 'text_content', 'values', 'xpath']
    '''
    # votes have now been wrapped in a form, this is the only form in tableRow
    # first element in the form is a span containing the vote count
    votes = tableRow.forms[0].getchildren()[0].text.strip(' \n\t\r[]')
    
    bounty = tableRow.xpath('td[3]/child::text()')[0].strip(' \n\t\r[]')

    requester = tableRow.xpath('td[6]/a/text()')[0]
    requesterID = tableRow.xpath('td[6]/a/@href')[0].split('=')[-1]

    created = tableRow.xpath('td[7]/span/@title')[0]
    lastVote = tableRow.xpath('td[8]/span/@title')[0]

    newRequest['artist'] = artist
    newRequest['artistID'] = artistID
    newRequest['album'] = album
    newRequest['requestID'] = requestID
    newRequest['year'] = year
    newRequest['tags'] = tags
    newRequest['votes'] = votes
    newRequest['bounty'] = bounty
    newRequest['requester'] = requester
    newRequest['requesterID'] = requesterID
    newRequest['created'] = created
    newRequest['lastVote'] = lastVote

    return newRequest

  def isVA(self, links):
    return len(links) == 1