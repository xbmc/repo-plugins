import xbmcgui, xbmcplugin
from xbmcutil import urlhandler

import time, urllib, HTMLParser, re
from xml.dom.minidom import parseString

RSSUrl = 'http://kanaalz.knack.be/about-us/rss/article-1184741189408.htm?layout=ThemisRSS'

class ParseRSSPage(HTMLParser.HTMLParser):
    ''' Parse de RSS kanaal Z '''
    def __init__(self):
        global RSSUrl

        HTMLParser.HTMLParser.__init__(self)
 
        self.in_rsslinks = self.in_h5 = self.in_a = self.in_ul = self.in_li = False
        self.rssfeed = None
        self.data = ''
        self.categories = []

        # Parse the kanaal Z RSS page
        # Cache RSS page for 2 minutes so it is not reloaded when browsing through
        # directory
        page = urlhandler.urlread(RSSUrl, 120)
        if not page:
            print 'Error loading page ', RSSUrl
            return

        self.feed(page)
        self.close()

    def handle_starttag(self, tag, attrs):
        methodname = 'start_' + tag
        if hasattr(self, methodname):
            getattr(self, methodname)(attrs)

    def start_div(self, attrs):
        for attr, value in attrs:
            if attr == 'class' and 'rssLinks' in value:
                if self.in_rsslinks:
                    raise "kanaal Z RSS pagina niet begrepen"
                self.in_rsslinks = True
                
    def start_h5(self, attrs):
        if self.in_rsslinks:
            self.in_h5 = True

    def start_ul(self, attrs):
        if self.in_h5:
            raise "kanaal Z RSS pagina niet begrepen"
        if self.in_rsslinks:
            self.in_ul = True

    def start_li(self, attrs):
        if self.in_ul:
            self.in_li = True

    def start_a(self, attrs):
        if self.in_h5 or self.in_li:
            for attr, value in attrs:
                if attr == 'href':
                    self.rssfeed = value
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

    def end_h5(self):
        if self.in_a or self.in_li:
            raise "kanaal Z RSS pagina niet begrepen"
        if self.in_h5:
            self.categories.append([self.data, [(self.data + ' (alles)', self.rssfeed)]])
            self.data = ''
            self.in_h5 = False

    def end_li(self):
        if self.in_h5 or self.in_a:
            raise "kanaal Z RSS pagina niet begrepen"
        if self.in_li:
            if len(self.categories) == 0:
                raise "kanaal Z RSS pagina niet begrepen"
            self.categories[-1][1].append((self.data, self.rssfeed))
            self.data = ''
            self.in_li = False

    def end_ul(self):
        if self.in_li or self.in_h5:
            raise "kanaal Z RSS pagina niet begrepen"
        self.in_ul = False

    def end_div(self):
        if self.in_h5 or self.in_ul:
            raise "kanaal Z RSS pagina niet begrepen"
        self.in_rsslinks = False


def handle_event(myself, handle, params):
    if 'feed' in params:
        url = params['feed'][0]
        h = urlhandler.urlopen(url, 300)
        feed = h.read()
        h.close()
        dom = parseString(feed)
        re_src = re.compile("\'http://.*\'")
        for item in dom.getElementsByTagName('item'):
            title = url = thumb = date = None
            for node in item.childNodes:
                nodename = node.nodeName
                if nodename == 'title':
                    title = node.childNodes[0].nodeValue
                elif nodename == 'link':
                    url = myself + '?' + urllib.urlencode({'url': node.childNodes[0].nodeValue})
                elif nodename == 'description':
                    thumb = re_src.findall(node.childNodes[0].nodeValue)[0][1:-1]
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
        h = urlhandler.urlopen(params['url'][0], 7*24*60*60) # Cached for a week
        page = h.read()
        h.close()
        urls = re.compile('http://.*.mp4').findall(page)
        if len(urls) == 1:
            li = xbmcgui.ListItem(path=urls[0])
            xbmcplugin.setResolvedUrl(handle, True, li)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Oei', 'Video niet gevonden')
    else:
        p = ParseRSSPage()
        if 'categorie' in params:
            cat = params['categorie'][0]
            for cat2, feeds in p.categories:
                if cat2 == cat:
                    for name, feed in feeds:
                        li = xbmcgui.ListItem(name)
                        url = myself + '?' + urllib.urlencode({'feed': feed})
                        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True)
                    break
        else:
            for cat, feeds in p.categories:
                li = xbmcgui.ListItem(cat)
                url = myself + '?' + urllib.urlencode({'categorie': cat})
                xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True)

        xbmcplugin.endOfDirectory(handle, True)
