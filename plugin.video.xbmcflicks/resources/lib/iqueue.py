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
import simplejson

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
	cmd="open /Applications/Firefox.app '"+url+"'"
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
            print "browser open has completed"
            
        #display click ok when finished adding xbmcflicks as authorized app for your netflix account
        dialog = xbmcgui.Dialog()
        ok = dialog.ok("After you have linked xbmcflick in netflix.", "Click OK after you finished the link in your browser window.")
        print "The dialog was displayed, hopefully you read the text and waited until you authorized it before clicking ok."
        MY_USER['request']['key'] = tok.key
        if(VERBOSE_USER_LOG):
            print "user key set to: " + tok.key
        MY_USER['request']['secret'] = tok.secret
        if(VERBOSE_USER_LOG):
            print "user secret set to: " + tok.secret
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
    f = open(os.path.join(str(USERINFO_FOLDER), 'userinfo.txt'),'r+')
    setting ='requestKey=' + MY_USER['request']['key'] + '\n' + 'requestSecret=' + MY_USER['request']['secret'] + '\n' +'accessKey=' + MY_USER['access']['key']+ '\n' + 'accessSecret=' + MY_USER['access']['secret']
    f.write(setting)
    f.close()

# END AUTH
def checkplayercore():
    checkFile = os.path.join(str(XBMCPROFILE), 'playercorefactory.xml')
    havefile = os.path.isfile(checkFile)
    if(not havefile):
        #copy file data from addon folder
        fileWithData = os.path.join(str(RESOURCE_FOLDER), 'playercorefactory.xml')
        if not os.path.exists('C:\Program Files (x86)'):
            fileWithData = os.path.join(str(RESOURCE_FOLDER), 'playercorefactory32.xml')
        if not os.path.exists('C:\Program Files'):
            fileWithData = os.path.join(str(RESOURCE_FOLDER), 'playercorefactoryOSX.xml')
        data = open(str(fileWithData),'r').read()
        f = open(checkFile,'r+')
        f.write(data)
        f.close()
    
def checkadvsettings():
    checkFile = os.path.join(str(XBMCPROFILE), 'advancedsettings.xml')
    havefile = os.path.isfile(checkFile)
    if(not havefile):
        #copy file from addon folder
        fileWithData = os.path.join(str(RESOURCE_FOLDER), 'advancedsettings.xml')
        data = open(str(fileWithData),'r').read()
        f = open(checkFile,'r+')
        f.write(data)
        f.close()

def addDirectoryItem(curX, isFolder=True, parameters={}, thumbnail=None):
    ''' Add a list item to the XBMC UI.'''
    if thumbnail:
        li = xbmcgui.ListItem(curX.Title, thumbnailImage=thumbnail)
    else:
        li = xbmcgui.ListItem(curX.Title)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    li.setInfo( type="Video", infoLabels={ "Mpaa": curX.Mpaa, "TrackNumber": int(curX.Position), "Year": int(curX.Year), "OriginalTitle": curX.Title, "Title": curX.TitleShort, "Rating": float(curX.Rating)*2, "Duration": str(int(curX.Runtime)/60), "Director": curX.Directors, "Genre": curX.Genres, "CastAndRole": curX.Cast, "Plot": curX.Synop})
    commands = []
    modScripLoc = os.path.join(str(LIB_FOLDER), 'modQueue.py')   
    argsRemove = str(curX.ID) + "delete"
    argsAdd = str(curX.ID) + "post"
    argsSimilar = str(curX.ID)
    runnerRemove = "XBMC.RunScript(" + modScripLoc + ", " + argsRemove + ")"
    runnerAdd = "XBMC.RunScript(" + modScripLoc + ", " + argsAdd + ")"
    runnerSearch = "XBMC.RunScript(" + modScripLoc + ", " + argsSimilar + ")"

    argsRemoveD = str(curX.ID) + "discdelete"
    argsAddD = str(curX.ID) + "discpost"
    argsAddTopD = str(curX.ID) + "disctoppost"
    argsSimilarD = str(curX.ID)
    runnerRemoveD = "XBMC.RunScript(" + modScripLoc + ", " + argsRemoveD + ")"
    runnerAddD = "XBMC.RunScript(" + modScripLoc + ", " + argsAddD + ")"
    runnerAddTopD = "XBMC.RunScript(" + modScripLoc + ", " + argsAddTopD + ")"
    runnerSearchD = "XBMC.RunScript(" + modScripLoc + ", " + argsSimilarD + ")"

    if(not curX.nomenu):
        if(not curX.TvEpisode):
            commands.append(( 'Netflix: Add to Disc Queue', runnerAddD, ))
            commands.append(( 'Netflix: Remove From Disc Queue', runnerRemoveD, ))
            commands.append(( 'Netflix: Add to Top of Disc Queue', runnerAddTopD, ))
        else:
            commands.append(( 'Netflix: Add Season to Disc Queue', runnerAddD, ))
            commands.append(( 'Netflix: Remove Season From Disc Queue', runnerRemoveD, ))
            commands.append(( 'Netflix: Add to Top of Disc Queue', runnerAddTopD, ))

        if(not curX.TvEpisode):
            commands.append(( 'Netflix: Add to Instant Queue', runnerAdd, ))
            commands.append(( 'Netflix: Remove From Instant Queue', runnerRemove, ))
            #commands.append(( 'Netflix: Find Similar', runnerSearch, ))
        else:
            commands.append(( 'Netflix: Add Entire Season to Instant Queue', runnerAdd, ))
            commands.append(( 'Netflix: Remove Entire Season From Instant Queue', runnerRemove, ))

    li.addContextMenuItems( commands )
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url, listitem=li, isFolder=isFolder)

