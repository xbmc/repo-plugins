import sys
import urllib
import urllib2


import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

from resources.lib.games_live import *
from resources.lib.games_archive import *
from resources.lib.common import *


def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
                            
    return param


def addLink(name,url,title,iconimage):
    if iconimage == '':
        iconimage = ICON
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setProperty('fanart_image',FANART)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)


def addDir(name,url,mode,iconimage,isfolder):
    if iconimage == '':
        iconimage = ICON
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    print u
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty('fanart_image',FANART)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,liz,isfolder)
    

def CATEGORIES():
    #Delete or generate the thumbnails
    if (DELETETHUMBNAILS == 'true') or (GENERATETHUMBNAILS == 'true'):
        updateThumbs()
    
    #Check if cookies are up to date
    checkLogin()
    
    if (USERNAME in open(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')).read()) and USERNAME != '':
        #Show categories
        addDir(LOCAL_STRING(31100),'/live',1,'',True)
        #addDir(LOCAL_STRING(31150),'/lastnight',9,'',True)
        addDir(LOCAL_STRING(31160),'/latest',11,'',True)
        addDir(LOCAL_STRING(31140),'/highlights',4,'',True)
        addDir(LOCAL_STRING(31110),'/condensed',4,'',True)
        addDir(LOCAL_STRING(31120),'/archive',4,'',True)

        #Space between Score Notifications
        addDir('','Do Nothing',-1,'',False)
        addDir('Turn On Score Notifications','Notifications ON',100,'',False)
        addDir('Turn Off Score Notifications','Notifications OFF',101,'',False)
        #addDir(LOCAL_STRING(31130),'/classic',10,'',True)
    else:
        os.remove(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        print "cookies removed"
        
        dialog = xbmcgui.Dialog()
        dialog.ok('Login failed', 'Check your login credentials')
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),succeeded=False)
        return None



def LIVE(url):   
    #Check if cookies are up to date
    checkLogin()
    
    #Get live games
    games = getLiveGames(True)
    
    for game in games:
        #Icon path
        iconPath = ''
        if USETHUMBNAILS == 'true':
            iconPath = os.path.join(ADDON_PATH_PROFILE, "images/" + THUMBFORMAT + "_" + BACKGROUND + "/"+ game[7] + "vs" + game[6] + ".png")
        
        #Add Game
        if game[4]:
            if QUALITY == 5: #Go to quality selection screen            
                addDir(game[5],url + "/" + game[0],2,iconPath,True)
            else: #Go to the stream selection screen
                addDir(game[5],url + "/" + game[0],3,iconPath,True)
        else:
            teams = game[5][21:]
            time = game[5][11:19]
            time = time.lstrip("0")            
            addDir(teams + " at " + time,url,1,iconPath,True)    

def LIVEQUALITY(url):    
    addDir('Best', url + '/bestquality',3,'',True)
    if 'highlights' not in url:
        addDir('HD (5000 kbit/s)', url + '/5000K',3,'',True)

    addDir('HD (3000 kbit/s)', url + '/3000K',3,'',True)
    addDir('SD (1600 kbit/s)', url + '/1600K',3,'',True)
    addDir('SD (800 kbit/s)', url + '/800K',3,'',True)


def LIVELINKS(url):
    #Get live games
    links = getLiveGameLinks(url)

    #Icon path
    iconPath = ''
    if USETHUMBNAILS == 'true':
        iconPath = os.path.join(ADDON_PATH_PROFILE, "images/" + THUMBFORMAT + "_" + BACKGROUND + "/"+ links[0][1] + "vs" + links[0][0] + ".png")
    
    #Remove teamnames (not needed anymore)
    del links[0]

    #Add links    
    for link in links:       
        if link[1] == '':
            addDir(link[0],url,3,iconPath,True)
        else:
            addLink(link[0],link[1],link[0],iconPath)


def ARCHIVE(url):
    #Check if cookies are up to date
    checkLogin()
    #Get all available Seasons
    seasonList = getSeasons()
    
    for season in seasonList:
        addDir(str(season[0]) + ' - ' + str(season[0] + 1),url+'/'+str(season[0]),5,ICON,True)
    

def ARCHIVEMONTH(url):
    #Load the list of seasons
    seasonList = pickle.load(open(os.path.join(ADDON_PATH_PROFILE, 'archive'),"rb"))

    for season in seasonList:
        if int(url.split('/')[-1]) == season[0]:
            months = season
            del months[0] #element 0: season, e.g. 2014
            
            for month in months:
                addDir(LOCAL_STRING(31200 + month),url+'/'+str(month).zfill(2),6,ICON,True)
            
            break


def ARCHIVEGAMES(url):
    #Get the list of games
    gameList = getGames(url)    
    #Add Games
    date = ''
    for game in gameList:
        #Icon path
        iconPath = ''
        if USETHUMBNAILS == 'true':
            iconPath = os.path.join(ADDON_PATH_PROFILE, "images/" + THUMBFORMAT + "_" + BACKGROUND + "/"+ game[3] + "vs" + game[2] + ".png")
        
        #print game

        if date <> game[0][0:10]:            
            date = game[0][0:10]
            addLink('[COLOR=FFFFFFFF][B][I]' + date + '[/I][/B][/COLOR]','','','')
        #print url
        if game[1] == "":
            addLink(game[0],'','','')
        else:
            #Add Directory
            if QUALITY == 5: #Go to quality selection screen
                addDir(game[0][12:],url+"/"+game[1],7,iconPath,True)
            else: #Go to the stream selection screen
                addDir(game[0][12:],url+"/"+game[1],8,iconPath,True)
            

def ARCHIVEQUALITY(url):        
    year = url.split("/")[2]
    addDir('Best', url + '/bestquality',8,'',True)
    if int(year) >= 2014:
        addDir('HD (5000 kbit/s)', url + '/5000K',8,'',True)
    elif int(year) >= 2012:    
        addDir('HD (4500 kbit/s)', url + '/4500K',8,'',True)

    addDir('HD (3000 kbit/s)', url + '/3000K',8,'',True)
    addDir('SD (1600 kbit/s)', url + '/1600K',8,'',True)
    addDir('SD (800 kbit/s)', url + '/800K',8,'',True)

    
def ARCHIVELINKS(url):
    #Get live games
    print url
    links = getGameLinks(url)

    #Title
    title = links[0]
    
    #Icon path
    iconPath = ''
    if USETHUMBNAILS == 'true':
        iconPath = os.path.join(ADDON_PATH_PROFILE, "images/" + THUMBFORMAT + "_" + BACKGROUND + "/"+ links[1][1] + "vs" + links[1][0] + ".png")

    #Get teamnames
    teams = getTeams()
    #teams[awayTeam][TEAMNAME]
    homeTeam = teams[str(links[1][0])][TEAMNAME]
    awayTeam = teams[str(links[1][1])][TEAMNAME]
    #Remove teamnames and title (not needed anymore)
    del links[0]
    del links[0]    
    #Add links
    for link in links:
        print link[0] #Home / Away
        print link[1] #Video url
        if link[0] == "Home":
            addLink(link[0] + " (" + homeTeam + " feed)",link[1],title + ' (' + link[0] + ')',iconPath)
        else:
            addLink(link[0] + " (" + awayTeam + " feed)",link[1],title + ' (' + link[0] + ')',iconPath)

"""
def LASTNIGHT(url):
    #Get season list
    seasonList = getSeasons()
    
    #If latest season fails, try previous season
    try:
        url = url + "/" + str(seasonList[0][0]) + "/" + str(seasonList[0][1])
    except:
        url = url + "/" + str(seasonList[1][0]) + "/" + str(seasonList[1][1])
    
    #Get the list of games
    gameList = getGames(url)
    
    #Add Games
    for game in gameList:
        #Icon path
        iconPath = ''
        if USETHUMBNAILS == 'true':
            iconPath = os.path.join(ADDON_PATH_PROFILE, "images/" + THUMBFORMAT + "_" + BACKGROUND + "/"+ game[3] + "vs" + game[2] + ".png")
        
        #Add Directory
        addDir(game[0],url+"/"+game[1],10,iconPath,True)

    
def LASTNIGHTTYPE(url):
    if QUALITY == 5: #Go to quality selection screen
        addDir(LOCAL_STRING(31500),url+"/highlights",7,'',True)
        addDir(LOCAL_STRING(31501),url+"/condensed" ,7,'',True)
        addDir(LOCAL_STRING(31502),url+"/archive",7,'',True)
    else: #Go to the stream selection screen
        addDir(LOCAL_STRING(31500),url+"/highlights",8,'',True)
        addDir(LOCAL_STRING(31501),url+"/condensed" ,8,'',True)
        addDir(LOCAL_STRING(31502),url+"/archive",8,'',True)
"""    

def LATESTGAMES(url):
    #Check if cookies are up to date
    checkLogin()
    #Get live games
    games = getLiveGames(False)
    
    date = ''
    for game in games:
        #Icon path
        iconPath = ''
        if USETHUMBNAILS == 'true':
            iconPath = os.path.join(ADDON_PATH_PROFILE, "images/" + THUMBFORMAT + "_" + BACKGROUND + "/"+ game[7] + "vs" + game[6] + ".png")
        
        #Add Game
        if date <> game[5][0:10]:
            date = game[5][0:10]
            addLink('[COLOR=FFFFFFFF][B][I]' + date + '[/I][/B][/COLOR]','','','')
        if game[4]:
            addDir(game[5][21:],url + "/" + game[0],14,iconPath,True)
        else:
            addDir(game[5][21:],url,11,iconPath,True)


def LATESTGTYPE(url):
    if QUALITY == 5: #Go to quality selection screen
        addDir(LOCAL_STRING(31500),url+"/highlights",12,'',True)
        addDir(LOCAL_STRING(31501),url+"/condensed" ,12,'',True)
        addDir(LOCAL_STRING(31502),url+"/archive",12,'',True)
    else: #Go to the stream selection screen
        addDir(LOCAL_STRING(31500),url+"/highlights",13,'',True)
        addDir(LOCAL_STRING(31501),url+"/condensed" ,13,'',True)
        addDir(LOCAL_STRING(31502),url+"/archive",13,'',True)


def LATESTGQUALITY(url):
    addDir('Best', url + '/bestquality',13,'',True)
    if "highlights" not in url:
        addDir('HD (5000 kbit/s)', url + '/5000K',13,'',True)
    addDir('HD (3000 kbit/s)', url + '/3000K',13,'',True)
    addDir('SD (1600 kbit/s)', url + '/1600K',13,'',True)
    addDir('SD (800 kbit/s)', url + '/800K',13,'',True)


def LATESTGLINKS(url):
    #Get live games
    links = getLiveGameLinks(url)

    #Icon path
    iconPath = ''
    if USETHUMBNAILS == 'true':
        iconPath = os.path.join(ADDON_PATH_PROFILE, "images/" + THUMBFORMAT + "_" + BACKGROUND + "/"+ links[0][1] + "vs" + links[0][0] + ".png")
    
    #Remove teamnames (not needed anymore)
    del links[0]
    
    #Add links
    for link in links:
        if link[1] == '':
            addDir(link[0],url,13,iconPath,True)
        else:
            addLink(link[0],link[1],link[0],iconPath)