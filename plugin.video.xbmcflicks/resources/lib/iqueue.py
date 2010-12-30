from Netflix import *
import getopt
import time 
import re
import xbmcplugin, xbmcaddon, xbmcgui, xbmc
import urllib, urllib2
import webbrowser
import os
from settings import *
from xinfo import *

# parameter keys
PARAMETER_KEY_MODE = "mode"
SUBMENU1a = "Movies"
SUBMENU1b = "TV Shows"
MODE1a = 11
MODE1b = 12

MY_USER = {
        'request': {
             'key': '',
             'secret': ''
        },
        'access': {
            'key': '',
            'secret': ''
        }
}

def __init__(self):
    self.data = []

def startBrowser(url):
	cmd="open -n '"+url+"'"
	print cmd
	os.system(cmd)
	

# AUTH 
def getAuth(netflix, verbose):
    print ".. getAuth called .."
    print "OSX Setting is set to: " + str(OSX)
    netflix.user = NetflixUser(MY_USER,netflix)
    print ".. user configured .."

    #handles all the initial auth with netflix
    if MY_USER['request']['key'] and not MY_USER['access']['key']:
        tok = netflix.user.getAccessToken( MY_USER['request'] )
        if(VERBOSE_USER_LOG):
            print "now put this key / secret in MY_USER.access so you don't have to re-authorize again:\n 'key': '%s',\n 'secret': '%s'\n" % (tok.key, tok.secret)
        MY_USER['access']['key'] = tok.key
        MY_USER['access']['secret'] = tok.secret
        saveUserInfo()
        dialog = xbmcgui.Dialog()
        dialog.ok("Settings completed", "You must restart the xbmcflicks plugin")
        print "Settings completed", "You must restart the xbmcflicks plugin"
        sys.exit(1)

    elif not MY_USER['access']['key']:
        (tok, url) = netflix.user.getRequestToken()
        if(VERBOSE_USER_LOG):
            print "Authorize user access here: %s" % url
            print "and then put this key / secret in MY_USER.request:\n 'key': '%s',\n 'secret': '%s'\n" % (tok.key, tok.secret)
            print "and run again."
        #open web page with urllib so customer can authorize the app

        if(OSX):
            startBrowser(url)
        else:
            webbrowser.open(url)
            
        #display click ok when finished adding xbmcflicks as authorized app for your netflix account
        dialog = xbmcgui.Dialog()
        ok = dialog.ok("After you have linked xbmcflick in netflix.", "Click OK after you finished the link in your browser window.")
        MY_USER['request']['key'] = tok.key
        MY_USER['request']['secret'] = tok.secret
        #now run the second part, getting the access token
        tok = netflix.user.getAccessToken( MY_USER['request'] )
        if(VERBOSE_USER_LOG):
            print "now put this key / secret in MY_USER.access so you don't have to re-authorize again:\n 'key': '%s',\n 'secret': '%s'\n" % (tok.key, tok.secret)
        MY_USER['access']['key'] = tok.key
        MY_USER['access']['secret'] = tok.secret
        #now save out the settings
        saveUserInfo()
        #exit script, user must restart
        dialog.ok("Settings completed", "You must restart XBMC")
        print "Settings completed", "You must restart XBMC"
        exit
        sys.exit(1)

    return netflix.user

def saveUserInfo():
    #create the file
    f = open(USERINFO_FOLDER + 'userinfo.txt','r+')
    setting ='requestKey=' + MY_USER['request']['key'] + '\n' + 'requestSecret=' + MY_USER['request']['secret'] + '\n' +'accessKey=' + MY_USER['access']['key']+ '\n' + 'accessSecret=' + MY_USER['access']['secret']
    f.write(setting)
    f.close()

# END AUTH
def checkplayercore():
    checkFile = XBMCPROFILE + 'playercorefactory.xml'
    havefile = os.path.isfile(checkFile)
    if(not havefile):
        #copy file data from addon folder
        fileWithData = ROOT_FOLDER + 'resources/playercorefactory.xml'
        if not os.path.exists('C:\Program Files (x86)'):
            fileWithData = ROOT_FOLDER + 'resources/playercorefactory32.xml'
        if not os.path.exists('C:\Program Files'):
            fileWithData = ROOT_FOLDER + 'resources/playercorefactoryOSX.xml'
        data = open(str(fileWithData),'r').read()
        f = open(checkFile,'r+')
        f.write(data)
        f.close()
    
def checkadvsettings():
    checkFile = XBMCPROFILE + 'advancedsettings.xml'
    havefile = os.path.isfile(checkFile)
    if(not havefile):
        #copy file from addon folder
        fileWithData = ROOT_FOLDER + 'resources/advancedsettings.xml'
        data = open(str(fileWithData),'r').read()
        f = open(checkFile,'r+')
        f.write(data)
        f.close()
    