def addLink(name,url,curX,rootID=None):
    ok=True
    rFolder = str(ROOT_FOLDER)
    lFolder = str(LIB_FOLDER)
    commands = []

    modScripLoc = os.path.join(lFolder, 'modQueue.py')
    argsRemove = str(curX.ID) + "delete"
    argsAdd = str(curX.ID) + "post"
    argsSimilar = str(curX.ID)
    if rootID:
        argsRemove = str(rootID) + "delete"
        argsAdd = str(rootID) + "post"
        argsSimilar = str(rootID)
    runnerRemove = "XBMC.RunScript(" + modScripLoc + ", " + argsRemove + ")"
    runnerAdd = "XBMC.RunScript(" + modScripLoc + ", " + argsAdd + ")"
    runnerSearch = "XBMC.RunScript(" + modScripLoc + ", " + argsSimilar + ")"

    if(not curX.TvEpisode):
        commands.append(( 'Netflix: Add to Instant Queue', runnerAdd, ))
        commands.append(( 'Netflix: Remove From Instant Queue', runnerRemove, ))
        #commands.append(( 'Netflix: Find Similar', runnerSearch, ))
    else:
        commands.append(( 'Netflix: Add Entire Season to Instant Queue', runnerAdd, ))
        commands.append(( 'Netflix: Remove Entire Season From Instant Queue', runnerRemove, ))
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=curX.Poster)
    liz.setInfo( type="Video", infoLabels={ "Mpaa": str(curX.Mpaa), "TrackNumber": int(str(curX.Position)), "Year": int(str(curX.Year)), "OriginalTitle": str(curX.Title), "Title": str(curX.TitleShort), "Rating": float(curX.Rating)*2, "Duration": str(int(curX.Runtime)/60), "Director": str(curX.Directors), "Genre": str(curX.Genres), "CastAndRole": str(curX.Cast), "Plot": str(curX.Synop) })
    liz.addContextMenuItems( commands )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz, isFolder=False)

    return ok

def addLinkDisc(name,url,curX,rootID=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=curX.Poster)
    liz.setInfo( type="Video", infoLabels={ "Mpaa": str(curX.Mpaa), "TrackNumber": int(str(curX.Position)), "Year": int(str(curX.Year)), "OriginalTitle": str(curX.Title), "Title": str(curX.TitleShort), "Rating": float(curX.Rating)*2, "Duration": str(int(curX.Runtime)/60), "Director": str(curX.Directors), "Genre": str(curX.Genres), "CastAndRole": str(curX.Cast), "Plot": str(curX.Synop) })

    commands = []
    filename = curX.ID + '_disc.html'
    url = os.path.join(str(REAL_LINK_PATH), filename)

    modScripLoc = os.path.join(str(LIB_FOLDER), 'modQueue.py')
    
    argsRemoveD = str(curX.ID) + "discdelete"
    argsAddD = str(curX.ID) + "discpost"
    argsAddTopD = str(curX.ID) + "disctoppost"
    
    argsSimilarD = str(curX.ID)
    if rootID:
        argsRemoveD = str(rootID) + "discdelete"
        argsAddD = str(rootID) + "discpost"
        argsSimilarD = str(rootID)
    runnerRemoveD = "XBMC.RunScript(" + modScripLoc + ", " + argsRemoveD + ")"
    runnerAddD = "XBMC.RunScript(" + modScripLoc + ", " + argsAddD + ")"
    runnerAddTopD = "XBMC.RunScript(" + modScripLoc + ", " + argsAddTopD + ")"
    runnerSearchD = "XBMC.RunScript(" + modScripLoc + ", " + argsSimilarD + ")"

    if(not curX.TvEpisode):
        commands.append(( 'Netflix: Add to Disc Queue', runnerAddD, ))
        commands.append(( 'Netflix: Remove From Disc Queue', runnerRemoveD, ))
        commands.append(( 'Netflix: Add to Top of Disc Queue', runnerAddTopD, ))
    else:
        commands.append(( 'Netflix: Add Season to Disc Queue', runnerAddD, ))
        commands.append(( 'Netflix: Remove Season From Disc Queue', runnerRemoveD, ))
        commands.append(( 'Netflix: Add to Top of Disc Queue', runnerAddTopD, ))

    liz.addContextMenuItems( commands )
    whichHandler = sys.argv[1]
    ok=xbmcplugin.addDirectoryItem(handle=int(whichHandler),url=url,listitem=liz, isFolder=False)

    return ok

def writeLinkFile(id, title):
    #check to see if we already have the file
    filename = id + '.html'
    fileLoc = os.path.join(str(LINKS_FOLDER), str(filename))
    havefile = os.path.isfile(fileLoc)
    if(not havefile):
        #create the file
        player = "WiPlayerCommunityAPI"
        if(useAltPlayer):
            player = "WiPlayer"
        redirect = "<!doctype html public \"-//W3C//DTD HTML 4.0 Transitional//EN\"><html><head><title>Requesting Video: " + title + "</title><meta http-equiv=\"REFRESH\" content=\"0;url=http://www.netflix.com/" + player + "?lnkctr=apiwn&nbb=y&devKey=gnexy7jajjtmspegrux7c3dj&movieid=" + id + "\"></head><body bgcolor=\"#FF0000\"> <p>Redirecting to Netflix in a moment ...</p></body></html>"
        f = open(fileLoc,'r+')
        f.write(redirect)
        f.close()

#writeDiscLinkFile
def writeDiscLinkFile(id, title, webURL):
    #check to see if we already have the file
    filename = id + '_disc.html'
    fileLoc = os.path.join(str(LINKS_FOLDER), str(filename))
    havefile = os.path.isfile(fileLoc)
    if(not havefile):
        #create the file
        player = "WiPlayerCommunityAPI"
        if(useAltPlayer):
            player = "WiPlayer"
        redirect = "<!doctype html public \"-//W3C//DTD HTML 4.0 Transitional//EN\"><html><head><title>Requesting Video: " + title + "</title><meta http-equiv=\"REFRESH\" content=\"0;url=" + webURL + "\"></head><body bgcolor=\"#0000cc\"> <p>Redirecting to Netflix in a moment ...</p></body></html>"
        f = open(fileLoc,'r+')
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
##    if(DEBUG):
##        print "current time: " + str(curTime)
##        print "expires: " + str(expires)
    try:
        result = str(time.strftime("%d %b %Y", time.localtime(int(expires))))
##        if(DEBUG):
##            print "result of time conversion is" + str(result)
        return result
    except:
        try:
            expiresObj = re.search(r"(\d*)000", expires)
            if expiresObj:
                expires = expiresObj.group(1)
            result = str(time.strftime("%d %b %Y", time.localtime(int(expires))))
            if(DEBUG):
                print "result of time conversion is" + str(result)
            return result
        except:
            return ""

def checkIsAvailable(strStart, strEnd):
    startTime = 0
    endTime = 0
    curTime = int(time.time())
    print "current time is: " + str(curTime)
    startsObj = re.search(r"(\d*)000", strStart)
    if startsObj:
        startTime = startsObj.group(1)
##        print "start time of: " + str(startTime)
    else:
        return False
    expiresObj = re.search(r"(\d*)000", strEnd)
    if expiresObj:
        endTime = expiresObj.group(1)
##        print "end time of: " + str(endTime)
    else:
        return False
    if(int(startTime) <= int(curTime)):
##        print "start is prior to current time"
        if(int(endTime) >= int(curTime)):
##            print "end is greater then current time"
            return True
    return False

