import re
import sys
from ClientForm import ParseResponse
from util import getHTML, getUrllib2ResponseObject, cleanHTML, resizeImage
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup

#MAIN URLS
URLTED = 'http://www.ted.com'
URLTHEMES = 'http://www.ted.com/themes/atoz/page/'
URLSPEAKERS = 'http://www.ted.com/speakers/atoz/page/'
URLNEW = 'http://www.ted.com/talks/list/page/'
URLSEARCH = 'http://www.ted.com/search?q=%s/page/'
URLLOGIN = 'http://www.ted.com/users/signin/'
URLPROFILE = 'http://www.ted.com/profiles/view/id/'
URLFAVORITES = 'http://www.ted.com/profiles/favorites/id/'
URLADDFAV ='http://www.ted.com/profiles/addfavorites?id=%s&modulename=talks'
URLREMFAV ='http://www.ted.com/profiles/removefavorites?id=%s&modulename=talks'

pluginName = sys.modules['__main__'].__plugin__


class TedTalks:

    def getNavItems(self, html):
        """self.navItems={'next':url, 'previous':url, 'selected':pagenumberasaninteger}"""
        navItems = {'next':None, 'previous':None, 'selected':1}
        paginationContainer = SoupStrainer(attrs = {'class':re.compile('pagination')})
        for liTag in BeautifulSoup(html, parseOnlyThese = paginationContainer).findAll('li'):
            if liTag.a.has_key('class'):
                if liTag.a['class'] == 'next':
                    navItems['next'] = URLTED+liTag.a['href']
                elif liTag.a['class'] == 'previous':
                    navItems['previous'] = URLTED+liTag.a['href']
                elif liTag.a['class'] == 'selected':
                    navItems['selected'] = int(liTag.a.string)
            else: #no class attrib found.
                print '[%s] %s no pagination found.' % (pluginName, __name__)
        return navItems

    def getVideoDetails(self, url):
        """self.videoDetails={Title, Director, Genre, Plot, id, url}"""
        #TODO: get 'related tags' and list them under genre
        html = getHTML(url)
        soup = BeautifulSoup(html)
        #get title
        title = soup.find('span', attrs={'id':'altHeadline'}).string
        #get speaker from title
        speaker = title.split(':', 1)[0]
        #get description:
        plot = soup.find('p', attrs={'id':'tagline'}).string
        #get url
        for link in soup.findAll('a'):
            if re.match('Watch.*high-res' , str(link.string)):
                url = URLTED+link['href']
        #get id from url
        id = url.split('/')[-1]
        return {'Title':title, 'Director':speaker, 'Genre':'TED', 'Plot':plot, 'PlotOutline':plot, 'id':id, 'url':url}

    class User:
        """makes a user object"""

        def __init__(self, username = None, password = None):
            self.username = username
            self.password = password
            if username and password:
                self.id, self.realName = self.getUserDetails()
            else:
                self.id = self.realName = None

        def getUserDetails(self):
            html = self.getLoginResponse()
            userContainer = SoupStrainer(attrs = {'class':re.compile('notices')})
            for aTag in BeautifulSoup(html, parseOnlyThese = userContainer).findAll('a'):
                if aTag['href'].startswith(URLPROFILE):
                    id = aTag['href'].split('/')[-1]
                    realName = aTag.string.strip()
                    break
                else:
                    id = realName = None
            return id, realName

        def getLoginResponse(self, url = URLLOGIN):
            #clientform doesn't like HTML, and I don't want to monkey patch it, so getUrllib2ResponseObject was born.
            response = getUrllib2ResponseObject(url)
            forms = ParseResponse(response, backwards_compat=False)
            response.close()
            #set username & password in the signin form
            form = forms[1]
            form["users[username]"] = self.username
            form["users[password]"] = self.password
            form["users[rememberme]"] = ['1']
            #click submit
            return getHTML(form.click())

    class NewTalks:
        """self.videos=[{'link':link,'Title':title,'pic':pic},...]"""

        def __init__(self, url=None):
            if url is None:
                url = URLNEW
            self.html = getHTML(url)
            self.navItems = TedTalks().getNavItems(self.html)

        def getNewTalks(self):
            talkContainers = SoupStrainer(attrs = {'class':re.compile('talkMedallion')})
            for talk in BeautifulSoup(self.html, parseOnlyThese = talkContainers):
                link = URLTED+talk.dt.a['href']
                title = cleanHTML(talk.dt.a['title'])
                pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
                yield {'url':link, 'Title':title, 'Thumb':pic}

    class Speakers:

        def __init__(self, url=None):
            # adding 9999 to the url takes the script to the very last page of the list, providing the total # of pages.
            if url == None:
                url = URLSPEAKERS+'9999'
            self.html = getHTML(url)
            # only bother with navItems where they have a chance to appear.
            if URLSPEAKERS in url:
                self.navItems = TedTalks().getNavItems(self.html)

        def getSpeakers(self):
            # use getAllSpeakers instead... just leaving this function here for educational purposes.
            speakerContainers = SoupStrainer(attrs = {'href':re.compile('/speakers/\S.+?.html')})
            for speaker in BeautifulSoup(self.html, parseOnlyThese = speakerContainers):
                title = speaker.string
                link = URLTED+speaker['href']
                yield {'url':link, 'Title':title, 'label':title}

        def getAllSpeakers(self):
            speakerContainers = SoupStrainer(attrs = {'href':re.compile('/speakers/\S.+?.html')})
            for i in range(self.navItems['selected']):
                # don't parse the last page twice.
                if i is not 8:
                    html = getHTML(URLSPEAKERS+str(i+1))
                else:
                    html = self.html
                for speaker in BeautifulSoup(html, parseOnlyThese = speakerContainers):
                    title = speaker.string
                    link = URLTED+speaker['href']
                    yield {'url':link, 'Title':title}

        def getTalks(self):
            talkContainer = SoupStrainer(attrs = {'class':re.compile('box clearfix')})
            for talk in BeautifulSoup(self.html, parseOnlyThese = talkContainer):
                title = talk.h4.a.string
                link = URLTED+talk.dt.a['href']
                pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
                yield {'url':link, 'Title':title, 'Thumb':pic}

    class Themes:

        def __init__(self, url=None):
            if url == None:
                url = URLTHEMES
            self.html = getHTML(url)
            # a-z themes don't yet have navItems, so the check can be skipped for now.
            # self.navItems = TedTalks().getNavItems(html)

        def getThemes(self):
            themes = list()
            themeContainers = SoupStrainer(attrs = {'href':re.compile('/themes/\S.+?.html')})
            for theme in BeautifulSoup(self.html, parseOnlyThese = themeContainers):
                title = theme.string
                link = URLTED+theme['href']
                yield {'url':link, 'Title':title}

        def getTalks(self):
            # themes loaded with a json call. Why are they not more consistant?
            from simplejson import loads
            # search HTML for the link to tedtalk's "api".  It is easier to use regex here than BS.
            jsonUrl = URLTED+re.findall('DataSource\("(.+?)"', self.html)[0]
            # make a dict from the json formatted string from above url
            talksMarkup = loads(getHTML(jsonUrl))
            # parse through said dict for all the metadata
            for markup in talksMarkup['resultSet']['result']:
                talk = BeautifulSoup(markup['markup'])
                link = URLTED+talk.dt.a['href']
                title = cleanHTML(talk.dt.a['title'])
                pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
                yield {'url':link, 'Title':title, 'Thumb':pic}

    class Favorites:

        def getFavoriteTalks(self, user, url = URLFAVORITES):
            """user must be TedTalks().User object with .id attribute"""
            if user.id is not None:
                html = getHTML(url+user.id)
                talkContainer = SoupStrainer(attrs = {'class':re.compile('box clearfix')})
                for talk in BeautifulSoup(html, parseOnlyThese = talkContainer):
                    title = talk.h4.a.string
                    link = URLTED+talk.dt.a['href']
                    pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
                    yield {'url':link, 'Title':title, 'Thumb':pic}
            else:
                print '[%s] %s invalid user object' % (pluginName, __name__)

        def addToFavorites(self, user, url):
            """user must be TedTalks().User object with .id attribute"""
            if user.id is not None:
                id = TedTalks().getVideoDetails(url)['id']
                print id
                response = getHTML(URLADDFAV % (id))
                if response:
                    print '[%s] %s addToFavorites success' % (pluginName, __name__)
                    return True
            else:
                print '[%s] %s invalid user object' % (pluginName, __name__)

        def removeFromFavorites(self, user, url):
            """user must be TedTalks().User object with .id attribute"""
            if user.id is not None:
                id = TedTalks().getVideoDetails(url)['id']
                print id
                response = getHTML(URLREMFAV % (id))
                if response:
                    print '[%s] %s removeFromFavorites success' % (pluginName, __name__)
                    return True
            else:
                print '[%s] %s invalid user object' % (pluginName, __name__)

    class Search:
        pass
        #TODO: SEARCH
