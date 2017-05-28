import xbmcaddon

import sys, urllib, os
import re
import requests
import urllib2
from BeautifulSoup import BeautifulSoup

import xbmc, xbmcgui, xbmcplugin

ADDON = "plugin.image.dumpert"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGE_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
DATE = "2017-05-27"
VERSION = "1.0.0"

MODE_LATEST = 1

class dumpertSession:

    def LATEST(self, page=1):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
            ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

        self.image_list_page_url = "http://www.dumpert.nl/plaatjes/" + str(page) + "/"
        self.next_page_possible = True
        # Determine current page number and base_url
        # find last slash
        pos_of_last_slash = self.image_list_page_url.rfind('/')
        # remove last slash
        self.image_list_page_url = self.image_list_page_url[0: pos_of_last_slash]
        pos_of_last_slash = self.image_list_page_url.rfind('/')
        self.base_url = self.image_list_page_url[0: pos_of_last_slash + 1]
        self.current_page = self.image_list_page_url[pos_of_last_slash + 1:]
        self.current_page = int(self.current_page)
        # add last slash
        self.image_list_page_url = str(self.image_list_page_url) + "/"

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "self.base_url", str(self.base_url)), xbmc.LOGDEBUG)
        #
        # Init
        #
        titles_and_thumbnail_urls_index = 0

        #
        # Get HTML page
        #
        if SETTINGS.getSetting('nsfw') == 'true':
            html_source = requests.get(self.image_list_page_url, cookies={'nsfw': '1'}).text
        else:
            html_source = requests.get(self.image_list_page_url).text

        # Parse response
        soup = BeautifulSoup(html_source)

        # Find titles and thumnail-urls
        # img src="http://static.dumpert.nl/sq_thumbs/2245331_272bd4c3.jpg" alt="Turnlulz" title="Turnlulz" width="100" height="100" />
        # titles_and_thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://static.dumpert.nl/")} )
        titles_and_thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("thumb")})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "len(titles_and_thumbnail_urls)",
            str(len(titles_and_thumbnail_urls))),
                 xbmc.LOGDEBUG)

        # Find image page urls
        # <a href="http://www.dumpert.nl/mediabase/2245331/272bd4c3/turnlulz.html" class="dumpthumb" title="Turnlulz">
        image_page_urls = soup.findAll('a', attrs={'class': re.compile("dumpthumb")})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "len(image_page_urls)", str(len(image_page_urls))), xbmc.LOGDEBUG)

        # <a href="http://www.dumpert.nl/mediabase/7145289/32891f48/zo_is_f1_in_monaco.html" class="dumpthumb" title="Zo is F1 in Monaco">
        # 	<img src="http://media.dumpert.nl/sq_thumbs/7145289_32891f48.jpg" alt="Zo is F1 in Monaco" title="Zo is F1 in Monaco" width="100" height="100">
        # 	<span class="foto"></span>
        # 	<div class="details">
        # 		<h1>Zo is F1 in Monaco</h1>
        # 		<date>27 mei 2017  0:11</date>
        # 		<p class="stats">views: 75163 kudos: 899</p>
        # 		<p class="description">fap</p>
        # 	</div>
        # </a>
        for image_page_url in image_page_urls:
            pos_of_image_tag = str(image_page_url).find('class="foto"')
            if pos_of_image_tag >= 0:
                pass
            else:
                # skip image page url without a image
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "skipped image_page_url without image", str(image_page_url)),
                         xbmc.LOGDEBUG)
                titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1
                continue

            image_page_url = image_page_url['href']

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "image_page_url", str(image_page_url)), xbmc.LOGDEBUG)

            description = '...'
            # <a href="http://www.dumpert.nl/mediabase/6721593/46f416fa/stukje_snowboarden.html?thema=bikini" class="dumpthumb" title="Stukje snowboarden">
            #	<img src="http://media.dumpert.nl/sq_thumbs/6721593_46f416fa.jpg" alt="Stukje snowboarden" title="Stukje snowboarden" width="100" height="100" />
            #	<span class="image"></span>
            #	<div class="details">
            #		<h1>Stukje snowboarden</h1>
            #		<date>5 februari 2016 10:32</date>
            #		<p class="stats">views: 63687 kudos: 313</p>
            #		<p class="description">Fuck winterkleding </p>
            #	</div>
            # </a>
            try:
                description = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index].parent.find("p","description").string
                description = description.encode('utf-8')
            except:
                pass

            # Make title
            title = ''
            try:
                title = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index]['title']
                # convert from unicode to encoded text (don't use str() to do this)
                title = title.encode('utf-8')
                # <a href="http://www.dumpert.nl/mediabase/1958831/21e6267f/pixar_s_up_inspreken.html?thema=animatie" class="dumpthumb" title="Pixar's &quot;Up&quot; inspreken ">
            except KeyError:
                # http://www.dumpert.nl/mediabase/6532392/82471b66/dumpert_heeft_talent.html
                title = str(image_page_url)
                pos_last_slash = title.rfind('/')
                pos_last_dot = title.rfind('.')
                title = title[pos_last_slash + 1:pos_last_dot]
                title = title.capitalize()
            except UnicodeDecodeError:
                pass

            title = title.replace('-', ' ')
            title = title.replace('/', ' ')
            title = title.replace('_', ' ')

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                     xbmc.LOGDEBUG)

            if titles_and_thumbnail_urls_index >= len(titles_and_thumbnail_urls):
                thumbnail_url = ''
            else:
                thumbnail_url = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index]['src'].replace("sq_thumbs",
                                                                                                          "stills/large")
            mode = MODE_LATEST
            self.addImage(title, image_page_url, mode, thumbnail_url, title, tot=0, relatedTags="")

            titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1

        self.next_page_possible = True
        # Next page entry
        if self.next_page_possible:
            next_page = self.current_page + 1
            next_url = str(self.base_url) + str(next_page) + '/'

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "next_url", str(next_url)),
                     xbmc.LOGDEBUG)

            mode = MODE_LATEST
            self.addDir(LANGUAGE(30503), next_url, mode, os.path.join(IMAGE_PATH, 'next-page.png'), page=next_page, sort=0)

        return True

    def addImage(self, iId, url, mode, iconimage, title, tot=0, relatedTags=""):

        self.image_page_url = url

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "self.image_page_url", str(self.image_page_url)), xbmc.LOGDEBUG)

        #
        # Init
        #
        no_url_found = False
        unplayable_media_file = False
        have_valid_url = False

        html_source = ''
        try:
            if SETTINGS.getSetting('nsfw') == 'true':
                response = requests.get(self.image_page_url, cookies={'nsfw': '1'})
            else:
                response = requests.get(self.image_page_url)

            html_source = response.text
        except urllib2.HTTPError, error:
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGDEBUG)
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        soup = BeautifulSoup(html_source)
        image_url = ''

        # <div id="item1" class="foto" data-res="1080x1349">
        #   <a href="http://media.dumpert.nl/foto/ced3f11a_Sara_Underwood_Nude_Sexy3.jpg.jpg" target="_blank" title="klik voor groot (1080x1349)">
        #     <img class="player" src="http://media.dumpert.nl/foto/ced3f11a_Sara_Underwood_Nude_Sexy3.jpg.jpg">
        #   </a>
        # </div>
        image_urls = soup.findAll('div', attrs={'class': re.compile("foto")}, limit=1)
        if len(image_urls) == 0:
            no_url_found = True
        else:
            image_url = image_urls[0].img['src']
            have_valid_url = True

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "image_url", str(image_url)), xbmc.LOGDEBUG)

        # Show image...
        if have_valid_url:
            tot = 1
            iconimage = ""
            liz = xbmcgui.ListItem(title, iconImage="DefaultImage.png", thumbnailImage=iconimage)
            liz.setInfo(type="image", infoLabels={"Id": title})
            # Add refresh option to context menu
            liz.addContextMenuItems([('Refresh', 'Container.Refresh')])
            return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=image_url, listitem=liz, isFolder=False,
                                               totalItems=tot)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))
        return True

    def addDir(self, name, url, mode, iconimage, page=1, tot=0, sort=0, q="", ref=0):
        u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&page=" + str(
            page) + "&q=" + urllib.quote_plus(str(q))
        liz = xbmcgui.ListItem(name, 'test', iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo(type="image", infoLabels={"Title": name, "Label": str(sort)})
        contextMenu = []
        liz.addContextMenuItems(contextMenu)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True, totalItems=tot)

# copied from the google image plugin (thanks)
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
            if (len(splitparams)) == 1:
                param[splitparams[0]] = ""

    return param


def main():
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGDEBUG)

    # Get all parameters (current path etc.)
    params = get_params()
    url = None
    name = None
    mode = None
    page = 1

    try:
        url = urllib.unquote_plus(params["url"])
    except:
        pass
    try:
        name = urllib.unquote_plus(params["name"])
    except:
        pass
    try:
        mode = int(params["mode"])
    except:
        pass
    try:
        page = int(params["page"])
    except:
        pass
    try:
        query = urllib.unquote_plus(params["q"])
    except:
        pass

    update_dir = False
    success = True
    cache = True

    if mode==None or url==None or len(url)<1:
        success = dumpert.LATEST(1)
    elif mode == MODE_LATEST:
        success = dumpert.LATEST(page)

    xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=success, updateListing=update_dir, cacheToDisc=cache)

# Create the interface
dumpert = dumpertSession()

main()