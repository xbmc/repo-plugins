# -*- coding: utf-8 -*-
import re
import sys
import simplejson
from ClientForm import ParseResponse
from util import getHTML, getUrllib2ResponseObject, cleanHTML
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup

# MAIN URLS
URLASI = 'http://www.arretsurimages.net'
URLLOGIN = 'http://www.arretsurimages.net/forum/login.php'
URLMONCOMPTE = 'http://www.arretsurimages.net/forum/control.php?panel=summary'
IPHONEVIDEO = 'http://iphone.dailymotion.com/video/'
JSONREQUEST = 'http://www.dailymotion.com/json/video/%s?fields=title,thumbnail_url,stream_h264_hq_url,stream_h264_url'


pluginName = sys.modules['__main__'].__plugin__


class ArretSurImages:

    def getNavItems(self, html):
        """Return the navigation items"""
        navItems = {'next':None, 'previous':None}
        filterContainer = SoupStrainer(attrs = {'class':re.compile('rech-filtres-droite')})
        # There are two 'rech-filtres-droite' per page. Look only in the first one (contents[0])
        for aTag in BeautifulSoup(html, parseOnlyThese = filterContainer).contents[0].findAll('a'):
            if aTag.has_key('href'):
                if aTag.string == '&gt;':
                    navItems['next'] = URLASI + aTag['href']
                elif aTag.string == '&lt;':
                    navItems['previous'] = URLASI + aTag['href']
            else:
                print '[%s] %s no navigation items found.' % (pluginName, __name__)
        return navItems

    def getVideoDownloadLink(self, url):
        """Return the video title and download link"""
        title = None
        link = None
        html = getHTML(url)
        soup = BeautifulSoup(html)
        # Look for the download link image
        img = soup.find('img', attrs = {'src':'http://www.arretsurimages.net/images/boutons/bouton-telecharger.png'})
        if img:
            downloadPage = img.findParent()['href']
            print downloadPage
            if downloadPage.endswith('.avi'):
                title = downloadPage.split('/')[-1]
                print title
                html = getHTML(downloadPage)
                soup = BeautifulSoup(html)
                click = soup.find(text=re.compile('cliquer ici'))
                if click:
                    link = click.findParent()['href']
                    print link
                else:
                    print "No \"cliquer ici\" found"
        else:
            print "bouton-telecharger.png not found"
        return {'Title':title, 'url':link}

    def getIphoneVideoDetails(self, url):
        """Return the video title and link"""
        html = getHTML(url)
        soup = BeautifulSoup(html)
        # Get title and url
        videoTitle = soup.find('a', attrs = {'class':'title'})
        if videoTitle:
            title = videoTitle.string
        else:
            title = 'ASI'
        videoLink = soup.find(type="video/x-m4v")
        if videoLink:
            link = videoLink['href']
        else:
            link = 'None'
        return {'Title':title, 'url':link}

    def getIphoneProgramParts(self, url, name):
        """Return all parts of a program"""
        html = getHTML(url)
        soup = BeautifulSoup(html)
        parts = []
        # Get the different parts
        part = 0
        for media in soup.findAll(text=re.compile(u'.*title="voir la vidéo".*')):
            match = re.search(u'href="(.*?)"', media)
            if match:
                part += 1
                partLink = match.group(1)
                partTitle = name + ' - Acte %d' % (part)
            match = re.search(u'img src="(.*?)"', media)
            if match:
                partThumb = URLASI + match.group(1)
            parts.append({'url':partLink, 'Title':partTitle, 'Thumb':partThumb})
        # If there is only one part, we keep only one link
        if part == 1 and len(parts) == 2:
            parts.pop()
        return parts

    def getVideoDetails(self, url, streams):
        """Return the video title and link"""
        # Run the json request using the video id
        # passed in url argument
        request = getHTML(JSONREQUEST % url)
        result = simplejson.loads(request)
        # The stream quality chosen might not be available
        # -> get the first video link available (following the streams quality order)
        for stream in streams:
            if result[stream]:
                print "Found %s link" % stream
                link = result[stream]
                break
        else:
            print "No video link found for this video id"
            link = 'None'
        title = result["title"]
        return {'Title':title, 'url':link}

    def getProgramParts(self, url, name, icon):
        """Return all parts of a program (video id)

        video id allows to get video url with a json request"""
        html = getHTML(url)
        # Filter to avoid wrap-porte (La chronique porte) defined at the beginning
        # of the html page
        blocContainers = SoupStrainer(attrs = {'class':'contenu-html bg-page-contenu'})
        soup = BeautifulSoup(html, parseOnlyThese = blocContainers)
        parts = []
        part = 1
        # Get all movie id
        for param in soup.findAll('param', attrs = {'name':'movie'}):
            try:
                videoId = param.parent["id"]
            except KeyError:
                continue
            title = name + ' - Acte %d' % part
            # Try to get the icon linked to the iPhone video on that page
            # That's faster than getting it from the json request (see getVideoDetails),
            # which would require one extra HTML request for each part
            try:
                media = param.parent.parent.find(text=re.compile(u'img src='))
                match = re.search(u'img src="(.*?)"', media)
                thumb = URLASI + match.group(1)
            except (TypeError, AttributeError):
                thumb = icon
            parts.append({'url':videoId, 'Title':title, 'Thumb':thumb})
            part += 1
        return parts

    def isLoggedIn(self, username):
        """Return True if @username is already logged in,
        False otherwise"""
        html = getHTML(URLMONCOMPTE)
        soup = BeautifulSoup(html)
        if soup.title.string == u'Arrêt sur images – Mon compte':
            # Already logged in, check that the username is still the same
            userText = soup.find(text=re.compile(u'L’e-mail que vous utilisez pour @si est.*'))
            if userText and userText.next.string == username:
                return True
            else:
                print "Already logged in, but username does not match..."
        return False 

    def login(self, username = None, password = None):
        """Try to login using @username and @password.
        Return True if successful, False otherwise"""
        if username and password:
            response = getUrllib2ResponseObject(URLLOGIN)
            forms = ParseResponse(response, backwards_compat=False)
            response.close()
            # Set username & password in the signin form
            form = forms[2]
            form["username"] = username
            form["password"] = password
            # Click submit
            html = getHTML(form.click())
            soup = BeautifulSoup(html)
            if soup.title.string == u'Le Forum Arrêt Sur Images':
                # We are on the forum page - login successful
                return True
        return False


    class Programs:
        """Class used to get all programs and navigation items
        from an url""" 

        def __init__(self, url):
            self.html = getHTML(url)
            # Get the navigation items
            self.navItems = ArretSurImages().getNavItems(self.html)

        def getPrograms(self):
            """Return all programs in self.html"""
            # Couldn't parse properly the file using "'div', {'class':'bloc-contenu-8'}"
            # BeautifulSoup returns nothing in that class
            # So use 'contenu-descr-8 ' and find previous tag
            soup = BeautifulSoup(cleanHTML(self.html))
            for media in soup.findAll('div', {'class':'contenu-descr-8 '}):
                aTag = media.findPrevious('a')
                # Get link, title and thumb
                mediaLink = URLASI + aTag['href']
                mediaTitle = aTag['title'].encode('utf-8')
                mediaThumb = URLASI + aTag.find('img', attrs = {'src':re.compile('.+?\.[png|jpg]')})['src']
                yield {'url':mediaLink, 'Title':mediaTitle, 'Thumb':mediaThumb}