def addLink(name,url,curX,rootID=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=curX.Poster)
    #if(xSummary):
    liz.setInfo( type="Video", infoLabels={ "Mpaa": curX.Mpaa, "TrackNumber": int(curX.Position), "Year": int(curX.Year), "OriginalTitle": curX.Title, "Title": curX.TitleShort, "Rating": float(curX.Rating)*2, "Duration": str(int(curX.Runtime)/60), "Director": curX.Directors, "Genre": curX.Genres, "CastAndRole": curX.Cast, "Plot": curX.Synop })

    commands = []

    argsRemove = str(curX.ID) + "delete"
    argsAdd = str(curX.ID) + "post"
    argsSimilar = str(curX.ID)
    if rootID:
        argsRemove = str(rootID) + "delete"
        argsAdd = str(rootID) + "post"
        argsSimilar = str(rootID)
    runnerRemove = "XBMC.RunScript(special://home/addons/plugin.video.xbmcflicks/resources/lib/modQueue.py, " + argsRemove + ")"
    runnerAdd = "XBMC.RunScript(special://home/addons/plugin.video.xbmcflicks/resources/lib/modQueue.py, " + argsAdd + ")"
    runnerSearch = "XBMC.RunScript(special://home/addons/plugin.video.xbmcflicks/resources/lib/modQueue.py, " + argsSimilar + ")"

    if(not curX.TvEpisode):
        commands.append(( 'Netflix: Add to Instant Queue', runnerAdd, ))
        commands.append(( 'Netflix: Remove From Instant Queue', runnerRemove, ))
        #commands.append(( 'Netflix: Find Similar', runnerSearch, ))
    else:
        commands.append(( 'Netflix: Add Entire Season to Instant Queue', runnerAdd, ))
        commands.append(( 'Netflix: Remove Entire Season From Instant Queue', runnerRemove, ))

    liz.addContextMenuItems( commands )
    whichHandler = sys.argv[1]
    ok=xbmcplugin.addDirectoryItem(handle=int(whichHandler),url=url,listitem=liz, isFolder=False)

    return ok

def addLinkDisc(name,url,curX,rootID=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=curX.Poster)
    #if(xSummary):
    liz.setInfo( type="Video", infoLabels={ "Mpaa": curX.Mpaa, "TrackNumber": int(curX.Position), "Year": int(curX.Year), "OriginalTitle": curX.Title, "Title": curX.TitleShort, "Rating": float(curX.Rating)*2, "Duration": str(int(curX.Runtime)/60), "Director": curX.Directors, "Genre": curX.Genres, "CastAndRole": curX.Cast, "Plot": curX.Synop })

    commands = []
    url = REAL_LINK_PATH + curX.ID + '_disc.html'
    argsRemove = str(curX.ID) + "discdelete"
    argsAdd = str(curX.ID) + "discpost"
    argsAddTop = str(curX.ID) + "disctoppost"
    
    argsSimilar = str(curX.ID)
    if rootID:
        argsRemove = str(rootID) + "discdelete"
        argsAdd = str(rootID) + "discpost"
        argsSimilar = str(rootID)
    runnerRemove = "XBMC.RunScript(special://home/addons/plugin.video.xbmcflicks/resources/lib/modQueue.py, " + argsRemove + ")"
    runnerAdd = "XBMC.RunScript(special://home/addons/plugin.video.xbmcflicks/resources/lib/modQueue.py, " + argsAdd + ")"
    runnerAddTop = "XBMC.RunScript(special://home/addons/plugin.video.xbmcflicks/resources/lib/modQueue.py, " + argsAddTop + ")"
    runnerSearch = "XBMC.RunScript(special://home/addons/plugin.video.xbmcflicks/resources/lib/modQueue.py, " + argsSimilar + ")"

    if(not curX.TvEpisode):
        commands.append(( 'Netflix: Add to Disc Queue', runnerAdd, ))
        commands.append(( 'Netflix: Remove From Disc Queue', runnerRemove, ))
        commands.append(( 'Netflix: Add to Top of Disc Queue', runnerAddTop, ))
    else:
        commands.append(( 'Netflix: Add Season to Disc Queue', runnerAdd, ))
        commands.append(( 'Netflix: Remove Season From Disc Queue', runnerRemove, ))
        commands.append(( 'Netflix: Add to Top of Disc Queue', runnerAddTop, ))

    liz.addContextMenuItems( commands )
    whichHandler = sys.argv[1]
    ok=xbmcplugin.addDirectoryItem(handle=int(whichHandler),url=url,listitem=liz, isFolder=False)

    return ok

def writeLinkFile(id, title):
    #check to see if we already have the file
    havefile = os.path.isfile(LINKS_FOLDER + id + '.html')
    if(not havefile):
        #create the file
        player = "WiPlayerCommunityAPI"
        if(useAltPlayer):
            player = "WiPlayer"
        redirect = "<!doctype html public \"-//W3C//DTD HTML 4.0 Transitional//EN\"><html><head><title>Requesting Video: " + title + "</title><meta http-equiv=\"REFRESH\" content=\"0;url=http://www.netflix.com/" + player + "?lnkctr=apiwn&nbb=y&devKey=gnexy7jajjtmspegrux7c3dj&movieid=" + id + "\"></head><body bgcolor=\"#FF0000\"> <p>Redirecting to Netflix in a moment ...</p></body></html>"
        f = open(LINKS_FOLDER + id + '.html','r+')
        f.write(redirect)
        f.close()

#writeDiscLinkFile
def writeDiscLinkFile(id, title, webURL):
    #check to see if we already have the file
    havefile = os.path.isfile(LINKS_FOLDER + id + '_disc.html')
    if(not havefile):
        #create the file
        player = "WiPlayerCommunityAPI"
        if(useAltPlayer):
            player = "WiPlayer"
        redirect = "<!doctype html public \"-//W3C//DTD HTML 4.0 Transitional//EN\"><html><head><title>Requesting Video: " + title + "</title><meta http-equiv=\"REFRESH\" content=\"0;url=" + webURL + "\"></head><body bgcolor=\"#0000cc\"> <p>Redirecting to Netflix in a moment ...</p></body></html>"
        f = open(LINKS_FOLDER + id + '_disc.html','r+')
        f.write(redirect)
        f.close()

