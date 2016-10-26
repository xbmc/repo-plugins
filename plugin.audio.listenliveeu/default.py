"""
 A plugin to get radio links from listenlive.eu
"""

import sys, os, os.path, xbmcaddon
import xbmc, xbmcgui, xbmcplugin
import urllib, re, time
from HTMLParser import HTMLParser
from shutil import rmtree, copy
import traceback
from pprint import pprint

BASE_URL = 'http://www.listenlive.eu'
URL_INDEX = '/'.join( [BASE_URL, 'index.html'] )
URL_NEW = '/'.join( [BASE_URL, 'new.html'] )

ADDON = xbmcaddon.Addon()
ADDONNAME = ADDON.getAddonInfo('name')
ADDONVERSION = ADDON.getAddonInfo('version')
LANGUAGE = ADDON.getLocalizedString
DIR_SETTINGS = ADDON.getAddonInfo('profile').decode('utf-8')
DIR_SETTINGS = xbmc.translatePath(DIR_SETTINGS).decode('utf-8')
FILE_INDEX_PAGE = os.path.join(DIR_SETTINGS, 'index.html')
FILE_FAVS = os.path.join(DIR_SETTINGS, 'favorites.xml')

dialogProgress = xbmcgui.DialogProgress()
dialog = xbmcgui.Dialog()

def log(msg):
    if type(msg) not in (str, unicode):
        xbmc.log("[%s]: %s" % (ADDONNAME, type(msg)))
        pprint (msg)
    else:
        if type(msg) in (unicode,):
            msg = msg.encode('utf-8')
        xbmc.log("[%s]: %s" % (ADDONNAME, msg))

def errorOK(title="", msg=""):
    e = str( sys.exc_info()[ 1 ] )
    log(e)
    if not title:
        title = ADDONNAME + ' v' + ADDONVERSION
    if not msg:
        msg = "ERROR!"
    dialog.ok( title, msg, e )
    
#######################################################################################################################    
# write favs file
#######################################################################################################################    
def writeFavs():
    f = open(xbmc.translatePath(FILE_FAVS),"w")
    f.write('This is your favorites file.' + '\n')
    f.close()

#######################################################################################################################    
# add favorite
#######################################################################################################################    
def addFav(url):
    log("> addFav()")
    if url:
        try:
            favoritesRE=re.compile('(?i)name=(.+?)&url=(.+?)\n')
            favorites = favoritesRE.findall(url)
            for favorite in favorites:
                name = favorite[0]
                url = favorite[1]
            nameurl = 'name=%s&url=%s%s' % (name, url, '\n')
            doc = open(FILE_FAVS, "r+")
            text = doc.read().decode('utf-8')
            doc.close()
            if nameurl in text:
                dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30015), '', urllib.unquote_plus(name).decode('utf-8') )
            else:
                doc = open(FILE_FAVS, "a+")
                doc.write(nameurl)
                doc.close()                
                dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30007), '', urllib.unquote_plus(name).decode('utf-8') )
        except:
            dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30008), '', urllib.unquote_plus(name).decode('utf-8') )
    return True

#######################################################################################################################    
# remove favorite
#######################################################################################################################    
def remFav(url):
    log("> remFav()")
    if url:
        try:
            favoritesRE=re.compile('(?i)name=(.+?)&url=(.+?)\n')
            favorites = favoritesRE.findall(url)
            for favorite in favorites:
                name = favorite[0]
                url = favorite[1]
            nameurl = 'name=%s&url=%s%s' % (name, url, '\n')
            if dialog.yesno( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30009), '', urllib.unquote_plus(name).decode('utf-8') ):
                doc = open(FILE_FAVS, "rU")
                text = doc.read().decode('utf-8')
                doc.close()
                doc = open(FILE_FAVS, "w")
                doc.write(text.replace(nameurl, ''))
                doc.close()    
                xbmc.executebuiltin('Container.Refresh')
                dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30010), '', urllib.unquote_plus(name).decode('utf-8') )
                doc = open(FILE_FAVS).read().decode('utf-8')
                if doc == 'This is your favorites file.\n':
                    dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30016) )
        except:
            dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30011), '', urllib.unquote_plus(name).decode('utf-8') )
    return True