def getMovieDataFromFeed(curX, curQueueItem, bIsEpisode, netflix, instantAvail, intDisplayWhat, forceExpand=None):
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

    matchAvailObj = re.search(r'"NetflixCatalog.Model.InstantAvailability".*?}, "Available": (?P<iAvail>true|false|null), "AvailableFrom": .*?\((?P<availFrom>\d*)\).*?, "AvailableTo": ".*?\((?P<availUntil>\d*)\).*?"Runtime": (\d*), "Rating": .*?\}', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchAvailObj:
        curX.oData = True
        result = matchAvailObj.group(1)
        print "----------------------------------"
        print " matched formats for oData "
        print " iAvail: " + str(matchAvailObj.group(1).strip())
        curX.oData = True
        if(matchAvailObj.group(1).strip() == "true"):
            curX.iAvail = True
        if(matchAvailObj.group(1).strip() == "True"):
            curX.iAvail = True
        else:
            curX.iAvail = False
        curX.iAvailFrom = matchAvailObj.group("availFrom")
        curX.iAvailTil = matchAvailObj.group("availUntil")
        curX.iAvail = checkIsAvailable(curX.iAvailFrom, curX.iAvailTil)
        if(DEBUG):
            print "------------------"
            print "is avail: " + str(curX.iAvail) + " avail from: " + str(curX.iAvailFrom) + " until: " + str(curX.iAvailTil)

    #mpaa
    if(DEBUG):
        print "-------------------------------------"
        print curQueueItem
    matchMpaa = re.search(r'[\'"]scheme[\'"]: u{0,1}[\'"]http://api.netflix.com/categories/mpaa_ratings[\'"],.*?[\'"]label[\'"]: u{0,1}[\'"](.*?)"', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchMpaa:
        curX.Mpaa = matchMpaa.group(1).strip()
    else:
        #matching by maturity_level
        matchRating = re.search(r"maturity_level': (\d{1,4}),", curQueueItem, re.DOTALL | re.MULTILINE)
        if matchRating:
            iRating = int(matchRating.group(1).strip())
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
                curX.Mpaa = matchRating.group(1)
        else:
            matchRating2 = re.search(r'"Synopsis": "(.*?)", "AverageRating": (.{1,5}), "ReleaseYear": (\d{4}), "Url": ".*?", "Runtime": (\d{1,10}), "Rating": "(.*?)"', curQueueItem)
            if matchRating2:
                curX.Mpaa = matchRating2.group(5).strip()
            else:
                matchRating3 = re.search(r'"Runtime": (\d{1,10}), "Rating": "(.*?)"', curQueueItem)
                if matchRating3:
                    curX.Mpaa = matchRating3.group(2).strip()
            
            if curX.Mpaa == "TV-Y":
                iRating = 10
            elif curX.Mpaa == "TV-Y7":
                iRating = 20
            elif curX.Mpaa == "G":
                iRating = 40
            elif curX.Mpaa == "TV-G": 
                iRating = 50
            elif curX.Mpaa == "PG":
                iRating = 60
            elif curX.Mpaa == "NR (Kids)":
                iRating = 75
            elif curX.Mpaa == "PG-13":
                iRating = 80
            elif curX.Mpaa == "TV-14":
                iRating = 90
            elif curX.Mpaa == "R":
                iRating = 100
            elif curX.Mpaa == "TV-MA":
                iRating = 110
            elif curX.Mpaa == "NR (Mature)":
                iRating = 130
            elif curX.Mpaa == "UR (Mature)":
                iRating = 1000
            else:
                iRating = 1000
    #check rating against max rating
    if (not int(iRating) <= int(MAX_RATING)):
        print "iRating is cur item is: " + str(iRating) + " which has the MPAA value of " + str(curX.Mpaa)
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
    else:
        matchYear2 = re.search(r'"ReleaseYear": (\d{4})', curQueueItem, re.IGNORECASE)
        if matchYear2:
            curX.Year = matchYear2.group(1).strip()
    if(not int(curX.Year) >= int(YEAR_LIMITER)):
        print "couldn't parse year"
        #return curX



    
    #title
    matchTitle = re.search(r'[\'"]title[\'"]: {.*?[\'"]regular[\'"]: u{0,1}[\'"](.*?)[\'"].*?},', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchTitle:
        curX.Title = matchTitle.group(1).strip()
    else:
        matchTitle2 = re.search('"ShortName": "(.*?)"',curQueueItem, re.DOTALL | re.MULTILINE)
        if matchTitle2:
            curX.Title = matchTitle2.group(1).strip()
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
        else:
            matchRuntime3 = re.search(r'"NetflixCatalog.Model.InstantAvailability".*?}, "Available": (?P<iAvail>true|false|null), "AvailableFrom": (?P<iAvailFrom>.*?), "AvailableTo": ".*?\((?P<availUntil>\d*)\).*?"Runtime": (\d*), "Rating": .*?\}', curQueueItem, re.DOTALL | re.MULTILINE)
            if matchRuntime3:
                curX.Runtime = matchRuntime3.group(4)

    #Available Until (in seconds since EPOC)
    matchAvailUntil = re.search(r"available_until': (\d{8,15})", curQueueItem, re.DOTALL | re.MULTILINE)
    if matchAvailUntil:
        curX.AvailableUntil = matchAvailUntil.group(1)
    else:
        #"NetflixCatalog.Model.InstantAvailability".*?}, "Available": (?P<iAvail>true|false|null), "AvailableFrom": (?P<iAvailFrom>.*?), "AvailableTo": (?P<iAvailTil>.*?)
        matchAvailUntil = re.search(r'"NetflixCatalog.Model.InstantAvailability".*?}, "Available": (?P<iAvail>true|false|null), "AvailableFrom": (?P<iAvailFrom>.*?), "AvailableTo": ".*?\((?P<availUntil>\d*)\)', curQueueItem, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if matchAvailUntil:
            curX.AvailableUntil = matchAvailUntil.group(3)
            if(DEBUG):
                print "matched avail until date from oData source regex"
                print str(curX.AvailableUntil)

    matchWebURL = re.search(r"u'web_page': u'(.*?)'", curQueueItem)
    if matchWebURL:
        curX.WebURL = matchWebURL.group(1)
                
    #shorttitle
    matchTitleShort = re.search('[\'"]title[\'"]: {.*?[\'"](title_)?short[\'"]: u{0,1}[\'"](.*?)[\'"].*?},', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchTitleShort:
        curX.TitleShort = matchTitleShort.group(2).strip()
    else:
        matchTitleShort2 = re.search('"ShortName": "(.*?)"',curQueueItem, re.DOTALL | re.MULTILINE)
        if matchTitleShort2:
            curX.TitleShort = matchTitleShort2.group(1).strip()
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
    else:
        matchRating2 = re.search(r'"Synopsis": "(.*?)", "AverageRating": (.{1,5}), "ReleaseYear": (\d{4}),', curQueueItem)
        if matchRating2:
            curX.Rating = matchRating2.group(2)
            curX.Rating = curX.Rating.replace("}", "")
            curX.Rating = curX.Rating.replace("]", "")
            curX.Rating = curX.Rating.strip()
    #print "attempting to get id next"   
    #id and fullid
    matchIds = re.search(r"u'web_page': u'http://.*?/(\d{1,15})'", curQueueItem, re.DOTALL | re.MULTILINE)
    if matchIds:
        curX.ID = matchIds.group(1).strip()
        #print "id regex: matched matchIds"
    else:
        #print "didnt' match matchIds"
        match = re.search(r"u'\d{1,3}pix_w': u'http://.*?.nflximg.com/US/boxshots/(small|tiny|large|ghd|small_epx|ghd_epx|large_epx|88_epx|tiny_epx)/(\d{1,15}).jpg'", curQueueItem, re.DOTALL | re.MULTILINE)
        if match:
            #print "id regex: matched match"
            curX.ID = match.group(2).strip()
        else:
            #print "didn't match match"
            matchIds2 = re.search(r'id[\'"]: u{0,1}[\'"](?P<fullId>.*?/(?P<idNumber>\d{1,15}))[\'"].*?', curQueueItem, re.DOTALL | re.MULTILINE)
            if matchIds2:
                #print "id regex: matched matchIds2"
                curX.FullId = matchIds2.group(1)
                curX.ID = matchIds2.group(2)
            else:
                #print "didn't match matchIds2"
                matchIds3 = re.search(r'"media_src": "http://.*?.nflximg.com/us/boxshots/(small|tiny|large|ghd|small_epx|ghd_epx|large_epx|88_epx|tiny_epx)/(\d{1,15}).jpg"', curQueueItem, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                if matchIds3:
                    #print "id regex: matched matchIds3"
                    curX.FullId = matchIds3.group(1)
                    curX.ID = matchIds3.group(2)
                else:
                    matchIds4 = re.search(r'"type": "NetflixCatalog.Model.BoxArt".*?}, ".*Url": "http://.*?.nflximg.com/us/boxshots/(small|tiny|large|ghd|small_epx|ghd_epx|large_epx|88_epx|tiny_epx)/(\d{1,15}).jpg"', curQueueItem, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                    if matchIds4:
                        #print "id regex: matched matchIds3"
                        curX.FullId = matchIds4.group(1)
                        curX.ID = matchIds4.group(2)
                    else:
                        print "CRITICAL ERROR: Unable to parse ID of item. Stopping parse..."
                        return curX
    #print "got id of : " + curX.ID
    #show info
    curX.TvShowSeriesID = curX.ID
    matchShowData = re.search(r"http://api.netflix.*?/catalog/titles/series/(\d*)/seasons/(\d*)", curQueueItem, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    if (matchShowData):
        curX.TvShow = True
        curX.TvShowSeriesID = matchShowData.group(1).strip()
        curX.TvShowSeasonID = matchShowData.group(2).strip()

    #synop
    match = re.search(r"u'synopsis': {.*?u'regular': u'(.*?)}", curQueueItem, re.DOTALL | re.MULTILINE)
    if match:
        curX.Synop = match.group(1)
    else:
        matchSynop = re.search(r'"Synopsis": "(.*?)", "AverageRating": (.{1,5}), "ReleaseYear": (\d{4}),', curQueueItem, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if matchSynop:
            curX.Synop = matchSynop.group(1)
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
        addLinkDisc(curX.TitleShort,os.path.join(str(REAL_LINK_PATH), str(curX.TitleShortLink + '.html')), curX)
        #write the link file for Disc items that will link to the webpage
        writeDiscLinkFile(curX.TitleShortLink, curX.Title, curX.WebURL)
        return curX
        
    #see if we are filtering for Instant Only Items
    if (instantAvail):
        #see if the source is odata, if so, ensure iAvail is set to true (return on fail)
        if(curX.oData):
            if(not curX.iAvail):
                return curX
            else:
                curX.IsInstantAvailable = True
        else:
            #api data will return a string the following regex will parse
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
        ciName = str(curX.TitleShortLink + '.html')
        ciPath = str(REAL_LINK_PATH)
        ciFullPath = os.path.join(ciPath, ciName )
        addLink(curX.TitleShort,ciFullPath, curX)
        #write the link file
        writeLinkFile(curX.TitleShortLink, curX.Title)
        return curX

    #if we are here, it's a tvshow, see if we should expand them automatically (user setting)
    if(not forceExpand):
        if(not AUTO_EXPAND_EPISODES):
            #it's a tvshow and we are not autoexpanding the episodes, we want to add the item as a folder with it's list of episodes
            boolDiscQueue = False
            if(discQueue):
                boolDiscQueue = True
            addDirectoryItem(curX, parameters={ PARAMETER_KEY_MODE:"tvExpand" + "shId" + curX.TvShowSeriesID + "seId" + curX.TvShowSeasonID + str(boolDiscQueue) }, isFolder=True, thumbnail=curX.Poster)

            #add the link to UI
            #addLink(curX.TitleShort,os.path.join(str(REAL_LINK_PATH), str(curX.TitleShortLink + '.html')), curX)
            #write the link file
            #writeLinkFile(curX.TitleShortLink, curX.Title)
            return curX
        
    matchAllEpData = re.search(r'(?sm){(u{0,1}[\'"]episode_short[\'"].*?)}', curQueueItem, re.DOTALL | re.MULTILINE)
    if matchAllEpData:
        data = matchAllEpData.group(1)
    else:
        data = ""

    foundMatch = False
    #if still processing, we want to auto-expand the episode lets add the folder, and then parse the episodes into that folder
    for matchAllEp in re.finditer('(?sm)(u{0,1}[\'"]episode_short[\'"].*?)}', curQueueItem):
        foundMatch = True
        curXe = XInfo()
        curXe.Mpaa = curX.Mpaa
        curXe.Position = curX.Position
        curXe.Year = curX.Year
        curXe.Rating = curX.Rating
        curXe.Runtime = "0"
        curXe.Genres = curX.Genres
        curXe.Directors = curX.Directors
        curXe.FullId = ""
        curXe.Poster = curX.Poster
        curXe.Cast = curX.Cast

        matchTitle = re.search('(?sm)u{0,1}[\'"]title[\'"]: u{0,1}[\'"](?P<title>.*?)[\'"],', matchAllEp.group())
        if matchTitle:
            curXe.Title = str(matchTitle.group("title"))
	
        curXe.Synop = curXe.Title + "\n\n" + curX.Synop
        
        matchEpNum = re.search('(?sm)u{0,1}[\'"]sequence[\'"]: u{0,1}(?P<episodeNum>\\d{1,3})', matchAllEp.group())
        if matchEpNum:
            curXe.TvEpisodeEpisodeNum = str(matchEpNum.group("episodeNum"))
        
        matchShortTitle = re.search('(?sm)u{0,1}[\'"]episode_short[\'"]: u{0,1}[\'"](?P<shorttitle>.*?)[\'"],', matchAllEp.group())
        if matchShortTitle:
            shortTitleString = str(matchShortTitle.group("shorttitle"))
            
        if re.search(r"Episode", curQueueItem, re.DOTALL | re.MULTILINE):
            if(not forceExpand):
                curXe.TitleShort = curX.TitleShort + " " + shortTitleString
            else:
                curXe.TitleShort = shortTitleString
        else:
            if(not forceExpand):
                curXe.TitleShort = curX.TitleShort + " " + "Episode: " + curXe.TvEpisodeEpisodeNum + " " + shortTitleString
            else:
                curXe.TitleShort = "Episode: " + curXe.TvEpisodeEpisodeNum + " - " + shortTitleString

        curXe.TvShow = True
        curXe.TvShowLink = curX.TvShowLink
        curXe.TvShowSeasonID = curX.TvShowSeasonID
        curXe.TvShowSeriesID = curX.TvShowSeriesID
        curXe.TvEpisode = True
        
        matchNetflixID = re.search('(?sm)u{0,1}[\'"]id[\'"]: u{0,1}[\'"](?P<mgid>.*?)[\'"],', matchAllEp.group())
        if matchNetflixID:
            curXe.TvEpisodeNetflixID = str(matchNetflixID.group("mgid"))
            
        curXe.TvEpisodeEpisodeSeasonNum = 0
        curXe.IsInstantAvailable = curX.IsInstantAvailable
        curXe.MaturityLevel = curX.MaturityLevel
        curXe.AvailableUntil = curX.AvailableUntil
        #curXe.TvEpisodeEpisodeNum = matchAllEpisodes.group("eNum")
        #curXe.TvEpisodeEpisodeSeasonNum = matchAllEpisodes.group("title")

        matchAllEpisodesRealID = re.search(r"http://api.netflix.com/catalog/titles/programs/\d{1,15}/(?P<id>\d{1,15})", curXe.TvEpisodeNetflixID, re.DOTALL | re.MULTILINE)
        if matchAllEpisodesRealID:
            curXe.ID = matchAllEpisodesRealID.group("id").strip()
            curXe.TitleShortLink = curXe.ID
            curXe.TitleShortLink.strip()
            #add and write file
            ciName2 = str(curXe.TitleShortLink + '.html')
            ciPath2 = str(REAL_LINK_PATH)
            ciFullPath2 = os.path.join(ciPath2, ciName2 )
            addLink(curXe.TitleShort, ciFullPath2, curXe, curX.ID)
            writeLinkFile(curXe.TitleShortLink, curXe.Title)
        else:
            #don't add it
            print "not adding episode, couldn't parse id"
    
    if (not foundMatch):
        #this is to cover those tv shows that are just a single episode
        ciName = str(curX.TitleShortLink + '.html')
        ciPath = str(REAL_LINK_PATH)
        ciFullPath = os.path.join(ciPath, ciName )
        addLink(curX.TitleShort,ciFullPath, curX)
        #write the link file
        writeLinkFile(curX.TitleShortLink, curX.Title)

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
    feeds = netflix.user.getDiscQueue(None,None,500,None,IN_CANADA)
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
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflix, False, False)


def getUserInstantQueue(netflix,user, displayWhat):
    print "*** What's in the Instant Queue? ***"
    #get user setting for max number to download
    feeds = netflix.user.getInstantQueue(None,None,MAX_INSTANTQUEUE_RETREVE,None,IN_CANADA)
    print "Max value: " + str(MAX_INSTANTQUEUE_RETREVE)
    print "In CA: " + str(IN_CANADA)
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
    feeds = netflixClient.user.getRecommendedQueue(0,100,None,IN_CANADA)
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
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflixClient, True, False)
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
            curX.Poster = "http://cdn-8.nflximg.com/us/boxshots/" + str(POSTER_QUAL) + "/" + curX.ID + ".jpg"
            
    except:
        print "error parsing data from RSS feed Item"
    return curX


def parseFeedburnerItem(curQueueItem, curX):
    try:
        reobjCurItem = re.compile(r'<strong>(?P<title>.*?)</strong><br/><a href="http://www\.netflix\.ca/[^"]*"><img src="(?P<posterPrefix>http://cdn-0\.nflximg\.com/en_CA/boxshots/)small/\d{2,14}\.jpg" /></a><br />(?P<summary>.*?)<a href="http://www\.netflix\.ca/[^"]*">More details</a> / <a href="http://www\.netflix\.ca/WiPlayer\?movieid=(?P<id>\d{2,14})">Watch now</a>', re.DOTALL | re.MULTILINE)
        matchCurItem = reobjCurItem.search(curQueueItem)
        if matchCurItem:
            curX.Title = matchCurItem.group(1)
            curX.TitleShort = matchCurItem.group(1)
            curX.Synop = matchCurItem.group(3)
            curX.WebURL = matchCurItem.group(4)
            curX.ID = matchCurItem.group(5)
            curX.Poster = matchCurItem.group(2) + str(POSTER_QUAL) + "/" + curX.ID + ".jpg"
    except:
        print "error parsing data from Feedburner RSS feed Item"        
    return curX

def convertFeedburnerFeed(tData, intLimit, DiscQueue=None):
    #parse feed to curX object
    curX = XInfo()
    intCount = 0
    for match in re.finditer(r"(?sm)<li.*?>(.*?)</li>", tData):
        for matchItem in re.finditer(r"(?sm)<p>(.*?)</p>", match.group(1)):
            intCount = intCount + 1
            if(intCount > int(intLimit)):
                return
            curQueueItem = match.group(1)
            parseFeedburnerItem(curQueueItem, curX)
            
            if(curX.ID == ""):
                print "fatal error: unable to parse ID in string " + curQueueItem
            else:
                #add the link to the UI
                if(DiscQueue):
                    addLinkDisc(curX.TitleShort,os.path.join(str(REAL_LINK_PATH), str(curX.ID + '_disc.html')), curX)
                    writeDiscLinkFile(curX.ID, curX.Title, curX.WebURL)
                else:
                    addLink(curX.TitleShort,os.path.join(str(REAL_LINK_PATH), str(curX.ID + '.html')), curX)            
                    #write the link file
                    writeLinkFile(curX.ID, curX.Title) 

def convertRSSFeed(tData, intLimit, DiscQueue=None, strArg=None):
    #strArg (0 = all, 1 = movies, 2 = tv)
    incMovie = False
    incTV = False
    
    if(strArg):
        if(str(strArg) == "0"):
            incMovie = True
            incTV = True
            if(DEBUG):
                print "No filter"
        elif(str(strArg) == "1"):
            incMovie = True
            incTV = False
            if(DEBUG):
                print "Filtering for Movies"
        elif(str(strArg) == "2"):
            incMovie = False
            incTV = True
            if(DEBUG):
                print "Filtering for TV"
    else:
        incMovie = True
        incTV = True
            
    #parse feed to curX object
    curX = XInfo()
    intCount = 0
    for match in re.finditer(r"(?sm)<item>(.*?)</item>", tData):
        curQueueItem = match.group(1)
        parseRSSFeedItem(curQueueItem, curX)

        if(curX.ID == ""):
            print "fatal error: unable to parse ID in string " + curQueueItem
            exit

        isMovie = False
        isTV = False
        skip = True
        if re.search(r"(Season|Vol\.|: Chapter)", curX.Title, re.DOTALL | re.MULTILINE):
            isTV = True
        else:
            isMovie = True
            
        if (isMovie & incMovie):
            intCount = intCount + 1
            if (DEBUG):
                print "triggered count on movies limiter:" + str(intCount) + " of " + str(intLimit)
            skip = False
        elif (isTV & incTV):
            intCount = intCount + 1
            if (DEBUG):
                print "triggered count on tv limiter:" + str(intCount) + " of " + str(intLimit)
            skip = False
        #print str(intCount)
        if(intCount > int(intLimit)):
            return

        if(not skip):
        #add the link to the UI
            if(DiscQueue):
                addLinkDisc(curX.TitleShort,os.path.join(str(REAL_LINK_PATH), str(curX.ID + '_disc.html')), curX)
                writeDiscLinkFile(curX.ID, curX.Title, curX.WebURL)
            else:
                addLink(curX.TitleShort,os.path.join(str(REAL_LINK_PATH), str(curX.ID + '.html')), curX)            
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
    global IN_CANADA
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
    global RESOURCE_FOLDER
    global LIB_FOLDER
    global USERINFO_FOLDER
    global XBMCPROFILE

    #genre settings
    global SGACTION
    global SGANIME
    global SGBLURAY
    global SGCHILDREN
    global SGCLASSICS
    global SGCOMEDY
    global SGDOCUMENTARY
    global SGDRAMA
    global SGFAITH
    global SGFOREIGN
    global SGGAY
    global SGHORROR
    global SGINDIE
    global SGMUSIC
    global SGROMANCE
    global SGSCIFI
    global SGSPECIALINTEREST
    global SGSPORTS
    global SGTV
    global SGTHRILLERS
    
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
    IN_CANADA = getUserSettingCaUser(arg)
    AUTO_EXPAND_EPISODES = getUserSettingExpandEpisodes(arg)
    useAltPlayer = getUserSettingAltPlayer(arg)
    POSTER_QUAL = getUserSettingPosterQuality(arg)
    APPEND_YEAR_TO_TITLE = getUserSettingAppendYear(arg)
    
    MAX_INSTANTQUEUE_RETREVE = getUserSettingMaxIQRetreve(arg)
    MAX_RATING = getUserSettingRatingLimit(arg)
    SHOW_RATING_IN_TITLE = getUserSettingShowRatingInTitle(arg)
    YEAR_LIMITER = getUserSettingYearLimit(arg)

    SGACTION = getUserSettingGenreDisplay(arg, "sgAction")
    SGANIME = getUserSettingGenreDisplay(arg, "sgAnime")
    SGBLURAY = getUserSettingGenreDisplay(arg, "sgBluray")
    SGCHILDREN = getUserSettingGenreDisplay(arg, "sgChildren")
    SGCLASSICS = getUserSettingGenreDisplay(arg, "sgClassics")
    SGCOMEDY = getUserSettingGenreDisplay(arg, "sgComedy")
    SGDOCUMENTARY = getUserSettingGenreDisplay(arg, "sgDocumentary")
    SGDRAMA = getUserSettingGenreDisplay(arg, "sgDrama")
    SGFAITH = getUserSettingGenreDisplay(arg, "sgFaith")
    SGFOREIGN = getUserSettingGenreDisplay(arg, "sgForeign")
    SGGAY = getUserSettingGenreDisplay(arg, "sgGay")
    SGHORROR = getUserSettingGenreDisplay(arg, "sgHorror")
    SGINDIE = getUserSettingGenreDisplay(arg, "sgIndie")
    SGMUSIC = getUserSettingGenreDisplay(arg, "sgMusic")
    SGROMANCE = getUserSettingGenreDisplay(arg, "sgRomance")
    SGSCIFI = getUserSettingGenreDisplay(arg, "sgSciFi")
    SGSPECIALINTEREST = getUserSettingGenreDisplay(arg, "sgSpecialInterest")
    SGSPORTS = getUserSettingGenreDisplay(arg, "sgSports")
    SGTV = getUserSettingGenreDisplay(arg, "sgTV")
    SGTHRILLERS = getUserSettingGenreDisplay(arg, "sgThrillers")
    
    #get addon info
    __settings__ = xbmcaddon.Addon(id='plugin.video.xbmcflicks')
    ROOT_FOLDER = __settings__.getAddonInfo('path')
    RESOURCE_FOLDER = os.path.join(str(ROOT_FOLDER), 'resources')
    LIB_FOLDER = os.path.join(str(RESOURCE_FOLDER), 'lib')
    WORKING_FOLDER = xbmc.translatePath(__settings__.getAddonInfo("profile"))
    LINKS_FOLDER = os.path.join(str(WORKING_FOLDER), 'links')
    REAL_LINK_PATH = os.path.join(str(WORKING_FOLDER), 'links')
    USERINFO_FOLDER = WORKING_FOLDER
    XBMCPROFILE = xbmc.translatePath('special://profile')
    if(DEBUG):
        print "root folder: " + ROOT_FOLDER
        print "working folder: " + WORKING_FOLDER
        print "links folder: " + LINKS_FOLDER
        print "real link path: " + REAL_LINK_PATH
        print "resource folder: " + RESOURCE_FOLDER
        print "lib folder: " + LIB_FOLDER
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
    userInfoFileLoc = os.path.join(str(USERINFO_FOLDER), 'userinfo.txt')
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
        print "couldn't load user information from userinfo.txt file"
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
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getRecommendedQueue():
    initApp()
    if(not user):
        exit
    getUserRecommendedQueue(netflixClient, user)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getNewToWatchInstantCA(strArg):
    initApp()
    if(not user):
        exit
    curUrl = "http://www.netflix.ca/NewWatchInstantlyRSS"
    convertRSSFeed(getUrlString(curUrl), 500, None, strArg)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getNewToWatchInstantCATopX(strArg):
    initApp()
    if(not user):
        exit
    curUrl = "http://www.netflix.ca/NewWatchInstantlyRSS"
    convertRSSFeed(getUrlString(curUrl), 25, None, strArg)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getNewToWatchInstant(strArg):
    initApp()
    if(not user):
        exit
    curUrl = "http://www.netflix.com/NewWatchInstantlyRSS"
    convertRSSFeed(getUrlString(curUrl), 500, None, strArg)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getNewToWatchInstantTopX(strArg):
    initApp()
    if(not user):
        exit    
    curUrl = "http://www.netflix.com/NewWatchInstantlyRSS"
    convertRSSFeed(getUrlString(curUrl), 25, None, strArg)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getTop25Feed(strArg):
    initApp()
    curUrl = "http://rss.netflix.com/Top25RSS?gid=" + str(strArg)
    convertRSSFeed(getUrlString(curUrl), 25)
    time.sleep(1)
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getTop25FeedD(strArg):
    initApp()
    curUrl = "http://rss.netflix.com/Top25RSS?gid=" + str(strArg)
    convertRSSFeed(getUrlString(curUrl), 25, True)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def escape(s):
    """Escape a URL including any /."""
    return urllib.quote(s, safe='~')

def _utf8_str(s):
    """Convert unicode to utf-8."""
    if isinstance(s, unicode):
        return s.encode("utf-8")
    else:
        return str(s)

def normalize_params(params):
    # Escape key values before sorting.
    key_values = [(escape(_utf8_str(k)), escape(_utf8_str(v))) \
        for k,v in params.items()]
    # Combine key value pairs into a string.
    return '?' + '&'.join(['$%s=%s' % (k, v) for k, v in key_values])

def checkGenre(strGenreName):
    result = False
    if SGGAY:
        if re.search(r"(lesb|gay|sex|erotic|experimental)", strGenreName, re.IGNORECASE):
            return "lesbian.png&genre=Gay & Lesbian"
    else:
        if re.search(r"(lesb|gay|sex|erotic|experimental)", strGenreName, re.IGNORECASE):
            return False

    if SGACTION:
        if re.search(r"(action|adventures|mobster|heist|swashbucklers|westerns|epics|blockbusters)", strGenreName, re.IGNORECASE):
            return "action.png&genre=Action & Adventure"
    if SGANIME:
        if re.search(r"(anime|animation)", strGenreName, re.IGNORECASE):
            return "anime.png&genre=Anime"
##    if SGBLURAY:
##        if re.search(r"blu", strGenreName, re.IGNORECASE):
##            return "bluray.png&genre=Blu-ray"
    if SGCHILDREN:
        if re.search(r"(book characters|animal tales|dinosaurs|nickelodeon|children|family|ages 0-2|ages 2-4|ages 5-7|ages 8-10|ages 11-12|cartoon|comic|kids|disney|inspirational|magic)", strGenreName, re.IGNORECASE):
            return "children.png&genre=Children & Family"
    if SGCOMEDY:
        if re.search(r"(mock|spoof|screwball|stand-up|saturday night live|slapstick|comedy|comedies|humor)", strGenreName, re.IGNORECASE):
            return "comedy.png&genre=Comedy"
    if SGDOCUMENTARY:
        if re.search(r"document", strGenreName, re.IGNORECASE):
            return "documentary.png&genre=Documentary"
    if SGDRAMA:
        if re.search(r"biographies|suspense|drama|mystery|underdogs|epics|blockbusters", strGenreName, re.IGNORECASE):
            return "drama.png&genre=Drama"
    if SGFAITH:
        if re.search(r"(religious|god|faith|pray|spirit)", strGenreName, re.IGNORECASE):
            return "faith.png&genre=Faith & Spirituality"
    if SGHORROR:
        if re.search(r"(monsters|satanic|horror|scream|dead|slash|kill)", strGenreName, re.IGNORECASE):
            return "horror.png&genre=Horror"
    if SGINDIE:
        if re.search(r"(indie|independent|IMAX|LOGO|film noir)", strGenreName, re.IGNORECASE):
            return "independent.png&genre=Independant"
    if SGMUSIC:
        if re.search(r"(blues|swing|reggae|singer|tunes|art|music|rock|rap|guitar|bass|jazz|r&b|folk|language|drum|guitar|banjo|karaoke|pop|concerts|piano|disco|country|new age|keyboard|opera)", strGenreName, re.IGNORECASE):
            return "music.png&genre=Music"
    if SGROMANCE:
        if re.search(r"(shakespeare|tearjerk|romance)", strGenreName, re.IGNORECASE):
            return "romance.png&genre=Romance"
    if SGSCIFI:
        if re.search(r"(sci-fi|scifi|science|fantasy)", strGenreName, re.IGNORECASE):
            return "scifi.png&genre=Sci-Fi"
    if SGSPECIALINTEREST:
        if re.search(r"(world|coming of age|theatrical|period pieces|sculpture|wine|social studies|sytle|beauty|voice lessons|technology|math|meditation|body|home|garden|pets|special|hobbies|math|food|heal|homespecial|blaxploitation|painting|poker|goth|computer|hobby|entertaining|preganancy|parent|career|bollywood|cooking)", strGenreName, re.IGNORECASE):
            return "special_interest.png&genre=Special Interest"
    if SGTV:
        if re.search(r"(car culture|tv|television)", strGenreName, re.IGNORECASE):
            return "television.png&genre=Television"
    if SGSPORTS:
        if re.search(r"(skateboarding|climbing|soccer|skiing|self-def|snowboard|wrestling|yoga|tai chi|climbing|golf|stunts|tennis|fishing|pilates|fitness|car|hockey|biking|olympics|bmx|bodybuilding|car|kung fu|strength|sports|racing|baseball|basketball|boxing|aerobics|cycling|dance|boxing|karate|martial arts|extreme combat|glutes|football|workout|motorcycle|hunting|boat)", strGenreName, re.IGNORECASE):
            return "sports.png&genre=Sports"
    if SGTHRILLERS:
        if re.search(r"(thrill|werewolves|vampires|frankenstein|zombies|creature)", strGenreName, re.IGNORECASE):
            return "thrillers.png&genre=Thrillers"
    if SGCLASSICS:
        if re.search(r"(classic|silent)", strGenreName, re.IGNORECASE):
            return "classics.png&genre=Classics"
    if SGFOREIGN:
        if re.search(r"(russia|china|foreign|scandinavia|asia|spain|thailand|united kingdom|brazil|australia|czech|africa|argentina|belgium|eastern|france|germany|greece|hong kong|india|iran|israel|italy|japan|judaica|korea|latin america|mexico|middle east|netherlands|philippines|poland)", strGenreName, re.IGNORECASE):
            return "foreign.png&genre=Foreign"
    if(DEBUG):
        print "Filtered out: " + strGenreName
    return False

def getInstantGenres():
    initApp()
    boolDiscQueue = False
    parameters = {}
    parameters['format'] = "json"
    parameters['callback'] = "render"
    requestUrl = "http://odata.netflix.com/Catalog/Genres"
    requestUri = requestUrl + normalize_params(parameters)
    print requestUri
    data = getUrlString(requestUri)
    #print data
    reobj = re.compile(r"(?sm)(?sm)(?P<main>(__metadata)((?!(__metadata)).)*)", re.DOTALL | re.MULTILINE)
    #real processing begins here
    for matchGenre in reobj.finditer(str(data)):
        curQueueItem = matchGenre.group(1)
        #now parse out each item
        reobj = re.compile('"uri": "http://odata.netflix.com/Catalog/Genres\\(\'(?P<linkname>[^\']*?)\'\\)", "type": "NetflixCatalog.Model.Genre".*?}, "Name": "(?P<displayname>.*?)", "Titles": {', re.DOTALL | re.MULTILINE)
        for matchGenreItem in reobj.finditer(curQueueItem):
            curX = XInfo()
            curX.Title = matchGenreItem.group(2)
            curX.LinkName = matchGenreItem.group(1)
            curGenreCheckData = checkGenre(curX.Title)
            match = re.search(r"(.*\.png)&genre=(.*)", str(curGenreCheckData))
            if match:
                curX.Poster = os.path.join(str(RESOURCE_FOLDER), str(match.group(1)))
                curX.Genres = match.group(2)
                curX.nomenu = True
                addDirectoryItem(curX, parameters={ PARAMETER_KEY_MODE:"gExpand" + "lId" + curX.LinkName + str(boolDiscQueue) }, isFolder=True, thumbnail=curX.Poster)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def oDataSearch(strSeachValue, sDiscMode):
    #http://odata.netflix.com/Catalog/Titles?$filter=substringof%28%27xxx%27,%20Name%29
    instantOnly = False
    strType = "0"
    initApp()
    parameters = {}
    searchString = "substringof('" + str(strSeachValue) + "', Name)"
    parameters['filter'] = searchString
    parameters['format'] = "json"
    parameters['callback'] = "render"
    if(sDiscMode == "False"):
        instantOnly = True
        #parameters['filter'] = searchString + " and Instant/Available eq true"
    requestUrl = "http://odata.netflix.com/Catalog/Titles"
    requestUri = requestUrl + normalize_params(parameters)
    print requestUri
    data = getUrlString(requestUri)
    #print data
    if(DEBUG):
        print data
        #simplejson.dumps(data,indent=4)
    counter = 0
    reobj = re.compile(r'(?sm)(?P<main>(__metadata": {.{1,100}"uri")((?!(__metadata": {.{1,100}"uri")).)*)', re.DOTALL | re.IGNORECASE | re.MULTILINE)
    for match in reobj.finditer(str(data)):
        curX = XInfo()
        curQueueItem = match.group(1)
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflixClient, instantOnly, strType)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def getGenreListing(nGenreLID, sDiscMode):
    instantOnly = False
    strType = "0"
    initApp()
    parameters = {}
    parameters['format'] = "json"
    parameters['callback'] = "render"
    if(sDiscMode == "False"):
        parameters['filter'] = "Instant/Available eq true"
    requestUrl = "http://odata.netflix.com/Catalog/Genres('" + nGenreLID + "')/Titles"
    requestUri = requestUrl + normalize_params(parameters)
    data = getUrlString(requestUri)
    #print data
    if(DEBUG):
        print data
        #simplejson.dumps(data,indent=4)
    counter = 0
    reobj = re.compile(r'(?sm)(?P<main>(__metadata": {.{1,100}"uri")((?!(__metadata": {.{1,100}"uri")).)*)', re.DOTALL | re.IGNORECASE | re.MULTILINE)
    for match in reobj.finditer(str(data)):
        curX = XInfo()
        curQueueItem = match.group(1)
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflixClient, instantOnly, strType)
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
##    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
##    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getEpisodeListing(nShowID, nSeasonID, sDiscMode):
    print "iQueue TV ShowID : " + nShowID
    print "iQueue TV SeasonID : : " + nSeasonID
    print "FormatMode?: " + sDiscMode
    instantOnly = True
    strType = "5"
    initApp()
    if(not user):
        exit    
    feeds = netflixClient.user.getSeries(nShowID,nSeasonID,sDiscMode,0,100)
    if(DEBUG):
        print simplejson.dumps(feeds,indent=4)
    counter = 0
    #parse each item in queue by looking for the category: [ string 
    reobj = re.compile(r"(?sm)(?P<main>('catalog_title': )((?!('catalog_title': )).)*)", re.DOTALL | re.MULTILINE)
    for match in reobj.finditer(str(feeds)):
        curX = XInfo()
        curQueueItem = match.group(1)
        if(DEBUG):
            print "current feed item from regex is: " + curQueueItem
        #now parse out each item
        curX = getMovieDataFromFeed(curX, curQueueItem, False, netflixClient, instantOnly, strType, True)
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
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getDVDQueue(displayWhat):
    initApp()
    getUserDiscQueue(netflixClient,user, displayWhat)
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def rhShipped():
    initApp()
    getUserRentalHistory(netflixClient,user, "shipped", "3")
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def rhReturned():
    initApp()
    getUserRentalHistory(netflixClient,user, "returned", "3")
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def rhWatched():
    initApp()
    getUserRentalHistory(netflixClient,user, "watched")
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getHomeList():
    initApp()
    getUserAtHomeItems(netflixClient,user)
    if(not user):
        exit
    time.sleep(1)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    xbmcplugin.setContent(int(sys.argv[1]),'Movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
