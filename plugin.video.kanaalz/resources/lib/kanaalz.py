import xbmcgui, xbmcplugin
from xbmcutil import urlhandler

import time, urllib, HTMLParser, re
from xml.dom.minidom import parseString

class LocalException(Exception):
    def __init__(self, desc):
        self.desc = desc

RSSroot = 'http://kanaalz.knack.be'
RSSUrl = RSSroot+ '/rss/'

class ParseRSSPage(HTMLParser.HTMLParser):
    ''' Parse de RSS kanaal Z pagina'''
    def __init__(self):
        global RSSUrl

        HTMLParser.HTMLParser.__init__(self)
 
        self.in_ul = self.in_li = self.in_a = False
        self.rssfeed = None
        self.data = ''
        self.feeds = []

        # Parse the kanaal Z RSS page
        # Cache RSS page for 2 minutes so it is not reloaded when browsing through
        # directory
        page = urlhandler.urlread(RSSUrl, 120)
        if not page:
            raise LocalException('Fout tijdens laden pagina '+RSSUrl)
        self.feed(page)
        self.close()
        # reshuffle feeds
        m = max([len(f) for f in self.feeds])
        feeds = []
        for i in range(m):
            for f in self.feeds:
                if i < len(f):
                    feeds.append(f[i])
        self.feeds = feeds

    def handle_starttag(self, tag, attrs):
        methodname = 'start_' + tag
        if hasattr(self, methodname):
            getattr(self, methodname)(attrs)

    def start_ul(self, attrs):
        for attr, value in attrs:
            if attr == 'class' and 'feedList' in value:
                if self.in_ul:
                    raise LocalException("kanaal Z RSS pagina niet begrepen")
                self.feeds.append([])
                self.in_ul = True

    def start_li(self, attrs):
        if self.in_ul:
            self.in_li = True

    def start_a(self, attrs):
        global RSSroot
        if self.in_li:
            for attr, value in attrs:
                if attr == 'href':
                    self.rssfeed = RSSroot + value
            self.in_a = True

    def handle_data(self, data):
        if self.in_a:
            self.data += data

    def handle_endtag(self, tag):
        methodname = 'end_' + tag
        if hasattr(self, methodname):
            getattr(self, methodname)()

    def end_a(self):
        self.in_a = False

    def end_li(self):
        if self.in_ul:
            self.feeds[-1].append((self.data, self.rssfeed))
            self.data = ''
            self.in_li = False

    def end_ul(self):
        if self.in_li:
            raise LocalException("kanaal Z RSS pagina niet begrepen")
        self.in_ul = False


def handle_event(myself, handle, params):
    try:
        if 'feed' in params:
            url = params['feed'][0]
            h = urlhandler.urlopen(url, 300)
            feed = h.read()
            h.close()
            dom = parseString(feed)
            re_src = re.compile('\"(http://\S*)\"')
            for item in dom.getElementsByTagName('item'):
                title = url = thumb = date = None
                for node in item.childNodes:
                    nodename = node.nodeName
                    if nodename == 'title':
                        title = node.childNodes[0].nodeValue
                    elif nodename == 'link':
                        url = myself + '?' + urllib.urlencode({'url': node.childNodes[0].nodeValue})
                    elif nodename == 'description':
                        thumb = re_src.findall(node.childNodes[0].nodeValue)[0]
                    elif nodename == 'pubDate':
                        date = time.strptime(node.childNodes[0].nodeValue[:-6], '%a, %d %b %Y %H:%M:%S')
                li = xbmcgui.ListItem(title, thumbnailImage=thumb)
                li.setInfo('video', {
                    'title': title,
                    'date': time.strftime('%d.%m.%Y', date)
                })
                li.setProperty("IsPlayable","true")
                xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)

            xbmcplugin.endOfDirectory(handle, True)
        elif 'url' in params:
            global RSSroot
            h = urlhandler.urlopen(params['url'][0], 7*24*60*60) # Cached for a week
            page = h.read()
            h.close()
            redirects = re.compile('src="(/embed/\S*)"').findall(page)
            if len(redirects) < 1:
                raise LocalException('Video niet gevonden')
            h = urlhandler.urlopen(RSSroot+redirects[0], 7*24*60*60) # Cached for a week
            page = h.read()
            h.close()
            urls = re.compile('http://.*.mp4').findall(page)
            if len(urls) < 1:
                raise LocalException('Video niet gevonden')
            li = xbmcgui.ListItem(path=urls[0])
            xbmcplugin.setResolvedUrl(handle, True, li)
        else:
            p = ParseRSSPage()
            for name, feed in p.feeds:
                li = xbmcgui.ListItem(name)
                url = myself + '?' + urllib.urlencode({'feed': feed})
                xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True)
            xbmcplugin.endOfDirectory(handle, True)
    except LocalException as e:
        dialog = xbmcgui.Dialog()
        dialog.ok('Oei', e.desc)
    except:
        dialog = xbmcgui.Dialog()
        dialog.ok('Oei', 'Fout met interpretatie pagina')