#######################################################################################################################    
# remove all favs
######################################################################################################
def remallFavs(url):
    log("> remallFavs()")
    if dialog.yesno(ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30012) ):
        try:
            doc = open(FILE_FAVS).read().decode('utf-8')
            if doc == 'This is your favorites file.\n':
                dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30017) )
            else:
                deleteFile(FILE_FAVS)
                dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30013) )
                xbmc.executebuiltin('Container.Refresh')
                writeFavs()
        except:
            dialog.ok( ADDONNAME + ' v' + ADDONVERSION, LANGUAGE(30014) )
    return True
        
#######################################################################################################################    
# get favorite
######################################################################################################
def getFavorites(url):
    log("> getFavorites()")
    doc = open(url).read()
    if doc:
        try:
            favoritesRE=re.compile('(?i)name=(.+?)&url=(.+?)\n')
            favorites = favoritesRE.findall(doc)
            for favorite in favorites:
                name = favorite[0]
                url = favorite[1]
                infolabels = {}
                addDirectoryItem(urllib.unquote_plus(name).decode('utf-8'), urllib.unquote_plus(url), 3, infoLabels=infolabels, isFolder=False)
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
        except:
            errorOK("getFavorites()")
    log("< getFavorites()")
    return True

#######################################################################################################################    
# get initial root category
#######################################################################################################################    
def getRootCats():
    log("> getRootCats()")    
    doc = open(FILE_FAVS).read().decode('utf-8')
    if doc == 'This is your favorites file.\n':
        items = ( (LANGUAGE(30000), "new"), (LANGUAGE(30001),"country"), (LANGUAGE(30002),"genre"), )
    else:
        items = ( (LANGUAGE(30000), "new"), (LANGUAGE(30003),"favorites"), (LANGUAGE(30001),"country"), (LANGUAGE(30002),"genre"), )

    for title, url in items:
        addDirectoryItem(title, url, 0)

    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    log("< getRootCats()")
    return True

#######################################################################################################################    
# Get category of by country or by genre
#######################################################################################################################    
def getCats(byCountry):
    log("> getCats() byCountry=%s" % byCountry)
    ok = False

    doc = getURL(URL_INDEX, FILE_INDEX_PAGE)
    if doc:
        log("getCats() parsing ...")
        try:
            # get section
            baseRE = '<p>Stations by $SECTION.*?</div>(.+?)</tr></tbody></table></div><br />'
            if byCountry:
                sectionRE = baseRE.replace('$SECTION','country')
            else:
                sectionRE = baseRE.replace('$SECTION','genre')
            #section = re.search(sectionRE, doc, re.IGNORECASE + re.MULTILINE + re.DOTALL).group(1)
            section = re.search('(?ims)' + sectionRE, doc).group(1)

            # parse info from section
            p=re.compile('<a href="(.+?)".*?>(.+?)</a', re.IGNORECASE)
            matches = p.findall(section)
            for page, name in matches:
                url = "/".join([BASE_URL,page])
                addDirectoryItem(name,url,1)

            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
            ok = True
        except:
            errorOK("getCats()")

    log("< getCats() ok=%s" % ok)
    return ok