def checkFormat(netflix, curX):
    strLinkUrl = "http://api.netflix.com/catalog/titles/movies/" + curX.ID
    try:
        movie = netflix.catalog.getTitle(strLinkUrl)
        disc = NetflixDisc(movie['catalog_title'],netflix)
    except:
        print "unable to get details of the format of the movie, returning empty object"
        return False
    formats = disc.getInfo('formats')
    strFormats = simplejson.dumps(formats,indent=4)
    if(VERBOSE_USER_LOG):
        print "formats json: " + strFormats
    matchFormat = re.search(r'"label": "instant"', strFormats)
    if matchFormat:
        return True
    else:
        return False

def getSummary(netflix, curX):
    #time.sleep(.11)
    strCastClean = ""
    strSynopsisCleaned = ""
    strDirectorsCleaned = ""
    strLinkUrl = "http://api.netflix.com/catalog/titles/movies/" + curX.ID
    #try to get movie from catalog
    movie = None
    disc = None
    
    try:
        movie = netflix.catalog.getTitle(strLinkUrl)
        disc = NetflixDisc(movie['catalog_title'],netflix)
    except:
        #unable to get details, return empty object
        return curX
    
    #try to get synop
    try:
        synopsis = disc.getInfo('synopsis')
        strSynopsis = simplejson.dumps(synopsis, indent=4)
        strSynopsisCleaned = strSynopsis
        #clean out all html tags
        for match in re.finditer(r"(?sm)(<[^>]+>)", strSynopsis):
            strSynopsisCleaned = strSynopsisCleaned.replace(match.group(1),"")
        #clean out actor names that follows the name of character in movie
        for match2 in re.finditer(r"(?sm)(\([^\)]+\))", strSynopsisCleaned):
            strSynopsisCleaned = strSynopsisCleaned.replace(match2.group(1),"")
        #strip out the text ""synopsis": " and "{}|" and then clean up
        strSynopsisCleaned = strSynopsisCleaned.replace("\"synopsis\": ", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("{", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("}", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("|", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("  ", " ")
        strSynopsisCleaned = strSynopsisCleaned.replace("\"", "")
        strSynopsisCleaned = strSynopsisCleaned.strip()
        if(DEBUG):
            print "Cleaned Synopsis: %s" % strSynopsisCleaned
    except:
        print "No Synop Data available for " + curX.Title
    curX.Synop = strSynopsisCleaned

    return curX

def availableTimeRemaining(expires):
    """Get seconds since epoch (UTC)."""
    curTime = int(time.time())
    try:
        result = str(time.strftime("%d %b %Y", time.localtime(int(expires))))
        #print result
        return result
    except:
        return ""

def getMovieDataFromFeed(curX, curQueueItem, bIsEpisode, netflix, instantAvail, intDisplayWhat=None):
    #if display what = 0, will only show instant queue items
    #if display what = 1, will only display movies
    #if display what = 2, will only display tv shows
    #if display what = 3, working with Movies in Disc Queue
    #if display what = 4, working with TvShows in Disc Queue
    #if display what = 5, working with Everything in Disc Queue
    #if the value is not set, everything is shown (instant queue items)

    showTvShow = True
    showMovies = True
    discQueue = False
    
    if intDisplayWhat:
        if (int(intDisplayWhat) == 0):
            discQueue = False
        if (int(intDisplayWhat) == 1):
            showTvShow = False
        if (int(intDisplayWhat) == 2):
            showMovies = False
        if (int(intDisplayWhat) == 3):
            discQueue = True
        if (int(intDisplayWhat) == 4):
            showTvShow = False
            discQueue = True
        if (int(intDisplayWhat) == 5):
            showMovies = False
            discQueue = True

    if(instantAvail):
        discQueue = False
    
    #if it's a tv show it should be a folder, not a listing
    if re.search(r"{(u'episode_short'.*?)}", curQueueItem, re.DOTALL | re.MULTILINE):
        curX.TvShow = True
    if re.search(r"u'name': u'Television'", curQueueItem, re.IGNORECASE):
        curX.TvShow = True
    
    if (curX.TvShow):
        if(not showTvShow):
            return curX
    else:
        if(not showMovies):
            return curX

    iRating = 10001    
    #mpaa
    if(DEBUG):
        print "-------------------------------------"
        print curQueueItem
    matchMpaa = re.search(r'[\'"]scheme[\'"]: u{0,1}[\'"]http://api.netflix.com/categories/mpaa_ratings[\'"],.*?[\'"]label[\'"]: u{0,1}[\'"](.*?)"', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchMpaa:
        curX.Mpaa = matchMpaa.group(1).strip()
    else:
        #matching by maturity_level
        match = re.search(r"maturity_level': (\d{1,4}),", curQueueItem, re.DOTALL | re.MULTILINE)
        if match:
            iRating = int(match.group(1).strip())
            curX.MaturityLevel = iRating
            if (iRating == 0):
                curX.Mpaa = "0 Rating"
            elif (iRating == 10):
                curX.Mpaa = "TV-Y"
            elif (iRating == 20):
                curX.Mpaa = "TV-Y7"
            elif (iRating == 40):
                curX.Mpaa = "G"
            elif (iRating == 50):
                curX.Mpaa = "TV-G" 
            elif (iRating == 60):
                curX.Mpaa = "PG"
            elif (iRating == 75):
                curX.Mpaa = "NR (Kids)"
            elif (iRating == 80):
                curX.Mpaa = "PG-13"
            elif (iRating == 90):
                curX.Mpaa = "TV-14"
            elif (iRating == 100):
                curX.Mpaa = "R"
            elif (iRating == 110):
                curX.Mpaa = "TV-MA"
            elif (iRating == 130):
                curX.Mpaa = "NR (Mature)"
            elif (iRating == 1000):
                curX.Mpaa = "UR (Mature)"
            else:
                curX.Mpaa = match.group(1)

    #check rating against max rating
    if (not int(iRating) <= int(MAX_RATING)):
        print "Item failed rating check, not adding.."
        return curX
    
    #genre
    matchGenre = re.search(r"genres': \[?{.*?u'name': u'(.*?)'}", curQueueItem, re.DOTALL | re.MULTILINE)
    if matchGenre:
        curX.Genres = matchGenre.group(1).strip()

    #year
    matchYear = re.search(r'[\'"]release_year[\'"]: u{0,1}[\'"](\d{4})[\'"]', curQueueItem)
    if matchYear:
        curX.Year = matchYear.group(1).strip()

    if(not int(curX.Year) >= int(YEAR_LIMITER)):
        return curX

    #title
    matchTitle = re.search(r'[\'"]title[\'"]: {.*?[\'"]regular[\'"]: u{0,1}[\'"](.*?)[\'"].*?},', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchTitle:
        curX.Title = matchTitle.group(1).strip()

    #position
    matchPosition = re.search(r'[\'"]position[\'"]: u{0,1}[\'"](\d{1,6})[\'"], ', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchPosition:
        curX.Position = matchPosition.group(1)

    #runtime
    matchRuntime = re.search(r'[\'"]runtime[\'"]: u{0,1}[\'"](\d{1,6})[\'"], ', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchRuntime:
        curX.Runtime = matchRuntime.group(1)
    else:
        matchRuntime2 = re.search(r"u'runtime': ([\d]*?)}", curQueueItem)
        if matchRuntime2:
            curX.Runtime = matchRuntime2.group(1)

    #Available Until (in seconds since EPOC)
    matchAvailUntil = re.search(r"available_until': (\d{8,15})", curQueueItem, re.DOTALL | re.MULTILINE)
    if matchAvailUntil:
        curX.AvailableUntil = matchAvailUntil.group(1)

    matchWebURL = re.search(r"u'web_page': u'(.*?)'", curQueueItem)
    if matchWebURL:
	curX.WebURL = matchWebURL.group(1)
                
    #shorttitle
    matchTitleShort = re.search('[\'"]title[\'"]: {.*?[\'"](title_)?short[\'"]: u{0,1}[\'"](.*?)[\'"].*?},', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchTitleShort:
        curX.TitleShort = matchTitleShort.group(2).strip()

    firstM = True
    #director
    for matchDir in re.finditer(r"directors': \[(.*?)\]", curQueueItem):
        firstM = True
        for matchDir2 in re.finditer(r"u'name': u'(.*?)',", str(matchDir.group(1))):
            if (firstM):
                curX.Directors = curX.Directors + str(matchDir2.groups(1))
                firstM = False
            else:
                curX.Directors = curX.Directors + str(matchDir2.groups(1)) + ", "
    curX.Directors = curX.Directors.replace("(", "")
    curX.Directors = curX.Directors.replace(")", "")
    curX.Directors = curX.Directors.replace("'", "")
    curX.Directors = curX.Directors.replace(",,", ",")
        
    #rating
    matchRating = re.search('[\'"]average_rating[\'"]: [\'"]?(.*?)\}?[\'"]?}?,', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchRating:
        curX.Rating = matchRating.group(1)
        curX.Rating = curX.Rating.replace("}", "")
        curX.Rating = curX.Rating.replace("]", "")
        curX.Rating = curX.Rating.strip()
   
    #id and fullid
    matchIds = re.search(r"u'web_page': u'http://.*?/(\d{1,15})'", curQueueItem, re.DOTALL | re.MULTILINE)
    if matchIds:
        curX.ID = matchIds.group(1).strip()
    else:
        match = re.search(r"u'\d{1,3}pix_w': u'http://.*?.nflximg.com/US/boxshots/(small|tiny|large|ghd|small_epx|ghd_epx|large_epx|88_epx|tiny_epx)/(\d{1,15}).jpg'", curQueueItem, re.DOTALL | re.MULTILINE)
        if match:
            curX.ID = match.group(2).strip()
        else:
            matchIds2 = re.search(r'id[\'"]: u{0,1}[\'"](?P<fullId>.*?/(?P<idNumber>\d{1,15}))[\'"].*?', curQueueItem, re.DOTALL | re.MULTILINE)
            if matchIds2:
                curX.FullId = matchIds2.group(1)
                curX.id = matchIds2.group(2)
            else:
                print "CRITICAL ERROR: Unable to parse ID of item. Stopping parse..."
                exit
    #synop
    match = re.search(r"u'synopsis': {.*?u'regular': u'(.*?)}", curQueueItem, re.DOTALL | re.MULTILINE)
    if match:
        curX.Synop = match.group(1)

    #cleanup synop
    try:
        strSynopsis = curX.Synop
        strSynopsisCleaned = strSynopsis
        #clean out all html tags
        for match in re.finditer(r"(?sm)(<[^>]+>)", strSynopsis):
            strSynopsisCleaned = strSynopsisCleaned.replace(match.group(1),"")
        for match in re.finditer(r"(&.*?;)", strSynopsis):
            strSynopsisCleaned = strSynopsisCleaned.replace(match.group(1),"")
        #clean out actor names that follows the name of character in movie
        for match2 in re.finditer(r"(?sm)(\([^\)]+\))", strSynopsisCleaned):
            strSynopsisCleaned = strSynopsisCleaned.replace(match2.group(1),"")
        #strip out the text ""synopsis": " and "{}|" and then clean up
        strSynopsisCleaned = strSynopsisCleaned.replace("\"synopsis\": ", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("{", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("}", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("|", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("  ", " ")
        strSynopsisCleaned = strSynopsisCleaned.replace("\"", "")
        strSynopsisCleaned = strSynopsisCleaned.replace("\\'", "'")
        strSynopsisCleaned = strSynopsisCleaned.strip()
        curX.Synop = strSynopsisCleaned
        #print "Cleaned Synopsis: %s" % strSynopsisCleaned
    except:
        print "No Synop Data available for " + curX.Title

    curX.Synop = "Available Until: " + availableTimeRemaining(curX.AvailableUntil) + "\n" + curX.Synop
    
    #Appending MPAA Rating to Title
    if(SHOW_RATING_IN_TITLE):
        curX.TitleShort = curX.TitleShort + " [" + curX.Mpaa + "]"

    #poster
    posterLoc = ""
    if(posterLoc == ""):
        posterLoc = "http://cdn-" + str(get_CurMirrorNum()) + ".nflximg.com/us/boxshots/" + POSTER_QUAL + "/" + curX.ID + ".jpg"
    curX.Poster = posterLoc
    
    curX.TitleShortLink = curX.ID
    curX.TitleShortLink.strip()

    #append year to shorttitle based on user pref
    if(APPEND_YEAR_TO_TITLE):
        curX.TitleShort = curX.TitleShort + " (" + curX.Year + ")"

    if (DEBUG):
        print "curMpaa: " + curX.Mpaa
        print "curPosition: " + curX.Position
        print "curYear: " + curX.Year
        print "curTitle: " + curX.Title
        print "curTitleShort: " + curX.TitleShort
        print "curRating: " + curX.Rating
        print "curRuntime: " + curX.Runtime
        print "curGenres: " + curX.Genres
        print "curID: " + curX.ID
        print "curPoster: " + curX.Poster
        print "curSynop: " + curX.Synop
        print "curDirector: " + curX.Directors
    if (VERBOSE_USER_LOG):
        print "curFullId: " + curX.FullId

    if (discQueue):
        addLinkDisc(curX.TitleShort,REAL_LINK_PATH + curX.TitleShortLink + '.html', curX)
        #write the link file for Disc items that will link to the webpage
        writeDiscLinkFile(curX.TitleShortLink, curX.Title, curX.WebURL)
        return curX
        
    if (instantAvail):
        #need to verify it's available for instant watching before adding
        matchIA = re.search(r"delivery_formats': {(.*?instant.*?)}", curQueueItem, re.DOTALL | re.MULTILINE)
        if matchIA:
            matched = re.search(r"instant", matchIA.group(1))
            if(not matched):
                print "Item Filtered Out, it's not viewable instantly: " + curX.Title
                return curX
            else:
                curX.IsInstantAvailable = True
        else:
            return curX
    if(not curX.TvShow):
        addLink(curX.TitleShort,REAL_LINK_PATH + curX.TitleShortLink + '.html', curX)
        #write the link file
        writeLinkFile(curX.TitleShortLink, curX.Title)
        return curX

    #if we are here, it's a tvshow, see if we should expand them automatically (user setting)
    if(not AUTO_EXPAND_EPISODES):
        addLink(curX.TitleShort,REAL_LINK_PATH + curX.TitleShortLink + '.html', curX)
        #write the link file
        writeLinkFile(curX.TitleShortLink, curX.Title)
        return curX

    matchAllEpData = re.search(r"(?sm){(u'episode_short'.*?)}", curQueueItem, re.DOTALL | re.MULTILINE)
    if matchAllEpData:
        data = matchAllEpData.group(1)
    else:
        data = ""
    
    #addDir(curX.TitleShort,'',999,curX.Poster,data)
      
    #if still processing, we want to auto-expand the episode lets add the folder, and then parse the episodes into that folder
    for matchAllEp in re.finditer(r"(?sm){(u'episode_short'.*?)}", curQueueItem):
        reobj = re.compile('u\'episode_short\': u[\'"](?P<shorttitle>.*?)[\'"], u\'sequence\': (?P<eNum>\\d{1,3}), u\'id\': u\'(?P<link>.*?)\', u\'title\': u\'(?P<title>.*)}', re.DOTALL)
        matchAllEpisodes = reobj.search(matchAllEp.group())
        if matchAllEpisodes:
            curXe = XInfo()
            curXe.Mpaa = curX.Mpaa
            curXe.Position = curX.Position
            curXe.Year = curX.Year
            curXe.Rating = curX.Rating
            curXe.Runtime = "0"
            curXe.Genres = curX.Genres
            curXe.Directors = curX
            curXe.FullId = ""
            curXe.Poster = curX.Poster
            curXe.Cast = curX.Cast

            curXe.Title = matchAllEpisodes.group("title")
            curXe.Synop = curXe.Title + "\n\n" + curX.Synop
            curXe.TvEpisodeEpisodeNum = matchAllEpisodes.group("eNum")
            if re.search(r"Episode", curQueueItem, re.DOTALL | re.MULTILINE):
                curXe.TitleShort = curX.TitleShort + " " + matchAllEpisodes.group("shorttitle")
            else:
                curXe.TitleShort = curX.TitleShort + " " + "Episode: " + curXe.TvEpisodeEpisodeNum + " " + matchAllEpisodes.group("shorttitle")
            curXe.TvShow = True
            curXe.TvShowLink = curX.TvShowLink
            curXe.TvShowSeasonID = curX.TvShowSeasonID
            curXe.TvShowSeriesID = curX.TvShowSeriesID
            curXe.TvEpisode = True
            curXe.TvEpisodeNetflixID = matchAllEpisodes.group("link")
            
            curXe.TvEpisodeEpisodeSeasonNum = 0
            curXe.IsInstantAvailable = curX.IsInstantAvailable
            curXe.MaturityLevel = curX.MaturityLevel
            curXe.AvailableUntil = curX.AvailableUntil
            curXe.TvEpisodeEpisodeNum = matchAllEpisodes.group("eNum")
            curXe.TvEpisodeEpisodeSeasonNum = matchAllEpisodes.group("title")

            matchAllEpisodesRealID = re.search(r"http://api.netflix.com/catalog/titles/programs/\d{1,15}/(?P<id>\d{1,15})", curXe.TvEpisodeNetflixID, re.DOTALL | re.MULTILINE)
            if matchAllEpisodesRealID:
                curXe.ID = matchAllEpisodesRealID.group("id").strip()
                curXe.TitleShortLink = curXe.ID
                curXe.TitleShortLink.strip()
                
                #add and write file
                addLink(curXe.TitleShort,REAL_LINK_PATH + curXe.TitleShortLink + '.html', curXe, curX.ID)
                writeLinkFile(curXe.TitleShortLink, curXe.Title)
            else:
                #don't add it
                print "not adding episode, couldn't parse id"

    #xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return curX

def addDir(name,url,mode,iconimage,data):
    whichHandler = sys.argv[1]

    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    #u= "mode=" + urllib.quote_plus(data)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(handle=int(whichHandler),url=u,listitem=liz,isFolder=True)
    return ok

def getUserDiscQueue(netflix,user,displayWhat):
    print "*** What's in the Disc Queue? ***"
    feeds = netflix.user.getDiscQueue(None,None,500)
    if (VERBOSE_USER_LOG):
        print feeds
  
    counter = 0
    reobj = re.compile(r"(?sm)(?P<main>('item': )((?!('item': )).)*)", re.DOTALL | re.MULTILINE)
    #real processing begins here
    for match in reobj.finditer(str(feeds)):
        curX = XInfo()
        curQueueItem = match.group(1)

        #now parse out each item
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflix, False,displayWhat)

def getUserAtHomeItems(netflix,user):
    print "*** What's Disc from the Queue are shipped or at the home? ***"
    feeds = netflix.user.getAtHomeList(None,None,500)
    if (VERBOSE_USER_LOG):
        print feeds
  
    counter = 0
    reobj = re.compile(r"(?sm)(?P<main>('item': )((?!('item': )).)*)", re.DOTALL | re.MULTILINE)
    #real processing begins here
    for match in reobj.finditer(str(feeds)):
        curX = XInfo()
        curQueueItem = match.group(1)

        #now parse out each item
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflix, False)


def getUserInstantQueue(netflix,user, displayWhat):
    print "*** What's in the Instant Queue? ***"
    #get user setting for max number to download
    feeds = netflix.user.getInstantQueue(None,None,MAX_INSTANTQUEUE_RETREVE)
    if (VERBOSE_USER_LOG):
        print feeds
    
    counter = 0
    reobj = re.compile(r"(?sm)(?P<main>('item': )((?!('item': )).)*)", re.DOTALL | re.MULTILINE)
    #real processing begins here
    for match in reobj.finditer(str(feeds)):
        curX = XInfo()
        curQueueItem = match.group(1)

        #now parse out each item
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflix, False,displayWhat)
  

	# match start: matchAllEpisodes.start()
	# match end (exclusive): matchAllEpisodes.end()
	# matched text: matchAllEpisodes.group()
        
##        matchIsTvShow = re.search(r'href": "(http://.*?/series/(\d{1,15})/seasons/(\d{1,15})/episodes)".*?title": "episodes"', curQueueItem, re.DOTALL | re.IGNORECASE | re.MULTILINE)
##        if(matchIsTvShow):
##            curX.TvShow = True
##            curX.TvShowSeriesID = matchIsTvShow.group(2).strip()
##            print curX.TvShowSeriesID
##            curX.TvShowSeasonID = matchIsTvShow.group(3).strip()
##            print curX.TvShowSeasonID
##            curX.TvShowLink = 'http://api.netflix.com/catalog/titles/series/'+ str(curX.TvShowSeriesID) + '/seasons/' + str(curX.TvShowSeasonID)
##            print curX.TvShowLink
##            if(AUTO_EXPAND_EPISODES):
##                epfeeds = netflix.user.getInstantQueueTvShowEpisodes(curX.TvShowSeriesID, curX.TvShowSeasonID)
##                epjFeeds = simplejson.dumps(epfeeds,indent=4)
##                if(VERBOSE_USER_LOG):
##                    print epjFeeds
##                for match in reobj.finditer(epjFeeds):
##                    curQueueItemTvE = match.group(1)
##                    curX.IsEpisode = True
##                    curX = getMovieDataFromFeed(curX, curQueueItemTvE, True, netflix, False)

def getUserRecommendedQueue(netflix,user):
    initApp()
    feeds = netflixClient.user.getRecommendedQueue(0,100)
    if(DEBUG):
        print simplejson.dumps(feeds,indent=4)
    counter = 0
    #parse each item in queue by looking for the category: [ string 
    reobj = re.compile(r"(?sm)(?P<main>('directors': )((?!('directors': )).)*)", re.DOTALL | re.MULTILINE)
    for match in reobj.finditer(str(feeds)):
        curX = XInfo()
        curQueueItem = match.group(1)
        if(DEBUG):
            print "current queue item from regex is: " + str(curQueueItem)
        #now parse out each item
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflixClient, True)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getUrlString(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    return data 

def parseRSSFeedItem(curQueueItem, curX):
    try:
        reobj = re.compile(r"<title>(.*?)</title>.*?<link>(.*?)</link>.*?<description>.*;{1}(.*?)</description>", re.DOTALL | re.MULTILINE)
        match = reobj.search(curQueueItem)
        if match:
            curX.Title = match.group(1)
            curX.TitleShort = match.group(1)
            curX.Synop = match.group(3)
            curX.WebURL = match.group(2)
            reobj = re.compile(r".*?/(\d{1,15})", re.DOTALL | re.MULTILINE)
            matchID = reobj.search(match.group(2))
            if matchID:
                curX.ID = matchID.group(1)
            curX.Poster = "http://cdn-8.nflximg.com/us/boxshots/" + POSTER_QUAL + "/" + curX.ID + ".jpg"
            
    except:
        print "error parsing data from RSS feed Item"
    return curX

def convertRSSFeed(tData, intLimit, DiscQueue=None):
    #parse feed to curX object
    curX = XInfo()
    intCount = 0
    for match in re.finditer(r"(?sm)<item>(.*?)</item>", tData):
        intCount = intCount + 1
        #print str(intCount)
        if(intCount > int(intLimit)):
            return
            
        curQueueItem = match.group(1)
        parseRSSFeedItem(curQueueItem, curX)

        if(curX.ID == ""):
            print "fatal error: unable to parse ID in string " + curQueueItem
            exit

        #add the link to the UI
        if(DiscQueue):
            addLinkDisc(curX.TitleShort,REAL_LINK_PATH + curX.ID + '_disc.html', curX)
            writeDiscLinkFile(curX.ID, curX.Title, curX.WebURL)
        else:
            addLink(curX.TitleShort,REAL_LINK_PATH + curX.ID + '.html', curX)            
            #write the link file
            writeLinkFile(curX.ID, curX.Title)

def getUserRentalHistory(netflix, user, strHistoryType, displayWhat=None):
    print "*** What's the rental history? ***"
    feeds = ""
    if(not strHistoryType):
        feeds = netflix.user.getRentalHistory(None,None,500)
    else:
        feeds = netflix.user.getRentalHistory(strHistoryType,None,500)
        
    if (VERBOSE_USER_LOG):
        print feeds
  
    counter = 0
    reobj = re.compile(r"(?sm)(?P<main>('item': )((?!('item': )).)*)", re.DOTALL | re.MULTILINE)
    #real processing begins here
    for match in reobj.finditer(str(feeds)):
        curX = XInfo()
        curQueueItem = match.group(1)
        #now parse out each item
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflix, False, displayWhat)

CUR_IMAGE_MIRROR_NUM = 0

def get_CurMirrorNum():
    global CUR_IMAGE_MIRROR_NUM
    if(CUR_IMAGE_MIRROR_NUM == 8):
        CUR_IMAGE_MIRROR_NUM
        CUR_IMAGE_MIRROR_NUM = 1
    else:
        CUR_IMAGE_MIRROR_NUM = int(CUR_IMAGE_MIRROR_NUM) + 1
    return CUR_IMAGE_MIRROR_NUM

def initApp():
    global APP_NAME
    global API_KEY
    global API_SECRET
    global CALLBACK
    global user
    global counter
    global DEBUG
    global VERBOSE_USER_LOG
    global AUTO_EXPAND_EPISODES
    global OSX
    global useAltPlayer
    global arg
    global netflixClient
    global pg
    global APPEND_YEAR_TO_TITLE
    global POSTER_QUAL
    global MAX_INSTANTQUEUE_RETREVE
    global MAX_RATING
    global SHOW_RATING_IN_TITLE
    global YEAR_LIMITER
    global CUR_IMAGE_MIRROR_NUM

    global ROOT_FOLDER
    global WORKING_FOLDER
    global LINKS_FOLDER
    global REAL_LINK_PATH
    global IMAGE_FOLDER
    global USERINFO_FOLDER
    global XBMCPROFILE
    
    arg = int(sys.argv[1])
    APP_NAME = 'xbmcflix'
    API_KEY = 'gnexy7jajjtmspegrux7c3dj'
    API_SECRET = '179530/200BkrsGGSgwP6446x4x22astmd5118'
    CALLBACK = ''
    counter = '0'
    #get user settings
    DEBUG = getUserSettingDebug(arg)
    VERBOSE_USER_LOG = getUserSettingVerboseUserInfo(arg)
    OSX = getUserSettingOSX(arg)
    AUTO_EXPAND_EPISODES = getUserSettingExpandEpisodes(arg)
    useAltPlayer = getUserSettingAltPlayer(arg)
    POSTER_QUAL = getUserSettingPosterQuality(arg)
    APPEND_YEAR_TO_TITLE = getUserSettingAppendYear(arg)
    
    MAX_INSTANTQUEUE_RETREVE = getUserSettingMaxIQRetreve(arg)
    MAX_RATING = getUserSettingRatingLimit(arg)
    SHOW_RATING_IN_TITLE = getUserSettingShowRatingInTitle(arg)
    YEAR_LIMITER = getUserSettingYearLimit(arg)

    #get addon info
    __settings__ = xbmcaddon.Addon(id='plugin.video.xbmcflicks')
    ROOT_FOLDER = 'special://home/addons/plugin.video.xbmcflicks/'
    IMAGE_FOLDER = ROOT_FOLDER + 'resources/'
    WORKING_FOLDER = __settings__.getAddonInfo("profile")
    LINKS_FOLDER = WORKING_FOLDER + 'links/'
    REAL_LINK_PATH = xbmc.translatePath(WORKING_FOLDER + 'links/')
    USERINFO_FOLDER = WORKING_FOLDER
    XBMCPROFILE = xbmc.translatePath('special://profile')
    if(DEBUG):
        print "root folder: " + ROOT_FOLDER
        print "working folder: " + WORKING_FOLDER
        print "real link path: " + REAL_LINK_PATH
        print "image folder: " + IMAGE_FOLDER
        print "userinfo folder: " + USERINFO_FOLDER

    #check playercorefactory and advancedsettings, create if missing
    checkplayercore()
    checkadvsettings()
    
    reobj = re.compile(r"200(.{10}).*?644(.*?)4x2(.).*?5118")
    match = reobj.search(API_SECRET)
    if match:
        result = match.group(1)
        API_SECRET = result

    #ensure we have a links folder in addon_data
    if not os.path.exists(LINKS_FOLDER):
        os.makedirs(LINKS_FOLDER)
    
    #get user info
    userInfoFileLoc = USERINFO_FOLDER + 'userinfo.txt'
    print "USER INFO FILE LOC: " + userInfoFileLoc
    havefile = os.path.isfile(userInfoFileLoc)
    if(not havefile):
        f = open(userInfoFileLoc,'r+')
        f.write("")
        f.close()

    userstring = open(str(userInfoFileLoc),'r').read()
        
    reobj = re.compile(r"requestKey=(.*)\nrequestSecret=(.*)\naccessKey=(.*)\naccessSecret=(.*)")
    match = reobj.search(userstring)
    if match:
        print "matched file contents, it is in the correct format"
        MY_USER['request']['key'] = match.group(1).strip()
        MY_USER['request']['secret'] = match.group(2).strip()
        MY_USER['access']['key'] = match.group(3).strip()
        MY_USER['access']['secret'] = match.group(4).strip()
        print "finished loading up user information from file"
    else:
        #no match, need to fire off the user auth from the start
        print "couldn't load user information from userinfo.properties file"
    #auth the user
    netflixClient = NetflixClient(APP_NAME, API_KEY, API_SECRET, CALLBACK, VERBOSE_USER_LOG)
    user = getAuth(netflixClient,VERBOSE_USER_LOG)
    if(not user):
        exit

def getInstantQueue(displayWhat=None):
    initApp()
    getUserInstantQueue(netflixClient,user, displayWhat)
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getRecommendedQueue():
    initApp()
    if(not user):
        exit
    getUserRecommendedQueue(netflixClient, user)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getNewToWatchInstant():
    initApp()
    if(not user):
        exit
    curUrl = "http://www.netflix.com/NewWatchInstantlyRSS"
    convertRSSFeed(getUrlString(curUrl), 500)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getNewToWatchInstantTopX():
    initApp()
    if(not user):
        exit    
    curUrl = "http://www.netflix.com/NewWatchInstantlyRSS"
    convertRSSFeed(getUrlString(curUrl), 25)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getTop25Feed(strArg):
    initApp()
    curUrl = "http://rss.netflix.com/Top25RSS?gid=" + str(strArg)
    convertRSSFeed(getUrlString(curUrl), 25)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getTop25FeedD(strArg):
    initApp()
    curUrl = "http://rss.netflix.com/Top25RSS?gid=" + str(strArg)
    convertRSSFeed(getUrlString(curUrl), 25, True)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def doSearch(strArg, strQueue, strInstantOnly=None):
    instantOnly = False
    strType = "3"
    if(strInstantOnly):
        instantOnly = True
        strType = "5"
    #title search
    print "looking for items that match " + str(strArg ) + " in " + str(strQueue)  + " instant only is set to: " + str(instantOnly)
    initApp()
    print "Instant set to: " + str(instantOnly)
    print "Queue set to: " + str(strQueue)
    print "Search String is: " + str(strQueue)
    if(not user):
        exit    
    feeds = netflixClient.user.searchTitles(strArg,strQueue,0,100)
    if(DEBUG):
        print simplejson.dumps(feeds,indent=4)
    counter = 0
    #parse each item in queue by looking for the category: [ string 
    reobj = re.compile(r"(?sm)(?P<main>('directors': )((?!('directors': )).)*)", re.DOTALL | re.MULTILINE)
    for match in reobj.finditer(str(feeds)):
        curX = XInfo()
        curQueueItem = match.group(1)
        if(DEBUG):
            print "current queue item from regex is: " + str(curQueueItem)
        #now parse out each item
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflixClient, instantOnly, strType)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getDVDQueue(displayWhat):
    initApp()
    getUserDiscQueue(netflixClient,user, displayWhat)
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def rhShipped():
    initApp()
    getUserRentalHistory(netflixClient,user, "shipped", "3")
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def rhReturned():
    initApp()
    getUserRentalHistory(netflixClient,user, "returned", "3")
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def rhWatched():
    initApp()
    getUserRentalHistory(netflixClient,user, "watched")
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getHomeList():
    initApp()
    getUserAtHomeItems(netflixClient,user)
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