######################################################################################################
def getStreams(url):
    log("> getStreams()")
    ok = False

    #doc = open('/'.join( [DIR_HOME, 'top40.html'] ) ).read()
    
    doc = getURL(url)
    if doc:
        try:
            log("parsing doc ...")
            doc=doc.replace('<br />','')
            # get all table rows, one staion per row - with possible multiple streams
            stationsRE=re.compile('(?ims)(<tr>.*?</tr>)')

            # url, name, loc, stream(s), genre
            #stationRE=re.compile('(?ims)<td><a href=".*?"><b>(.*?)</b>.*?<td>(.*?)</td>.*?alt=".*?".*?<td>(<a href=.*?</td>).*?(?:<td>(.*?)</td>|</tr>)')
            stationRE=re.compile('(?ims)<td.+?<a href=".*?"><b>(.*?)</b>.*?<td>(.*?)</td>.*?alt=".*?".*?<td>(<a href=.*?</td>).*?(?:<td>(.*?)</td>|</tr>)')

            #streamsRE=re.compile('(?i)href="(.*?)">(.*?)<')
            streamsRE=re.compile('(?i)href="([^"]+)">(\d+ +[^"]+|\d+[.]\d+ +[^"]+)</a>')

            # get all stations
            stations = stationsRE.findall(doc)
            #pprint (stations)
            genreExists = False
            for station in stations:
                #print station

                # get station details
                stationInfo = re.search(stationRE, station)
                if not stationInfo:
                    log("stationInfo re not matched - ignore station")
                    continue
                #print stationInfo.groups()

                # ensure we only use allowed stream type
                #type = stationInfo.group(3)
                #if type not in ('MP3','Windows Media'):                            # add allowed type here
                #    log("ignored stream type: " + type)
                #    continue
                
                name = stationInfo.group(1)
                loc = stationInfo.group(2)
                streamsData = stationInfo.group(3)
                genre = stationInfo.group(4)

                # parse station streams
                streams = streamsRE.findall(streamsData)
                
                for stream in streams:
                    streamURL = stream[0]
                    streamRate = stream[1]
                    if not streamRate.endswith('Kbps') or streamRate.endswith('kbps'):
                        log("ignored stream rate: " + streamRate)
                        continue
                    # further filter stream playlist types
                    #if streamURL.endswith('.m3u') or streamURL.endswith('.pls'):
                        #if not streamURL.endswith('ogg.m3u') and not streamURL.endswith('aac.m3u'):
                            # stream allowed, display it
                    infolabels = {}
                    label1 = "%s" % (name)
                    
                    if list_loc=='true':
                        label1 += " | %s" % (loc)

                    if genre:
                        if list_genre=='true':
                            label1 += " | %s" % (genre)
                        infolabels["Genre"] = genre
                        genreExists = True                # if any have genre then allow SORT_METHOD

                    if list_rate=='true':
                        label1 += " | %s" % (streamRate)
                        
                    infolabels["Title"] = HTMLParser().unescape(label1)
                    streamRate2= streamRate.replace('Kbps', '')
                    streamRate2= streamRate2.replace('kbps', '')
                    #print 'rate2: ' + streamRate2 + ' - ' + 'min_rate: ' + min_rate
                    if float(streamRate2) >= float(min_rate):
                        #print 'show it!'
                        addDirectoryItem(HTMLParser().unescape(label1), streamURL, 2, infoLabels=infolabels, isFolder=False)

            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
            if genreExists:
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
            ok = True
        except:
            errorOK("getStreams()")
    log("< getStreams() ok=%s" % ok)
    return ok

######################################################################################################
# fetch webpage or open filename if exists
######################################################################################################
def getURL(url, fn=''):
    """ read a doc from an url and save to file (if required) """
    
    try:
        doc = ''
        # load local file if exists
        if fn and os.path.isfile(fn):
            doc = open(fn).read()
            if not doc:
                deleteFile(fn)            # empty file, remove it
                log("Empty file removed: " + fn)
                doc = ''
            else:
                log("Loaded existing file: " + fn)

        if not doc:
            safe_url = url.replace( " ", "%20" )
            log('Downloading from url=%s' % safe_url)
            sock = urllib.urlopen( safe_url )
            doc = sock.read()
            if fn:
                fp = open(fn, "w")
                fp.write(doc)
                fp.close()
                log("File saved to " + fn)
            sock.close()

        if doc:
            return unicode(doc, 'utf-8', errors='ignore')
        else:
            return ''
    except:
        errorOK("getURL()")
        return None

######################################################################################################
# get redirect url for mms streams
######################################################################################################
def getRedirect(url):
    import requests
    url = url.replace('mms:', 'http:')
    response = requests.get(url, allow_redirects=False)
    try:
        redir = response.headers['Location']
    except:
        redir = ''
    return redir

######################################################################################################
def get_params():
    """ extract params from argv[2] to make a dict (key=value) """
    paramDict = {}
    try:
        if sys.argv[2]:
            paramPairs=sys.argv[2][1:].split( "&" )
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits))==2:
                    paramDict[paramSplits[0]] = paramSplits[1]
    except:
        errorOK()
    return paramDict

######################################################################################################
def addDirectoryItem(name, url, mode, label2='', infoType="Music", infoLabels = {}, isFolder=True):
    liz=xbmcgui.ListItem(name, label2)
    if not infoLabels:
        infoLabels = {"Title": name }
    liz.setInfo( infoType, infoLabels )
    
    v = "?name=%s&url=%s" % (urllib.quote_plus(name.encode('utf-8')), urllib.quote_plus(url.encode('utf-8')), )
    action1 = 'XBMC.RunPlugin(plugin://plugin.audio.listenliveeu/?add%s%s)' % (v, '\n')
    action2 = 'XBMC.RunPlugin(plugin://plugin.audio.listenliveeu/?remfav%s%s)' % (v, '\n')
    action3 = 'XBMC.RunPlugin(plugin://plugin.audio.listenliveeu/?removeall)'
    
    u = "%s?url=%s&mode=%s&name=%s" % (sys.argv[0], urllib.quote_plus(url), mode, urllib.quote_plus(name.encode('utf-8')), )

    if mode==2:
        try:
            liz.addContextMenuItems([(LANGUAGE(30004), action1), (LANGUAGE(30006), action3)])
            if url.startswith('mms'):
                liz.setProperty('IsPlayable', 'true')
            else:
                u = url
        except:
            errorOK("addDirectoryItem()")
        
    elif mode==3:
        try:
            liz.addContextMenuItems([(LANGUAGE(30005), action2), (LANGUAGE(30006), action3)])
            if url.startswith('mms'):
                liz.setProperty('IsPlayable', 'true')
            else:
                u = url
        except:
            errorOK("addDirectoryItem()")

    log("%s" % u)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)

######################################################################################################
def deleteFile(fn):
    try:
        os.remove(fn)
        log("File deleted: " + fn)
    except: pass
        
#######################################################################################################################    
# BEGIN !
#######################################################################################################################
try:
    __settings__ = xbmcaddon.Addon(id='plugin.audio.listenliveeu')
    LANGUAGE = __settings__.getLocalizedString
except:
    errorOK()


if not os.path.exists(DIR_SETTINGS):
    os.mkdir(DIR_SETTINGS)
if not os.path.exists(FILE_FAVS):
    writeFavs()

#######################################################################################################################    
# get settings
#######################################################################################################################

list_loc = __settings__.getSetting( "list_loc" )
list_genre = __settings__.getSetting( "list_genre" )
list_rate = __settings__.getSetting( "list_rate" )
min_rate = __settings__.getSetting( "min_rate" )

#######################################################################################################################
params=get_params()
url=urllib.unquote_plus(params.get("url", ""))
name=urllib.unquote_plus(params.get("name",""))
mode=int(params.get("mode","0"))
log("Mode: %s" % mode)
log("URL: %s" % url)
log("Name: %s" % name)

if "?add" in sys.argv[ 2 ] :
    ok = addFav(sys.argv[ 2 ])
    xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
elif "?remfav" in sys.argv[ 2 ] :
    ok = remFav(sys.argv[ 2 ])
    xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
elif "?removeall" in sys.argv[ 2 ] :
    ok = remallFavs(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)

if not "?add" in sys.argv[ 2 ] and not "?remfav" in sys.argv[ 2 ] and not "?removeall" in sys.argv[ 2 ]:
    if not sys.argv[ 2 ] or not url:
        # new start - cleanup old files
        deleteFile(FILE_INDEX_PAGE)

        ok = getRootCats()
        xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
    elif url == "new":
        ok = getStreams(URL_NEW)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
    elif url == "favorites":
        ok = getFavorites(FILE_FAVS)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
    elif url == "country":
        ok = getCats(True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
    elif url == "genre":
        ok = getCats(False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
    elif mode==1:
        ok = getStreams(url)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)
    elif mode==2 or mode==3:
        newurl = getRedirect(url)
        if newurl:
            item = xbmcgui.ListItem(path=newurl)
            succes = True
        else:
            item = xbmcgui.ListItem()
            succes = False
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), succes, listitem=item)
