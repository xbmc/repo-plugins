#!/usr/bin/python
# encoding: utf-8
import urllib
import urllib2
import socket
import sys
import re
import os
import json
import sqlite3
import random
import datetime
import time
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import urlparse

import SimpleDownloader
import requests
#from email import Message

#this import for the youtube_dl addon causes our addon to start slower. we'll import it when we need to playYTDLVideo   
if 'mode=playYTDLVideo' in sys.argv[2] :
    import YDStreamExtractor      #note: you can't just add this import in code, you need to re-install the addon with <import addon="script.module.youtube.dl"        version="16.521.0"/> in addon.xml

#YDStreamExtractor.disableDASHVideo(True) #Kodi (XBMC) only plays the video for DASH streams, so you don't want these normally. Of course these are the only 1080p streams on YouTube
from urllib import urlencode
reload(sys)
sys.setdefaultencoding("utf-8")




addon         = xbmcaddon.Addon()
addon_path    = addon.getAddonInfo('path')
pluginhandle  = int(sys.argv[1])
addonID       = addon.getAddonInfo('id')  #plugin.video.reddit_viewer

WINDOW        = xbmcgui.Window(10000)
#technique borrowed from LazyTV. 
#  WINDOW is like a mailbox for passing data from caller to callee. 
#    e.g.: addLink() needs to pass "image description" to playSlideshow()

osWin         = xbmc.getCondVisibility('system.platform.windows')
osOsx         = xbmc.getCondVisibility('system.platform.osx')
osLinux       = xbmc.getCondVisibility('system.platform.linux')

if osWin:
    fd="\\"
else:
    fd="/"

socket.setdefaulttimeout(30)
opener = urllib2.build_opener()
#opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))

#https://github.com/reddit/reddit/wiki/API
userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"
reddit_clientID      ="hXEx62LGqxLj8w"    
reddit_redirect_uri  ='http://localhost:8090/'   #specified when registering for a clientID
reddit_refresh_token =addon.getSetting("reddit_refresh_token")
reddit_access_token  =addon.getSetting("reddit_access_token") #1hour token

#test1 line

opener.addheaders = [('User-Agent', userAgent)]
#API requests with a bearer token should be made to https://oauth.reddit.com, NOT www.reddit.com.
urlMain = "https://www.reddit.com"


#filter           = addon.getSetting("filter") == "true"
#filterRating     = int(addon.getSetting("filterRating"))
#filterThreshold  = int(addon.getSetting("filterThreshold"))

showAll              = addon.getSetting("showAll") == "true"
showUnwatched        = addon.getSetting("showUnwatched") == "true"
showUnfinished       = addon.getSetting("showUnfinished") == "true"
showAllNewest        = addon.getSetting("showAllNewest") == "true"
showUnwatchedNewest  = addon.getSetting("showUnwatchedNewest") == "true"
showUnfinishedNewest = addon.getSetting("showUnfinishedNewest") == "true"

forceViewMode        = addon.getSetting("forceViewMode") == "true"
viewMode             = str(addon.getSetting("viewMode"))
comments_viewMode    = str(addon.getSetting("comments_viewMode"))
album_viewMode       = str(addon.getSetting("album_viewMode"))

r_AccessToken         = addon.getSetting("r_AccessToken") 

sitemsPerPage        = addon.getSetting("itemsPerPage")
try: itemsPerPage = int(sitemsPerPage)
except: itemsPerPage = 50    

itemsPerPage          = ["10", "25", "50", "75", "100"][itemsPerPage]
TitleAddtlInfo        = addon.getSetting("TitleAddtlInfo") == "true"   #Show additional post info on title</string>
HideImagePostsOnVideo = addon.getSetting("HideImagePostsOnVideo") == 'true' #<string id="30204">Hide image posts on video addon</string>
setting_hide_images = False

# searchSort = int(addon.getSetting("searchSort"))
# searchSort = ["ask", "relevance", "new", "hot", "top", "comments"][searchSort]
# searchTime = int(addon.getSetting("searchTime"))
# searchTime = ["ask", "hour", "day", "week", "month", "year", "all"][searchTime]

#--- settings related to context menu "Show Comments"
CommentTreshold          = addon.getSetting("CommentTreshold") 
try: int_CommentTreshold = int(CommentTreshold)
except: int_CommentTreshold = -1000    #if CommentTreshold can't be converted to int, show all comments 

#showBrowser     = addon.getSetting("showBrowser") == "true"
#browser_win     = int(addon.getSetting("browser_win"))
#browser_wb_zoom = str(addon.getSetting("browser_wb_zoom"))

ll_qualiy  = int(addon.getSetting("ll_qualiy"))
ll_qualiy  = ["480p", "720p"][ll_qualiy]
ll_downDir = str(addon.getSetting("ll_downDir"))

istreamable_quality =int(addon.getSetting("streamable_quality"))  #values 0 or 1
streamable_quality  =["full", "mobile"][istreamable_quality]       #https://streamable.com/documentation

gfy_downDir = str(addon.getSetting("gfy_downDir"))

addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
subredditsFile      = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits")
nsfwFile            = xbmc.translatePath("special://profile/addon_data/"+addonID+"/nsfw")

#C:\Users\myusername\AppData\Roaming\Kodi\userdata\addon_data\plugin.video.reddit_viewer
#SlideshowCacheFolder    = xbmc.translatePath("special://profile/addon_data/"+addonID+"/slideshowcache") #will use this to cache images for slideshow in video mode

if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)

#if not os.path.isdir(SlideshowCacheFolder):
#    os.mkdir(SlideshowCacheFolder)

allHosterQuery = urllib.quote_plus("site:youtu.be OR site:youtube.com OR site:vimeo.com OR site:liveleak.com OR site:dailymotion.com OR site:gfycat.com")
if os.path.exists(nsfwFile):
    nsfw = ""
else:
    nsfw = "nsfw:no+"





def getDbPath():
    path = xbmc.translatePath("special://userdata/Database")
    files = os.listdir(path)
    latest = ""
    for file in files:
        if file[:8] == 'MyVideos' and file[-3:] == '.db':
            if file > latest:
                latest = file
    if latest:
        return os.path.join(path, latest)
    else:
        return ""
    
def getPlayCount(url):
    if dbPath:
        c.execute('SELECT playCount FROM files WHERE strFilename=?', [url])
        result = c.fetchone()
        if result:
            result = result[0]
            if result:
                return int(result)
            return 0
    return -1

def format_multihub(multihub):
#properly format a multihub string
#make sure input is a valid multihub 
    t = multihub
    #t='User/sallyyy19/M/video'
    ls = t.split('/')

    for idx, word in enumerate(ls):
        if word.lower()=='user':ls[idx]='user'
        if word.lower()=='m'   :ls[idx]='m'
    #xbmc.log ("/".join(ls))            
    return "/".join(ls)
    
    
#MODE addSubreddit      - name, type not used
def addSubreddit(subreddit, name, type):
    alreadyIn = False
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    if subreddit:
        for line in content:
            if line.lower()==subreddit.lower():
                alreadyIn = True
        if not alreadyIn:
            fh = open(subredditsFile, 'a')
            fh.write(subreddit+'\n')
            fh.close()
    else:
        #dialog = xbmcgui.Dialog()
        #ok = dialog.ok('Add subreddit', 'Add a subreddit (videos)','or  Multiple subreddits (music+listentothis)','or  Multireddit (/user/.../m/video)')
        #would be great to have some sort of help to show first time user here
        
        keyboard = xbmc.Keyboard('', translation(30001))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            subreddit = keyboard.getText()

            #cleanup user input. make sure /user/ and /m/ is lowercase
            if this_is_a_multihub(subreddit):
                subreddit = format_multihub(subreddit)
            
            for line in content:
                if line.lower()==subreddit.lower()+"\n":
                    alreadyIn = True
            if not alreadyIn:
                fh = open(subredditsFile, 'a')
                fh.write(subreddit+'\n')
                fh.close()
        xbmc.executebuiltin("Container.Refresh")

#MODE removeSubreddit      - name, type not used
def removeSubreddit(subreddit, name, type):
    #note: calling code in addDirR() 
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    contentNew = ""
    for line in content:
        if line!=subreddit+'\n':
            #log('line='+line+'toremove='+subreddit)
            contentNew+=line
    fh = open(subredditsFile, 'w')
    fh.write(contentNew)
    fh.close()
    xbmc.executebuiltin("Container.Refresh")

def editSubreddit(subreddit, name, type):
    #note: calling code in addDirR() 
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    contentNew = ""

    keyboard = xbmc.Keyboard(subreddit, translation(30003))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        newsubreddit = keyboard.getText()
        #cleanup user input. make sure /user/ and /m/ is lowercase
        if this_is_a_multihub(newsubreddit):
            newsubreddit = format_multihub(newsubreddit)
        
        for line in content:
            if line.strip()==subreddit.strip() :      #if matches the old subreddit,
                #log("adding: %s  %s  %s" %(line, subreddit, newsubreddit)  )
                contentNew+=newsubreddit+'\n'
            else:
                contentNew+=line

        fh = open(subredditsFile, 'w')
        fh.write(contentNew)
        fh.close()
            
        xbmc.executebuiltin("Container.Refresh")    

def this_is_a_multihub(subreddit):
    #subreddits and multihub are stored in the same file
    #i think we can get away with just testing for user/ to determine multihub
    if subreddit.lower().startswith('user/') or subreddit.lower().startswith('/user/'): #user can enter multihub with or without the / in the beginning
        return True
    else:
        return False

def assemble_reddit_filter_string(search_string, subreddit, skip_site_filters="", domain="" ):
    #skip_site_filters -not adding a search query makes your results more like the reddit website 
    #search_string will not be used anymore, replaced by domain. leaving it here for now.
    #    using search string to filter by domain returns the same result everyday 
    
    url = urlMain      # global variable urlMain = "http://www.reddit.com"

    a=[':','/domain/']
    if any(x in subreddit for x in a):  #search for ':' or '/domain/'
        #log("domain "+ subreddit)
        domain=re.findall(r'(?::|\/domain\/)(.+)',subreddit)[0]
        #log("domain "+ str(domain))
        

    if domain:
        # put '/?' at the end. looks ugly but works fine.
        #https://www.reddit.com/domain/vimeo.com/?&limit=5
        url+= "/domain/%s/.json?" %(domain)   #/domain doesn't work with /search?q=
    else:
        if this_is_a_multihub(subreddit):
            #e.g: https://www.reddit.com/user/sallyyy19/m/video/search?q=multihub&restrict_sr=on&sort=relevance&t=all
            #https://www.reddit.com/user/sallyyy19/m/video
            #url+='/user/sallyyy19/m/video'     
            #format_multihub(subreddit)
            if subreddit.startswith('/'):
                #log("startswith/") 
                url+=subreddit  #user can enter multihub with or without the / in the beginning
            else: url+='/'+subreddit
        else:
            if subreddit: 
                url+= "/r/"+subreddit
            else: 
                url+= "/r/all"
 
        site_filter=""
        if search_string:  #search string overrides our supported sites filter
            search_string = urllib.unquote_plus(search_string)
            url+= "/search.json?q=" + urllib.quote_plus(search_string)
        elif skip_site_filters: 
            url+= "/.json?"
        else:            
            #url+= "/.json?"
            for site in supported_sites :
                if site[0] and site[5]:  #site[0]  is the show_youtube/show_vimeo/show_dailymotion/... global variables taken from settings file
                    site_filter += site[5] + " OR "
            #remove the last ' OR '
            if site_filter.endswith(" OR "):  site_filter = site_filter[:-4]
            #log("FILTER_STRING="+site_filter)
            #url += urllib.quote_plus(site_filter)
            url+= "/search.json?q=" + urllib.quote_plus(site_filter)
            #url += urllib.quote_plus(site_filter)

    url+= "&"+nsfw       #nsfw = "nsfw:no+"
    
    url += "&limit="+str(itemsPerPage)
    #url += "&limit=12"
    #log("assemble_reddit_filter_string="+url)
    return url

def site_filter_for_reddit_search():
    #go through the supported sites list and assemble the reddit search filter for them
    #except youtube_dl sites (too many)
    
    #this is only used for "search reddit" list item 
    site_filter=""
    
    for site in supported_sites :
        if site[0] and site[5]:  #site[0]  is the show_youtube/show_vimeo/show_dailymotion/... global variables taken from settings file
            site_filter += site[5] + " OR "
    #remove the last ' OR '
    if site_filter.endswith(" OR "):  site_filter = site_filter[:-4]

    #url+= "/search.json?q=" + urllib.quote_plus(site_filter)
    
    return urllib.quote_plus(site_filter)   #str( sites_filter )

def parse_subreddit_entry(subreddit_entry_from_file):
    #returns subreddit, [alias] and description. also populates WINDOW mailbox for custom view id of subreddit
    #  description= a friendly description of the 'subreddit shortcut' on the first page of addon 
    #    used for skins that display them

    subreddit, alias, viewid = subreddit_alias( subreddit_entry_from_file )

    description=subreddit
    #check for domain filter
    a=[':','/domain/']
    if any(x in subreddit for x in a):  #search for ':' or '/domain/'
        #log("domain "+ subreddit)
        domain=re.findall(r'(?::|\/domain\/)(.+)',subreddit)[0]
        description=translation(30008) % domain            #"Show posts from"
    
    #describe combined subreddits    
    if '+' in subreddit:
        description=subreddit.replace('+','[CR]')

    #describe multireddit or multihub
    if this_is_a_multihub(subreddit):
        description=translation(30007)  #"Custom Multireddit"

    #save that view id in our global mailbox (retrieved by listVideos)
    WINDOW.setProperty('viewid-'+subreddit, viewid)

    if viewid:
        #add it in the description
        description+='[CR]%s %s' %(translation(30011),viewid)   #View ID:
    
    return subreddit, alias, description

def subreddit_alias( subreddit_entry_from_file ):
    #users can specify an alias for the subredit and it is stored in the file as a regular string  e.g. diy[do it yourself]  
    #this function returns the subreddit without the alias identifier and alias if any or alias=subreddit if none
    ## in addition, users can specify custom viewID for a subreddit by encapsulating the viewid in ()'s
    
    a=re.compile(r"(\[[^\]]*\])") #this regex only catches the [] 
    #a=re.compile(r"(\[[^\]]*\])?(\(\d+\))?") #this regex catches the [] and ()'s
    alias=""
    viewid=""
    #return the subreddit without the alias. but (viewid), if present, is still there
    subreddit = a.sub("",subreddit_entry_from_file).strip()
    #log( "  re:" +  subreddit )
    
    #get the viewID
    try:viewid= subreddit[subreddit.index("(") + 1:subreddit.rindex(")")]
    except:viewid=""
    #log( "viewID=%s for r/%s" %( viewid, subreddit ) )
    
    if viewid:
        #remove the (viewID) string from subreddit 
        subreddit=subreddit.replace( "(%s)"%viewid, "" )

    #get the [alias]
    a= a.findall(subreddit_entry_from_file)
    if a:
        alias=a[0]
        #log( "      alias:" + alias )
    else:
        alias = subreddit
    
    return subreddit, alias, viewid

def index(url,name,type):
    
    ## this is where the __main screen is created
    content = ""
    if not os.path.exists(subredditsFile):
        #create a default file and sites
        fh = open(subredditsFile, 'a')
        #fh.write('/user/gummywormsyum/m/videoswithsubstance\n')
        fh.write('/user/sallyyy19/m/video[%s]\n' %(translation(30006)))  # user   http://forum.kodi.tv/member.php?action=profile&uid=134499
        fh.write('Documentaries+ArtisanVideos+lectures+LearnUselessTalents\n')
        fh.write('Stop_Motion+FrameByFrame+Brickfilms+Animation\n')
        #fh.write('SlowMotion+timelapse+PerfectTiming\n')
        fh.write('all\n')
        fh.write('aww+funny+Nickelodeons\n')
        fh.write('music+listentothis+musicvideos\n')
        fh.write('site:youtube.com\n')
        fh.write('videos\n')
        #fh.write('videos/new\n')
        fh.write('woahdude+interestingasfuck+shittyrobots\n')
        fh.close()
        #justiceporn
    #log(content)

    #log( sys.argv[0] ) #plugin://plugin.video.reddit_viewer/
    #log( addonID )     #plugin.video.reddit_viewer
    #log( "aaaaaaa" + addon.getAddonInfo('path') )
    #log( "bbbbbbb" + addon.getAddonInfo('profile') )

    #testing code
    #h="as asd [S]asdasd[/S] asdas "
    #log(markdown_to_bbcode(h))
    #addDir('test', "url", "next_mode", "", "subreddit" )


    #liz = xbmcgui.ListItem(label="test", label2="label2", iconImage="DefaultFolder.png")
    #u=sys.argv[0]+"?url=&mode=callwebviewer&type="
    #xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=False)
    
    
    entries = []
    if os.path.exists(subredditsFile):
        #log(subredditsFile) #....\Kodi\userdata\addon_data\plugin.video.reddit_viewer\subreddits
        fh = open(subredditsFile, 'r')
        content = fh.read()
        fh.close()
        spl = content.split('\n')
        
        for i in range(0, len(spl), 1):
            if spl[i]:
                subreddit = spl[i].strip()
                
                #entries.append(subreddit.title())  #this capitalizes the first letter of a word. looks nice but not necessary
                entries.append(subreddit )
    entries.sort()

    #this controls what infolabels will be used by the skin. very skin specific. 
    #  for estuary, this lets infolabel:plot (and genre) show up below the folder
    #  giving us the opportunity to provide a shortcut_description about the shortcuts
    xbmcplugin.setContent(pluginhandle, "mixed")

    #sys.argv[0] is plugin://plugin.video.reddit_viewer/
    #addDir("testing", sys.argv[0], "reddit_login", "" )  #<--- for testing
    
    next_mode='listVideos'
    for subreddit_entry in entries:
        #log(subreddit)
        
        #strip out the alias identifier from the subreddit string retrieved from the file so we can process it.
        #subreddit, alias = subreddit_alias(subreddit_entry) 
        
        subreddit, alias, shortcut_description=parse_subreddit_entry(subreddit_entry)
        #log( subreddit + "   " + shortcut_description )

        #url= urlMain+"/r/"+subreddit+"/.json?"+nsfw+allHosterQuery+"&limit="+itemsPerPage
        url= assemble_reddit_filter_string("",subreddit, "yes")
        #log("assembled================="+url)
        if subreddit.lower() == "all":  
            #   we're NOT asking reddit to filter the links for us.  
            #      we filter the supported sites in make_addon_url_from() to only show the supported sites to the user
            #   it is done this way because if we ask reddit to filter the links for us (search?q=site:youtube.com OR site:vimeo.com OR ... &restrict_sr=&sort=relevance&t=all )
            #      the results do not match the front page.
            addDir(subreddit, url, next_mode, "", subreddit, { "plot": translation(30009) } )  #Displays the currently most popular content from all of reddit....
        else:                           
            #addDirR(subreddit, subreddit.lower(), next_mode, "")
            addDirR(alias, url, next_mode, "", subreddit, { "plot": shortcut_description }, subreddit_entry )


    addDir("[B]- "+translation(30001)+"[/B]", "", 'addSubreddit', "", "", { "plot": translation(30006) } ) #"Customize this list with your favorite subreddit."
    addDir("[B]- "+translation(30005)+"[/B]", "",'searchReddits', "", "", { "plot": translation(30010) } ) #"Search reddit for a particular post or topic
    
    xbmcplugin.endOfDirectory(pluginhandle)

#MODE listVideos(url, name, type)    --name not used
def listVideos(url, name, subreddit_key):
    #url=r'https://www.reddit.com/r/videos/search.json?q=nsfw:yes+site%3Ayoutu.be+OR+site%3Ayoutube.com+OR+site%3Avimeo.com+OR+site%3Aliveleak.com+OR+site%3Adailymotion.com+OR+site%3Agfycat.com&sort=relevance&restrict_sr=on&limit=5&t=week'
    #url='https://www.reddit.com/search.json?q=site%3Adailymotion&restrict_sr=&sort=relevance&t=week'
    #url='https://www.reddit.com/search.json?q=site%3A4tube&sort=relevance&t=all'
    #url="https://www.reddit.com/domain/tumblr.com.json"
    #url="https://www.reddit.com/r/wiiu.json?&nsfw:no+&limit=13"

    #show_listVideos_debug=False
    show_listVideos_debug=True
    credate = ""
    is_a_video=False
    title_line2=""
    log("listVideos subreddit=%s url=%s" %(subreddit_key,url) )
    t_on = translation(30071)  #"on"
    #t_pts = u"\U0001F4AC"  # translation(30072) #"cmnts"  comment bubble symbol. doesn't work
    t_pts = u"\U00002709"  # translation(30072)   envelope symbol

    thumb_w=0
    thumb_h=0

    currentUrl = url
    xbmcplugin.setContent(pluginhandle, "movies") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos
        
    content = reddit_request(url)        
    #content = opener.open(url).read()
    
    if not content:
        return

    info_label={ "plot": translation(30013) }  #Automatically play videos
    if showAllNewest:
        addDir("[B]- "+translation(30016)+"[/B]", url, 'autoPlay', "", "ALL_NEW", info_label)
    if showUnwatchedNewest:
        addDir("[B]- "+translation(30017)+"[/B]", url, 'autoPlay', "", "UNWATCHED_NEW", info_label)
    if showUnfinishedNewest:
        addDir("[B]- "+translation(30018)+"[/B]", url, 'autoPlay', "", "UNFINISHED_NEW", info_label)
    if showAll:
        addDir("[B]- "+translation(30012)+"[/B]", url, 'autoPlay', "", "ALL_RANDOM", info_label)
    if showUnwatched:
        addDir("[B]- "+translation(30014)+"[/B]", url, 'autoPlay', "", "UNWATCHED_RANDOM", info_label)
    if showUnfinished:
        addDir("[B]- "+translation(30015)+"[/B]", url, 'autoPlay', "", "UNFINISHED_RANDOM", info_label)

    
    #7-15-2016  removed the "replace(..." statement below cause it was causing error
    #content = json.loads(content.replace('\\"', '\''))
    content = json.loads(content) 
    
    #log("query returned %d items " % len(content['data']['children']) )
    posts_count=len(content['data']['children'])
    
    hms = has_multiple_subreddits(content['data']['children'])
    
    for idx, entry in enumerate(content['data']['children']):
        try:
            title = cleanTitle(entry['data']['title'].encode('utf-8'))
            
            try:
                description = cleanTitle(entry['data']['media']['oembed']['description'].encode('utf-8'))
            except:
                description = ' '
                
            commentsUrl = urlMain+entry['data']['permalink'].encode('utf-8')
            #if show_listVideos_debug :log("commentsUrl"+str(idx)+"="+commentsUrl)

            try:
                aaa = entry['data']['created_utc']
                credate = datetime.datetime.utcfromtimestamp( aaa )
                #log("creation_date="+str(credate))
                
                ##from datetime import datetime
                #now = datetime.datetime.now()
                #log("     now_date="+str(now))
                ##from dateutil import tz
                now_utc = datetime.datetime.utcnow()
                #log("     utc_date="+str(now_utc))
                #log("  pretty_date="+pretty_datediff(now_utc, credate))
                pretty_date=pretty_datediff(now_utc, credate)
                credate = str(credate)
            except:
                credate = ""
                credateTime = ""

            subreddit=entry['data']['subreddit'].encode('utf-8')
            #if show_listVideos_debug :log("  SUBREDDIT"+str(idx)+"="+subreddit)
            try: author = entry['data']['author'].encode('utf-8')
            except: author = ""
            #if show_listVideos_debug :log("     AUTHOR"+str(idx)+"="+author)
            
            ups = entry['data']['score']       #downs not used anymore
            try:num_comments = entry['data']['num_comments']
            except:num_comments = 0
            
            #description = "[COLOR blue]r/"+ subreddit + "[/COLOR]  [I]" + str(ups)+" pts  |  "+str(comments)+" cmnts  |  by "+author+"[/I]\n"+description
            #description = "[COLOR blue]r/"+ subreddit + "[/COLOR]  [I]" + str(ups)+" pts.  |  by "+author+"[/I]\n"+description
            #description = title_line2+"\n"+description
            #if show_listVideos_debug :log("DESCRIPTION"+str(idx)+"=["+description+"]")
            try:
                media_url = entry['data']['url'].encode('utf-8')
            except:
                media_url = entry['data']['media']['oembed']['url'].encode('utf-8')
                
            thumb = entry['data']['thumbnail'].encode('utf-8')
            #if show_listSubReddit_debug : log("       THUMB%.2d=%s" %( idx, thumb ))
            
            if thumb in ['nsfw','default','self']:  #reddit has a "default" thumbnail (alien holding camera with "?")
                thumb=""               

            if thumb=="":
                try: thumb = entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8').replace('&amp;','&')
                except: pass
            
            try:
                #collect_thumbs(entry)
                preview=entry['data']['preview']['images'][0]['source']['url'].encode('utf-8').replace('&amp;','&')
                #poster = entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8')
                #t=thumb.split('?')[0]
                #can't preview gif thumbnail on thumbnail view, use alternate provided by reddit
                #if t.endswith('.gif'):
                    #log('  thumb ends with .gif')
                #    thumb = entry['data']['thumbnail'].encode('utf-8')
                
                try:
                    thumb_h = float( entry['data']['preview']['images'][0]['source']['height'] )
                    thumb_w = float( entry['data']['preview']['images'][0]['source']['width'] )
                except:
                    thumb_w=0
                    thumb_h=0

            except Exception as e:
                #log("   getting preview image EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
                thumb_w=0
                thumb_h=0
                preview="" #a blank preview image will be replaced with poster_url from make_addon_url_from() for domains that support it

            is_a_video = determine_if_video_media_from_reddit_json(entry) 
                
            try:
                over_18 = entry['data']['over_18']
            except:
                over_18 = False

            #setting: toggle showing 2-line title 
            #log("   TitleAddtlInfo "+str(idx)+"="+str(TitleAddtlInfo))
            title_line2=""
            #if TitleAddtlInfo:
            #title_line2 = "[I][COLOR dimgrey]%s by %s [COLOR darkslategrey]r/%s[/COLOR] %d pts.[/COLOR][/I]" %(pretty_date,author,subreddit,ups)
            #title_line2 = "[I][COLOR dimgrey]"+pretty_date+" by "+author+" [COLOR darkslategrey]r/"+subreddit+"[/COLOR] "+str(ups)+" pts.[/COLOR][/I]"

            title_line2 = "[I][COLOR dimgrey]%s %s [COLOR darkslategrey]r/%s[/COLOR] (%d) %s[/COLOR][/I]" %(pretty_date,t_on, subreddit,num_comments, t_pts)
            #title_line2 = "[I]"+str(idx)+". [COLOR dimgrey]"+ media_url[0:50]  +"[/COLOR][/I] "  # +"    "+" [COLOR darkslategrey]r/"+subreddit+"[/COLOR] "+str(ups)+" pts.[/COLOR][/I]"

            #if show_listVideos_debug : log( ("v" if is_a_video else " ") +"     TITLE"+str(idx)+"="+title)
            if show_listVideos_debug : log("  POST%cTITLE%.2d=%s" %( ("v" if is_a_video else " "), idx, title ))
            #if show_listVideos_debug :log("      OVER_18"+str(idx)+"="+str(over_18))
            #if show_listVideos_debug :log("   IS_A_VIDEO"+str(idx)+"="+str(is_a_video))
            #if show_listVideos_debug :log("        THUMB"+str(idx)+"="+thumb)
            #if show_listVideos_debug :log("    MediaURL%.2d=%s" % (idx,media_url) )

            #if show_listVideos_debug :log("       HOSTER"+str(idx)+"="+hoster)
            #log("    VIDEOID"+str(idx)+"="+videoID)
            #log( "["+description+"]1["+ str(date)+"]2["+ str( count)+"]3["+ str( commentsUrl)+"]4["+ str( subreddit)+"]5["+ video_url +"]6["+ str( over_18))+"]"
            addLink(title=title, 
                    title_line2=title_line2,
                    iconimage=thumb, 
                    previewimage=preview,
                    preview_w=thumb_w,
                    preview_h=thumb_h,
                    description=description, 
                    credate=credate, 
                    reddit_says_is_video=is_a_video, 
                    site=commentsUrl, 
                    subreddit=subreddit, 
                    media_url=media_url, 
                    over_18=over_18,
                    posted_by=author,
                    num_comments=num_comments,
                    post_index=idx,
                    post_total=posts_count,
                    many_subreddit=hms)
        except Exception as e:
            log(" EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
            pass
    
    #log("**reddit query returned "+ str(idx) +" items")
    #window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    #log("focusid:"+str(window.getFocusId()))

    try:
        #this part makes sure that you load the next page instead of just the first
        after=""
        after = content['data']['after']
        if "&after=" in currentUrl:
            nextUrl = currentUrl[:currentUrl.find("&after=")]+"&after="+after
        else:
            nextUrl = currentUrl+"&after="+after
            
        # plot shows up on estuary. etc. ( avoids the "No information available" message on description ) 
        info_label={ "plot": translation(30004) }  
        addDir(translation(30004), nextUrl, 'listVideos', "", subreddit,info_label)   #Next Page
        #if show_listVideos_debug :log("NEXT PAGE="+nextUrl) 
    except:
        pass
    
    #the +'s got removed by url conversion 
    subreddit_key=subreddit_key.replace(' ','+')
    viewID=WINDOW.getProperty( "viewid-"+subreddit_key )
    #log("  custom viewid %s for %s " %(viewID,subreddit_key) )

    if viewID:
        log("  custom viewid %s for %s " %(viewID,subreddit_key) )
        xbmc.executebuiltin('Container.SetViewMode(%s)' %viewID )
    else:
        if forceViewMode:
            xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
        
    xbmcplugin.endOfDirectory(pluginhandle)



def addLink(title, title_line2, iconimage, previewimage,preview_w,preview_h,description, credate, reddit_says_is_video, site, subreddit, media_url, over_18, posted_by="", num_comments=0,post_index=1,post_total=1,many_subreddit=False ):
    
    videoID=""
    post_title=title
    il_description=""
    n=""  #will hold red nsfw asterisk string
    h=""  #will hold bold hoster:  string
    t_Album = translation(30073) if translation(30073) else "Album"
    t_IMG =  translation(30074) if translation(30074) else "IMG"
    
    ok = False    
    #DirectoryItem_url=""
    from resources.domains import make_addon_url_from
    hoster, DirectoryItem_url, videoID, mode_type, thumb_url, poster_url, isFolder,setInfo_type, IsPlayable=make_addon_url_from(media_url,reddit_says_is_video)

    if iconimage in ["","nsfw", "default"]:
        #log( title+ ' iconimage blank['+iconimage+']['+thumb_url+ ']media_url:'+media_url ) 
        iconimage=thumb_url
        
    if poster_url=="":
        if previewimage:
            poster_url=previewimage
        else:
            poster_url=iconimage
            
    #mode=mode_type #usually 'playVideo'
    if DirectoryItem_url:
        h="[B]" + hoster + "[/B]: "
        if over_18: 
            mpaa="R"
            n = "[COLOR red]*[/COLOR] "
            #description = "[B]" + hoster + "[/B]:[COLOR red][NSFW][/COLOR] "+title+"\n" + description
            il_description = "[COLOR red][NSFW][/COLOR] "+ h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"
        else:
            mpaa=""
            il_description = h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"

        if TitleAddtlInfo:     #put the additional info on the description if setting set to single line titles
            post_title=title+"[CR]"+title_line2
        else:
            post_title=title
            il_description=title_line2+"[CR]"+il_description
            
        il={"title": post_title, "plot": il_description, "plotoutline": il_description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin

        if setting_hide_images==True and mode_type in ['listImgurAlbum','playSlideshow','listLinksInComment' ]:
            log('setting: hide non-video links') #and text links(reddit.com)
            return
        else:
            if mode_type in ['listImgurAlbum','playSlideshow','listLinksInComment','playTumblr','playInstagram','playFlickr' ]:
                #after all that work creating DirectoryItem_url, we parse it to get the media_url. this is used by playSlideshow as 'key' to get the image description
                #parsed = urlparse.urlparse(DirectoryItem_url)
                #media_url=urlparse.parse_qs(parsed.query)['url'][0]  #<-- this will error in openelec/linux    
                #log("   parsed media_url:" +  media_url  )
                #log("   parsed plugi_url:" +  videoID  )
                #WINDOW.setProperty(videoID, description )
                WINDOW.setProperty(videoID, il_description )

        
        if mode_type in ['listImgurAlbum','listTumblrAlbum', 'listFlickrAlbum']:post_title='[%s] %s' %(t_Album, post_title)
        #if mode_type=='playSlideshow': post_title='[IMG] '+post_title   
        if setInfo_type=='pictures'  : 
            post_title='[%s] %s' %(t_IMG, post_title)
                  
        if mode_type=='listLinksInComment': post_title='[reddit] '+post_title  
        
        liz=xbmcgui.ListItem(label=n+post_title, 
                              label2="",
                              iconImage="DefaultVideo.png", thumbnailImage=iconimage)

        liz.setInfo(type='video', infoLabels=il)
        
        #art_object
        liz.setArt({"thumb": iconimage, "poster":poster_url, "banner":iconimage, "fanart":poster_url, "landscape":poster_url   })

        #liz.setInfo(type=setInfo_type, infoLabels=il)
        
        liz.setProperty('IsPlayable', IsPlayable)
        
        entries = [] #entries for listbox for when you type 'c' or rt-click 


        if num_comments > 0:            
            #if we are using a custom gui to show comments, we need to use RunPlugin. there is a weird loading/pause if we use XBMC.Container.Update. i think xbmc expects us to use addDirectoryItem
            #  if we have xbmc manage the gui(addDirectoryItem), we need to use XBMC.Container.Update. otherwise we'll get the dreaded "Attempt to use invalid handle -1" error
            #entries.append( ( translation(30050) + " (c)",  #Show comments
            #              "XBMC.RunPlugin(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(site) ) ) )            
            #entries.append( ( translation(30052) , #Show comment links 
            #              "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s&type=linksOnly)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(site) ) ) )            

            entries.append( ( translation(30052) , #Show comment links 
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s&type=linksOnly)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(site) ) ) )            
            entries.append( ( translation(30050) ,  #Show comments
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(site) ) ) )

            #entries.append( ( translation(30050) + " (ActivateWindow)",  #Show comments
            #              "XBMC.ActivateWindow(Video, %s?mode=listLinksInComment&url=%s)" % (  sys.argv[0], urllib.quote_plus(site) ) ) )      #***  ActivateWindow is for the standard xbmc window     
        else:
            entries.append( ( translation(30053) ,  #No comments
                          "xbmc.executebuiltin('Action(Close)')" ) )            

        #no need to show the "go to other subreddits" if the entire list is from one subreddit        
        if many_subreddit:
            #sys.argv[0] is plugin://plugin.video.reddit_viewer/
            #prl=zaza is just a dummy: during testing the first argument is ignored... possible bug?
            entries.append( ( translation(30051)+" r/%s" %subreddit , 
                              "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listVideos&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit,True)  ) ) ) )
        else:
            entries.append( ( translation(30051)+" r/%s" %subreddit , 
                              "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listVideos&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit+'/new',True)  ) ) ) )


        #favEntry = '<favourite name="'+title+'" url="'+DirectoryItem_url+'" description="'+description+'" thumb="'+iconimage+'" date="'+credate+'" site="'+site+'" />'
        #entries.append((translation(30022), 'RunPlugin(plugin://'+addonID+'/?mode=addToFavs&url='+urllib.quote_plus(favEntry)+'&type='+urllib.quote_plus(subreddit)+')',))
        
        #if showBrowser and (osWin or osOsx or osLinux):
        #    if osWin and browser_win==0:
        #        entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.webbrowser/?url='+urllib.quote_plus(site)+'&mode=showSite&zoom='+browser_wb_zoom+'&stopPlayback=no&showPopups=no&showScrollbar=no)',))
        #    else:
        #        entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.chrome.launcher/?url='+urllib.quote_plus(site)+'&mode=showSite)',))
        liz.addContextMenuItems(entries)

        #you will get a WARNING: XFILE::CFileFactory::CreateLoader - unsupported protocol(plugin) in ....
        #reason: listitem=liz  has a   liz.setInfo(type="Video",...  set above
        #        xbmc will check if url is compatible with type="Video"
        #        we get a warning because url starts with 'plugin://' 
        #to make warning not show up, do not setInfo type="Video" on liz
        #but doing this will also not show the infolabels(title,plot,aired.etc.) to the user
        #u='http://i.imgur.com/IcpWBvq.jpg'
        #log("addDirectoryItem url["+u+"]")
        
        xbmcplugin.addDirectoryItem(pluginhandle, DirectoryItem_url, listitem=liz, isFolder=isFolder, totalItems=post_total)
        
    return ok
#MODE listFavourites -  name, type not used
# def listFavourites(subreddit, name, type):
#     xbmcplugin.setContent(pluginhandle, "episodes")
#     file = os.path.join(addonUserDataFolder, subreddit+".fav")
#     xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
#     if os.path.exists(file):
#         fh = open(file, 'r')
#         content = fh.read()
#         fh.close()
#         match = re.compile('<favourite name="(.+?)" url="(.+?)" description="(.+?)" thumb="(.+?)" date="(.+?)" site="(.+?)" />', re.DOTALL).findall(content)
#         for name, url, desc, thumb, date, site in match:
#             addFavLink(name, url, "playVideo", thumb, desc.replace("<br>","\n"), date, site, subreddit)
#     if forceViewMode:
#         xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
#     xbmcplugin.endOfDirectory(pluginhandle)

#MODE autoPlay        - name not used
def autoPlay(url, name, type):
    from resources.domains import make_addon_url_from
    #collect a list of title and urls as entries[] from the j_entries obtained from reddit
    #then create a playlist from those entries
    #then play the playlist

    entries = []
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    log("**********autoPlay*************")
    #content = opener.open(url).read()
    content = reddit_request(url)        
    if not content: return

    content = json.loads(content.replace('\\"', '\''))
    
    log("Autoplay %s - Parsing %d items" %( type, len(content['data']['children']) )    )
    
    for j_entry in content['data']['children']:
        try:
            #title = cleanTitle(entry['data']['media']['oembed']['title'].encode('utf-8'))
            title = cleanTitle(j_entry['data']['title'].encode('utf-8'))

            try:
                media_url = j_entry['data']['url']
            except:
                media_url = j_entry['data']['media']['oembed']['url']

            is_a_video = determine_if_video_media_from_reddit_json(j_entry) 

            #log("  Title:%s -%c"  %( title, ("v" if is_a_video else " ") ) )              
            hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, IsPlayable=make_addon_url_from(media_url,is_a_video)

            if DirectoryItem_url:
                if isFolder:  #imgur albums are 'isFolder'
                    #log('      skipping isFolder ')
                    continue
                if setInfo_type=='pictures': #we also skip images in autoplay
                    #log('      skipping setInfo_type==pictures ')
                    continue
                
                if setting_hide_images==True and mode_type in ['listImgurAlbum','playSlideshow','listLinksInComment' ]:
                    #log("      skipping 'listImgurAlbum','playSlideshow','listLinksInComment' ")
                    continue                
                
                if type.startswith("ALL_"):
                    #log("      ALL_" )
                    entries.append([title, DirectoryItem_url])
                elif type.startswith("UNWATCHED_") and getPlayCount(url) < 0:
                    #log("      UNWATCHED_" )
                    entries.append([title, DirectoryItem_url])
                elif type.startswith("UNFINISHED_") and getPlayCount(url) == 0:
                    #log("      UNFINISHED_" )
                    entries.append([title, DirectoryItem_url])
        except:
            pass
    
    if type.endswith("_RANDOM"):
        random.shuffle(entries)

    #for title, url in entries:
    #    log("  added to playlist:"+ title + "  " + urllib.unquote_plus(url) )
    for title, url in entries:
        listitem = xbmcgui.ListItem(title)
        playlist.add(url, listitem)
    xbmc.Player().play(playlist)

def determine_if_video_media_from_reddit_json( entry ):
    #reads the reddit json and determines if link is a video
    is_a_video=False
    
    try:
        media_url = entry['data']['media']['oembed']['url']   #+'"'
    except:
        media_url = entry['data']['url']   #+'"'
    
    media_url=media_url.split('?')[0] #get rid of the query string
    try:
        zzz = entry['data']['media']['oembed']['type']
        #log("    zzz"+str(idx)+"="+str(zzz))
        if zzz == None:   #usually, entry['data']['media'] is null for not videos but it is also null for gifv especially nsfw
            if ".gifv" in media_url.lower():  #special case for imgur
                is_a_video=True
            else:
                is_a_video=False
        elif zzz == 'video':  
            is_a_video=True
        else:
            is_a_video=False
    except:
        is_a_video=False

    return is_a_video

def has_multiple_subreddits(content_data_children):
    #check if content['data']['children'] returned by reddit contains a single subreddit or not
    s=""
    #compare the first subreddit with the rest of the list. 
    for entry in content_data_children:
        if s:
            if s!=entry['data']['subreddit'].encode('utf-8'):
                #log("  multiple subreddit")
                return True
        else:
            s=entry['data']['subreddit'].encode('utf-8')
    
    #log("  single subreddit")
    return False




def getYoutubeDownloadPluginUrl(id):
    return "plugin://plugin.video.youtube/?path=/root/search&action=download&videoid=" + id

def getVimeoDownloadPluginUrl(id):
    return "plugin://plugin.video.vimeo/?path=/root/search/new/search&action=download&videoid=" + id

def getDailymotionDownloadPluginUrl(id):
    return "plugin://plugin.video.dailymotion_com/?mode=downloadVideo&url=" + id

def getLiveleakDownloadPluginUrl(id):
    return "%s?mode=downloadLiveLeakVideo&url=%s" %(sys.argv[0], id )

def getGfycatDownloadPluginUrl(id):
    return "%s?mode=downloadGfycatVideo&url=%s" %(sys.argv[0], id )


def getLiveLeakStreamUrl(id):
    #log("getLiveLeakStreamUrl ID="+str(id) )
    #sometimes liveleak items are news articles and not video. 
    url=None
    content = opener.open("http://www.liveleak.com/view?i="+id).read()
    matchHD = re.compile('hd_file_url=(.+?)&', re.DOTALL).findall(content)
    matchSD = re.compile('file: "(.+?)"', re.DOTALL).findall(content)
    if matchHD and ll_qualiy=="720p":
        url = urllib.unquote_plus(matchHD[0])
    elif matchSD:
        url = matchSD[0]
    #log("**********getLiveLeakStreamUrl hd_file_url="+url)
    return url

#MODE playVideo       - name, type not used
def playVideo(url, name, type):
    if url :
        #url='http://i.imgur.com/ARdeL4F.mp4'
        #url='plugin://plugin.video.reddit_viewer/?mode=comments_gui'
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    else:
        log("playVideo(url) url is blank")
        
def playYTDLVideo(url, name, type):
    #url = "http://www.youtube.com/watch?v=_yVv9dx88x0"   #a youtube ID will work as well and of course you could pass the url of another site
    
    #url='https://www.youtube.com/shared?ci=W8n3GMW5RCY'
    #url='http://burningcamel.com/video/waster-blonde-amateur-gets-fucked'
    #url='http://www.3sat.de/mediathek/?mode=play&obj=51264'
    #url='http://www.4tube.com/videos/209271/hurry-fuck-i-bored'
    #url='http://www.pbs.org/newshour/rundown/cubas-elian-gonzalez-now-college-graduate/'
    choices = []

#these checks done in around May 2016
#does not work:  yourlust  porntube xpornvid.com porndig.com  thumbzilla.com eporner.com yuvutu.com porn.com pornerbros.com fux.com flyflv.com xstigma.com sexu.com 5min.com alphaporno.com
# stickyxtube.com xxxbunker.com bdsmstreak.com  jizzxman.com pornwebms.com pornurl.pw porness.tv openload.online pornworms.com fapgod.com porness.tv hvdporn.com pornmax.xyz xfig.net yobt.com
# eroshare.com kalporn.com hdvideos.porn dailygirlscute.com desianalporn.com indianxxxhd.com onlypron.com sherloxxx.com hdvideos.porn x1xporn.com pornhvd.com lxxlx.com xrhub.com shooshtime.com
# pornvil.com lxxlx.com redclip.xyz younow.com aniboom.com  gotporn.com  virtualtaboo.com 18porn.xyz vidshort.net fapxl.com vidmega.net freudbox.com bigtits.com xfapzap.com orgasm.com
# userporn.com hdpornstar.com moviesand.com chumleaf.com fucktube.com fookgle.com pornative.com dailee.com pornsharia.com fux.com sluttyred.com pk5.net kuntfutube.com youpunish.com
# vidxnet.com jizzbox.com bondagetube.tv spankingtube.tv pornheed.com pornwaiter.com lubetube.com porncor.com maxjizztube.com asianxtv.com analxtv.com yteenporn.com nurglestube.com yporn.tv
# asiantubesex.com zuzandra.com moviesguy.com bustnow.com dirtydirtyangels.com yazum.com watchersweb.com voyeurweb.com zoig.com flingtube.com yourfreeporn.us foxgay.com goshgay.com
# player.moviefap.com(www.moviefap.com works) nosvideo.com

# also does not work (non porn)
# rutube.ru  mail.ru  afreeca.com nicovideo.jp  videos.sapo.pt(many but not all) sciencestage.com vidoosh.tv metacafe.com vzaar.com videojug.com trilulilu.ro tudou.com video.yahoo.com blinkx.com blip.tv
# blogtv.com  brainpop.com crackle.com engagemedia.org expotv.com flickr.com fotki.com hulu.com lafango.com  mefeedia.com motionpictur.com izlesene.com sevenload.com patas.in myvideo.de
# vbox7.com 1tv.ru 1up.com 220.ro 24video.xxx 3sat.de 56.com adultswim.com atresplayer.com techchannel.att.com v.baidu.com azubu.tv www.bbc.co.uk/iplayer bet.com biobiochile.cl biqle.com
# bloomberg.com/news/videos bpb.de bravotv.com byutv.org cbc.ca chirbit.com cloudtime.to(almost) cloudyvideos.com cracked.com crackle.com criterion.com ctv.ca culturebox.francetvinfo.fr
# cultureunplugged.com cwtv.com daum.net dctp.tv democracynow.org douyutv.com dumpert.nl eitb.tv ex.fm fc-zenit.ru  ikudonsubs.com akb48ma.com Flipagram.com ft.dk Formula1.com
# fox.com/watch(few works) video.foxnews.com foxsports.com france2.fr franceculture.fr franceinter.fr francetv.fr/videos francetvinfo.fr giantbomb.com hbo.com History.com hitbox.tv
# howcast.com HowStuffWorks.com hrt.hr iconosquare.com infoq.com  ivi.ru kamcord.com/v video.kankan.com karrierevideos.at KrasView.ru hlamer.ru kuwo.cn la7.it laola1.tv le.com
# media.ccc.de metacritic.com mitele.es  moevideo.net,playreplay.net,videochart.net vidspot.net(might work, can't find recent post) movieclips.com mtv.de mtviggy.com muenchen.tv myspace.com
# myvi.ru myvideo.de myvideo.ge 163.com netzkino.de nfb.ca nicovideo.jp  videohive.net normalboots.com nowness.com ntr.nl nrk.no ntv.ru/video ocw.mit.edu odnoklassniki.ru/video 
# onet.tv onionstudios.com/videos openload.co orf.at parliamentlive.tv pbs.org

# news site (can't find sample to test) 
# bleacherreport.com crooksandliars.com DailyMail.com channel5.com Funimation.com gamersyde.com gamespot.com gazeta.pl helsinki.fi hotnewhiphop.com lemonde.fr mnet.com motorsport.com MSN.com
# n-tv.de ndr.de NDTV.com NextMedia.com noz.de


# these sites have mixed media. can handle the video in these sites: 
# 20min.ch 5min.com archive.org Allocine.fr(added) br.de bt.no  buzzfeed.com condenast.com firstpost.com gameinformer.com gputechconf.com heise.de HotStar.com(some play) lrt.lt natgeo.com
# nbcsports.com  patreon.com 
# 9c9media.com(no posts)

#ytdl plays this fine but no video?
#coub.com

#supported but is an audio only site 
#acast.com AudioBoom.com audiomack.com bandcamp.com clyp.it democracynow.org? freesound.org hark.com hearthis.at hypem.com libsyn.com mixcloud.com
#Minhateca.com.br(direct mp3) 

# 
# ytdl also supports these sites: 
# myvideo.co.za  ?
#bluegartr.com  (gif)
# behindkink.com   (not sure)
# facebook.com  (need to work capturing only videos)
# features.aol.com  (inconsistent)
# livestream.com (need to work capturing only videos)
# mail.ru inconsistent(need to work capturing only videos)
# miomio.tv(some play but most won't)
# ooyala.com(some play but most won't)
#  
    
#     extractors=[]
#     from youtube_dl.extractor import gen_extractors
#     for ie in gen_extractors():  
#         #extractors.append(ie.IE_NAME)
#         try:
#             log("[%s] %s " %(ie.IE_NAME, ie._VALID_URL) )
#         except Exception as e:
#             log( "zz   " + str(e) )

#     extractors.sort()
#     for n in extractors: log("'%s'," %n)

    try:
        if YDStreamExtractor.mightHaveVideo(url,resolve_redirects=True):
            log('    YDStreamExtractor.mightHaveVideo[true]=' + url)
            vid = YDStreamExtractor.getVideoInfo(url,0,True)  #quality is 0=SD, 1=720p, 2=1080p and is a maximum
            if vid:
                log("      getVideoInfo playableURL="+vid.streamURL())
                if vid.hasMultipleStreams():
                    log("        vid hasMultipleStreams")
                    for s in vid.streams():
                        title = s['title']
                        log('      choices' + title  )
                        choices.append(title)
                    #index = some_function_asking_the_user_to_choose(choices)
                    vid.selectStream(0) #You can also pass in the the dict for the chosen stream
        
                stream_url = vid.streamURL()                         #This is what Kodi (XBMC) will play        
                listitem = xbmcgui.ListItem(path=stream_url)
                xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
            else:
                #log("getVideoInfo failed==" )
                xbmc.executebuiltin('XBMC.Notification("'+ translation(30192) +'", "Youtube_dl" )' )  
    except Exception as e:
        #log( "zz   " + str(e) )
        xbmc.executebuiltin('XBMC.Notification("Youtube_dl","%s")' %str(e)  )
        

#MODE playGfycatVideo       - name, type not used
def playGfycatVideo(id, name, type):
    content = opener.open("http://gfycat.com/cajax/get/"+id).read()
    content = json.loads(content.replace('\\"', '\''))
    
    if "gfyItem" in content and "mp4Url" in content["gfyItem"]:
        GfycatStreamUrl=content["gfyItem"]["mp4Url"]
    
    playVideo(GfycatStreamUrl, name, type)

def listLinksInComment(url, name, type):
    from resources.domains import make_addon_url_from
    #called by context menu
    log('listLinksInComment:%s:%s' %(type,url) )

    #does not work for list comments coz key is the playable url (not reddit comments url)
    #msg=WINDOW.getProperty(url)
    #WINDOW.clearProperty( url )
    #log( '   msg=' + msg )

    directory_items=[]
    author=""
    ShowOnlyCommentsWithlink=False

    if type=='linksOnly':
        ShowOnlyCommentsWithlink=True
        
    #sometimes the url has a query string. we discard it coz we add .json at the end
    #url=url.split('?', 1)[0]+'.json'

    #url='https://www.reddit.com/r/Music/comments/4k02t1/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/' + '.json'
    #only get up to "https://www.reddit.com/r/Music/comments/4k02t1". 
    #   do not include                                            "/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/"
    #   because we'll have problem when it looks like this: "https://www.reddit.com/r/Overwatch/comments/4nx91h/ever_get_that_feeling_dÃ©jÃ _vu/"
    
    url=re.findall(r'(.*/comments/[A-Za-z0-9]+)',url)[0] 
    url+='.json'
    #log("listLinksInComment:"+url)

    #content = opener.open(url).read()  
    content = reddit_request(url)        
    if not content: return

    
    #log(content)
    #content = json.loads(content.replace('\\"', '\''))  #some error here ?      TypeError: 'NoneType' object is not callable
    content = json.loads(content)
    
    del harvest[:]
    #harvest links in the post text (just 1) 
    r_linkHunter(content[0]['data']['children'])
    
    #the post title is provided in json, we'll just use that instead of messages from addLink()
    try:post_title=content[0]['data']['children'][0]['data']['title']
    except:post_title=''
    #for i, h in enumerate(harvest):
    #    log("aaaaa first harvest "+h[2])

    #harvest links in the post itself    
    r_linkHunter(content[1]['data']['children'])

    comment_score=0
    for i, h in enumerate(harvest):
        #log(str(i)+"  score:"+ str(h[0]).zfill(5)+" "+ h[1] +'|'+ h[3] )
        comment_score=h[0]
        #log("score %d < %d (%s)" %(comment_score,int_CommentTreshold, CommentTreshold) )
        
        
        if comment_score < int_CommentTreshold:
            continue
        
        hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, setProperty_IsPlayable =make_addon_url_from(h[2])
    
        #mode_type #usually 'playVideo'
        kind=h[6] #reddit uses t1 for user comments and t3 for OP text of the post. like a poster describing the post.  
        d=h[5]   #depth of the comment
        
        tab=" "*d if d>0 else "-"
        
        author=h[7]
        
        if kind=='t1':
            list_title=r"[I]%2d pts.[/I] %s" %( h[0], tab )
        elif kind=='t3':
            list_title=r"[I]Title [/I] %s" %( tab )
            
        desc100=h[3].replace('\n',' ')[0:100] #first 100 characters of description
        
        if DirectoryItem_url:
            #(score, link_desc, link_http, post_text, post_html, d, )
            
            #list_item_name=str(h[0]).zfill(3)
            
            #log(str(i)+"  score:"+ str(h[0]).zfill(5)+" desc["+ h[1] +']|text:['+ h[3]+']' +h[2] + '  videoID['+videoID+']' + 'playable:'+ setProperty_IsPlayable )
            #log( h[4] + ' -- videoID['+videoID+']' )
            
            #yt_thumb = ret_youtube_thumbnail(videoID,0)
            #log("thumbnailImage:"+yt_thumb)
            
            #log("sss:"+ supportedPluginUrl )
            
            fl= re.compile('\[(.*?)\]\(.*?\)',re.IGNORECASE) #match '[...](...)' with a capture group inside the []'s as capturegroup1
            result = fl.sub(r"[B]\1[/B]", h[3])              #replace the match with [B] [/B] with capturegroup1 in the middle of the [B]'s
            
            #helps the the textbox control treat [url description] and (url) as separate words. so that tehy can be separated into 2 lines 
            result=result.replace('](', '] (')
            result=markdown_to_bbcode(result)
            #log(result)

            liz=xbmcgui.ListItem(label=     "[COLOR greenyellow]*"+     list_title+"[%s] %s"%(hoster, result.replace('\n',' ')[0:100])  + "[/COLOR]", 
                                 label2="",
                                 iconImage="DefaultVideo.png", 
                                 thumbnailImage=thumb_url,
                                 path=DirectoryItem_url)
            if poster_url:
                thumb_url=poster_url
                
            if thumb_url: pass
            else: thumb_url="DefaultVideo.png"

            
            liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": result, "studio": hoster, "votes": str(h[0]), "director": author } )
            liz.setArt({"thumb": thumb_url, "poster":thumb_url, "banner":thumb_url, "fanart":thumb_url, "landscape":thumb_url   })

            liz.setProperty('IsPlayable', setProperty_IsPlayable)
            liz.setProperty('url', DirectoryItem_url)  #<-- needed by the xml gui skin
            liz.setPath(DirectoryItem_url) 

            directory_items.append( (DirectoryItem_url, liz, isFolder,) )
            #xbmcplugin.addDirectoryItem(handle=pluginhandle,url=DirectoryItem_url,listitem=liz,isFolder=isFolder)
        else:
            #this section are for comments that have no links or unsupported links
            if not ShowOnlyCommentsWithlink:
                result=h[3].replace('](', '] (')
                result=markdown_to_bbcode(result)
                liz=xbmcgui.ListItem(label=list_title + desc100 , 
                                     label2="",
                                     iconImage="", 
                                     thumbnailImage="")
                liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": result, "studio": hoster, "votes": str(h[0]), "director": author } )
                liz.setProperty('IsPlayable', 'false')
                
                directory_items.append( ("", liz, False,) )
                #xbmcplugin.addDirectoryItem(handle=pluginhandle,url="",listitem=liz,isFolder=False)
            
            #END section are for comments that have no links or unsupported links

    #for di in directory_items:
    #    log( str(di) )
    
    log('  comments_view id=%s' %comments_viewMode)

    #xbmcplugin.setContent(pluginhandle, "mixed")  #in estuary, mixed have limited view id's available. it has widelist which is nice for comments but we'll just stick with 'movies'
    xbmcplugin.setContent(pluginhandle, "movies")    #files, songs, artists, albums, movies, tvshows, episodes, musicvideos 
    xbmcplugin.addDirectoryItems(handle=pluginhandle, items=directory_items )
    xbmcplugin.endOfDirectory(pluginhandle)

    if comments_viewMode:
        xbmc.executebuiltin('Container.SetViewMode(%s)' %comments_viewMode)


harvest=[]
def r_linkHunter(json_node,d=0):
    from resources.domains import url_is_supported
    #recursive function to harvest stuff from the reddit comments json reply
    prog = re.compile('<a href=[\'"]?([^\'" >]+)[\'"]>(.*?)</a>')   
    for e in json_node:
        link_desc=""
        link_http=""
        author=""
        created_utc=""
        if e['kind']=='t1':     #'t1' for comments   'more' for more comments (not supported)
        
            #log("replyid:"+str(d)+" "+e['data']['id'])
            body=e['data']['body'].encode('utf-8')
    
            #log("reply:"+str(d)+" "+body.replace('\n','')[0:80])
            
            try: replies=e['data']['replies']['data']['children']
            except: replies=""
            
            try: score=e['data']['score']
            except: score=0
            
            try: post_text=cleanTitle( e['data']['body'].encode('utf-8') )
            except: post_text=""
            post_text=post_text.replace("\n\n","\n")
            
            try: post_html=cleanTitle( e['data']['body_html'].encode('utf-8') )
            except: post_html=""
    
            try: created_utc=e['data']['created_utc']
            except: created_utc=""
    
            try: author=e['data']['author'].encode('utf-8')
            except: author=""
    
            #i initially tried to search for [link description](https:www.yhotuve.com/...) in the post_text but some posts do not follow this convention
            #prog = re.compile('\[(.*?)\]\((https?:\/\/.*?)\)')   
            #result = prog.findall(post_text)
            
            result = prog.findall(post_html)
            if result:
                #store the post by itself and then a separate one for each link.
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )
  
                for link_http,link_desc in result:
                    if url_is_supported(link_http) :   
                        #store an entry for every supported link. 
                        harvest.append((score, link_desc, link_http, link_desc, post_html, d, "t1",author,created_utc,)   )    
            else:
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )    
    
            d+=1 #d tells us how deep is the comment in
            r_linkHunter(replies,d)   
            d-=1         

        if e['kind']=='t3':     #'t3' for post text (a description of the post)
            #log(str(e))
            #log("replyid:"+str(d)+" "+e['data']['id'])
            try: score=e['data']['score']
            except: score=0

            try: self_text=cleanTitle( e['data']['selftext'].encode('utf-8') )
            except: self_text=""
            
            try: self_text_html=cleanTitle( e['data']['selftext_html'].encode('utf-8') )
            except: self_text_html=""

            result = prog.findall(self_text_html)
            if len(result) > 0 :
                harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",author,created_utc, )   )
                 
                for link_http,link_desc in result:
                    if url_is_supported(link_http) : 
                        harvest.append((score, link_desc, link_http, link_desc, self_text_html, d, "t3",author,created_utc, )   )
            else:
                if len(self_text) > 0: #don't post an empty titles
                    harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",author,created_utc,)   )    
            


#MODE listImgurAlbum
def listImgurAlbum(album_url, name, type):
    #log("listImgurAlbum")
    from resources.domains import ClassImgur
    #album_url="http://imgur.com/a/fsjam"
    ci=ClassImgur()
        
    dictlist=ci.ret_album_list(album_url)
    display_album_from(dictlist, name)

def display_album_from(dictlist, album_name):
    from resources.domains import make_addon_url_from
    #this function is called by listImgurAlbum and playTumblr
    #NOTE: the directoryItem calling this needs isFolder=True or you'll get handle -1  error

#works on kodi 16.1 but doesn't load images on kodi 17.

#     ui = ssGUI('tbp_main.xml' , addon_path)
#     items=[]
#     
#     for d in dictlist:
#         #hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, IsPlayable=make_addon_url_from(d['DirectoryItem_url'],False)
#         items.append({'pic': d['DirectoryItem_url'] ,'description': d['li_label'], 'title' :  d['li_label2'] })
#     
#     ui.items=items
#     ui.album_name=album_name
#     ui.doModal()
#     del ui
#  
#     return
    directory_items=[]
    label=""
    
    for idx, d in enumerate(dictlist):
        #log('li_label:'+d['li_label'] + "  pluginhandle:"+ str(pluginhandle))
        ti=d['li_thumbnailImage']
        
        #most of the time, the image does not have a title. it looks so lonely on the listitem, we just put a number on it.    
        label = d['li_label2'] if d['li_label2'] else str(idx+1).zfill(2)
            
        liz=xbmcgui.ListItem(label=label, 
                             label2=d['li_label2'],
                             iconImage=d['li_iconImage'],
                             thumbnailImage=ti)

        #classImgur puts the media_url into  d['DirectoryItem_url']  no modification.
        #we modify it here...
        #url_for_DirectoryItem = sys.argv[0]+"?url="+ urllib.quote_plus(d['DirectoryItem_url']) +"&mode=playSlideshow"
        hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, IsPlayable=make_addon_url_from(d['DirectoryItem_url'],False)
        if poster_url=="": poster_url=ti
        
        
        liz.setInfo( type='video', infoLabels= d['infoLabels'] ) #this tricks the skin to show the plot. where we stored the picture descriptions
        liz.setArt({"thumb": ti, "poster":poster_url, "banner":poster_url, "fanart":poster_url, "landscape":d['DirectoryItem_url']   })             


        directory_items.append( (DirectoryItem_url, liz, isFolder,) )

        #xbmcplugin.addDirectoryItem(handle=pluginhandle,url=DirectoryItem_url,listitem=liz)

    xbmcplugin.setContent(pluginhandle, "episodes")

    log( 'album_viewMode ' + album_viewMode )
    if album_viewMode=='0':
        pass
    else:
        xbmc.executebuiltin('Container.SetViewMode('+album_viewMode+')')

    xbmcplugin.addDirectoryItems(handle=pluginhandle, items=directory_items )
    xbmcplugin.endOfDirectory(pluginhandle)

 
def listTumblrAlbum(t_url, name, type):    
    from resources.domains import ClassTumblr
    log("listTumblrAlbum:"+t_url)
    t=ClassTumblr(t_url)
    
    media_url, media_type =t.get_playable_url(t_url, True)
    #log('  ' + str(media_url))
    
    if media_type=='album':
        display_album_from( media_url, name )
    else:
        log("  listTumblrAlbum can't process " + media_type)    


def playVineVideo(vine_url, name, type):
    from resources.domains import ClassVine
    #log('playVineVideo')
    
    v=ClassVine(vine_url)
    #vine_stream_url='https://v.cdn.vine.co/r/videos/38B4A9174D1177703702723739648_37968e655a0.1.5.1461921223578533188.mp4'
    vine_stream_url=v.get_playable_url(vine_url, True)    #instead of querying vine(for the .mp4 link) for each item when listing the directory item(addLink()). we do that query here. better have the delay here than for each item when listing the directory item 
    
    if vine_stream_url:
        playVideo(vine_stream_url, name, type)
    else:
        #media_status=v.whats_wrong()
        xbmc.executebuiltin('XBMC.Notification("Vine","%s")' % 'media_status'  )

    #xbmc.executebuiltin("PlayerControl('repeatOne')")  #how do i make this video play again? 

def playVidmeVideo(vidme_url, name, type):
    from resources.domains import ClassVidme
    log('playVidmeVideo')
    v=ClassVidme(vidme_url)
    vidme_stream_url=v.get_playable_url(vidme_url, True)
    if vidme_stream_url:
        playVideo(vidme_stream_url, name, type)
    else:
        media_status=v.whats_wrong()
        xbmc.executebuiltin('XBMC.Notification("Vidme","%s")' % media_status  )
        
def playStreamable(media_url, name, type):
    from resources.domains import ClassStreamable
    log('playStreamable '+ media_url)
    
    s=ClassStreamable(media_url)
    playable_url=s.get_playable_url(media_url, True)

    if playable_url:
        playVideo(playable_url, name, type)
    else:
        #media_status=s.whats_wrong()  #streamable does not tell us if access to video is denied beforehand
        xbmc.executebuiltin('XBMC.Notification("Streamable","%s")' % "Access Denied"  )
    
def playInstagram(media_url, name, type):
    from resources.domains import ClassInstagram
    log('playInstagram '+ media_url)
    #instagram video handled by ytdl. links that reddit says is image are handled here.
    i=ClassInstagram( media_url )
    image_url=i.get_playable_url(media_url, False)
    
    playSlideshow(image_url,"Instagram","")

#MODE playLiveLeakVideo       - name, type not used
def playLiveLeakVideo(id, name, type):
    playVideo(getLiveLeakStreamUrl(id), name, type)

def playFlickr(flickr_url, name, type):
    from resources.domains import ClassFlickr
    log('play flickr '+ flickr_url)
    f=ClassFlickr( flickr_url )

    media_url, media_type =f.get_playable_url(flickr_url, False)
    if media_type=='album':
        display_album_from( media_url, name )
    else:
        playSlideshow(media_url,"Flickr","")
        #log("  listTumblrAlbum can't process " + media_type)    
    
#MODE downloadLiveLeakVideo       - name, type not used
def downloadLiveLeakVideo(id, name, type):
    downloader = SimpleDownloader.SimpleDownloader()
    content = opener.open("http://www.liveleak.com/view?i="+id).read()
    match = re.compile('<title>LiveLeak.com - (.+?)</title>', re.DOTALL).findall(content)
    global ll_downDir
    while not ll_downDir:
        xbmc.executebuiltin('XBMC.Notification(Download:,Liveleak '+translation(30186)+'!,5000)')
        addon.openSettings()
        ll_downDir = addon.getSetting("ll_downDir")
    url = getLiveLeakStreamUrl(id)
    filename = ""
    try:
        filename = (''.join(c for c in unicode(match[0], 'utf-8') if c not in '/\\:?"*|<>')).strip()
    except:
        filename = id
    filename+=".mp4"
    if not os.path.exists(os.path.join(ll_downDir, filename)):
        params = { "url": url, "download_path": ll_downDir }
        downloader.download(filename, params)
    else:
        xbmc.executebuiltin('XBMC.Notification(Download:,'+translation(30185)+'!,5000)')

#MODE queueVideo       -type not used
def queueVideo(url, name, type):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)

#MODE addToFavs         -name not used
def addToFavs(url, name, subreddit):
    file = os.path.join(addonUserDataFolder, subreddit+".fav")
    if os.path.exists(file):
        fh = open(file, 'r')
        content = fh.read()
        fh.close()
        if url not in content:
            fh = open(file, 'w')
            fh.write(content.replace("</favourites>", "    "+url.replace("\n","<br>")+"\n</favourites>"))
            fh.close()
    else:
        fh = open(file, 'a')
        fh.write("<favourites>\n    "+url.replace("\n","<br>")+"\n</favourites>")
        fh.close()

#MODE removeFromFavs      -name not used
def removeFromFavs(url, name, subreddit):
    file = os.path.join(addonUserDataFolder, subreddit+".fav")
    fh = open(file, 'r')
    content = fh.read()
    fh.close()
    fh = open(file, 'w')
    fh.write(content.replace("    "+url.replace("\n","<br>")+"\n", ""))
    fh.close()
    xbmc.executebuiltin("Container.Refresh")

#searchReddits      --url, name, type not used
def searchReddits(url, name, type):
    keyboard = xbmc.Keyboard('sort=new&t=week&q=', translation(30005))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():  
        
        #search_string = urllib.quote_plus(keyboard.getText().replace(" ", "+"))
        search_string = keyboard.getText().replace(" ", "+")
        
        #sites_filter = site_filter_for_reddit_search()
        url = urlMain +"/search.json?" +search_string    #+ '+' + nsfw  # + sites_filter skip the sites filter

        listVideos(url, name, "")
        

def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')

def cleanTitle(title):
        title = title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"")
        return title.strip()
#MODE openSettings     --name, type not used
def openSettings(id, name,type):
    if id=="youtube":
        addonY = xbmcaddon.Addon(id='plugin.video.youtube')
    elif id=="vimeo":
        addonY = xbmcaddon.Addon(id='plugin.video.vimeo')
    elif id=="dailymotion":
        addonY = xbmcaddon.Addon(id='plugin.video.dailymotion_com')
    addonY.openSettings()
#MODE toggleNSFW     -- url, name, type not uised
def toggleNSFW(url, name, type):
#when you toggle the show nsfw in addon setting, the plugin is called and this function handles the dialog box
    if os.path.exists(nsfwFile):
        dialog = xbmcgui.Dialog()
        if dialog.yesno(translation(30187), translation(30189)):
            os.remove(nsfwFile)
    else:
        dialog = xbmcgui.Dialog()
        if dialog.yesno(translation(30188), translation(30190)+"\n"+translation(30191)):
            fh = open(nsfwFile, 'w')
            fh.write("")
            fh.close()

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

# def addFavLink(name, url, mode, iconimage, description, date, site, subreddit):
#     ok = True
#     liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
#     liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description, "Aired": date})
#     liz.setProperty('IsPlayable', 'true')
#     entries = []
#     entries.append((translation(30018), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(url)+'&name='+urllib.quote_plus(name)+')',))
#     favEntry = '<favourite name="'+name+'" url="'+url+'" description="'+description+'" thumb="'+iconimage+'" date="'+date+'" site="'+site+'" />'
#     entries.append((translation(30024), 'RunPlugin(plugin://'+addonID+'/?mode=removeFromFavs&url='+urllib.quote_plus(favEntry)+'&type='+urllib.quote_plus(subreddit)+')',))
#     if showBrowser and (osWin or osOsx or osLinux):
#         if osWin and browser_win==0:
#             entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.webbrowser/?url='+urllib.quote_plus(site)+'&mode=showSite&zoom='+browser_wb_zoom+'&stopPlayback=no&showPopups=no&showScrollbar=no)',))
#         else:
#             entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.chrome.launcher/?url='+urllib.quote_plus(site)+'&mode=showSite)',))
#     liz.addContextMenuItems(entries)
#     ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=liz)
#     return ok

#addDir(subreddit, subreddit.lower(), next_mode, "")
def addDir(name, url, mode, iconimage, type="", listitem_infolabel=None, label2=""):
    #adds a list entry
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type)
    #log('addDir='+u)
    ok = True
    liz = xbmcgui.ListItem(label=name, label2=label2, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    
    if listitem_infolabel==None:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    else:
        liz.setInfo(type="Video", infoLabels=listitem_infolabel)
        
    
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def addDirR(name, url, mode, iconimage, type="", listitem_infolabel=None, file_entry=""):
    #addDir with a remove subreddit context menu
    #alias is the text for the listitem that is presented to the user
    #file_entryis the actual string(containing alias & viewid) that is saved in the "subreddit" file
    
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type)
    #log('addDirR='+u)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)

    if listitem_infolabel==None:
        #liz.setInfo(type="Video", infoLabels={"Title": name})
        liz.setInfo(type="Video", infoLabels={"Title": name})
    else:
        liz.setInfo(type="Video", infoLabels=listitem_infolabel)
        
    if file_entry:
        liz.setProperty("file_entry", file_entry)
    
    #liz.addContextMenuItems([(translation(30002), 'RunPlugin(plugin://'+addonID+'/?mode=removeSubreddit&url='+urllib.quote_plus(url)+')',)])
    liz.addContextMenuItems([(translation(30003), 'RunPlugin(plugin://'+addonID+'/?mode=editSubreddit&url='+urllib.quote_plus(file_entry)+')',)     ,
                             (translation(30002), 'RunPlugin(plugin://'+addonID+'/?mode=removeSubreddit&url='+urllib.quote_plus(file_entry)+')',)  
                             ])
    
    #log("handle="+sys.argv[1]+" url="+u+" ")
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def pretty_datediff(dt1, dt2):
    try:
        diff = dt1 - dt2
        
        sec_diff = diff.seconds
        day_diff = diff.days
    
        if day_diff < 0:
            return 'future'
    
        if day_diff == 0:
            if sec_diff < 10:
                return translation(30060)     #"just now"
            if sec_diff < 60:
                return str(sec_diff) + translation(30061)      #" secs ago"
            if sec_diff < 120:
                return translation(30062)     #"a min ago"
            if sec_diff < 3600:
                return str(sec_diff / 60) + translation(30063) #" mins ago"
            if sec_diff < 7200:
                return translation(30064)     #"an hour ago"
            if sec_diff < 86400:
                return str(sec_diff / 3600) + translation(30065) #" hrs ago"
        if day_diff == 1:
            return translation(30066)         #"Yesterday"
        if day_diff < 7:
            return str(day_diff) + translation(30067)      #" days ago"
        if day_diff < 31:
            return str(day_diff / 7) + translation(30068)  #" wks ago"
        if day_diff < 365:
            return str(day_diff / 30) + translation(30069) #" months ago"
        return str(day_diff / 365) + translation(30070)    #" years ago"
    except:
        pass




def playSlideshow(url, name, type):
    #url='d:\\aa\\lego_fusion_beach1.jpg'

    #download_file=download_file.replace(r"\\",r"\\\\")

    #addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
    #i cannot get this to work reliably...
    #xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":"1","method":"Player.Open","params":{"item":{"directory":"%s"}}}' %(addonUserDataFolder) )
    #xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":"1","method":"Player.Open","params":{"item":{"directory":"%s"}}}' %(r"d:\\aa\\") )
    #xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":"1","method":"Player.Open","params":{"item":{"file":"%s"}}}' %(download_file) )
    #return

    #whis won't work if addon is a video add-on
    #xbmc.executebuiltin("XBMC.SlideShow(" + SlideshowCacheFolder + ")")

    return

def reddit_request( url ):
    #log( "  reddit_request " + url )
    
    #if there is a refresh_token, we use oauth.reddit.com instead of www.reddit.com
    if reddit_refresh_token:
        url=url.replace('www.reddit.com','oauth.reddit.com' )
        log( "  replaced reqst." + url + " + access token=" + reddit_access_token)
        
    req = urllib2.Request(url)

    #req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
    req.add_header('User-Agent', userAgent)   #userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"
    
    #if there is a refresh_token, add the access token to the header
    if reddit_refresh_token:
        req.add_header('Authorization','bearer '+ reddit_access_token )
    
    try:
        page = urllib2.urlopen(req)
        response=page.read();page.close()
        #log( response )
        return response

    except urllib2.HTTPError, err:
        if err.code in [403,401]:  #401 Unauthorized, 403 forbidden. access tokens expire in 1 hour. maybe we just need to refresh it
            log("    attempting to get new access token")
            if reddit_get_access_token():
                log("      Success: new access token "+ reddit_access_token)
                req.add_header('Authorization','bearer '+ reddit_access_token )
                try:
                    
                    log("      2nd attempt:"+ url)
                    page = urllib2.urlopen(req)   #it has to be https:// not http://
                    response=page.read();page.close()
                    return response
                
                except urllib2.HTTPError, err:
                    xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, url)  )
                    log( err.reason )         
                except urllib2.URLError, err:
                    log( err.reason ) 
            else:
                log( "*** failed to get new access token - don't know what to do " )

            
        xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, url)  )
        log( err.reason )         
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, url)  )
        log( err.reason ) 
    
        
def reddit_get_refresh_token(url, name, type):
    #this function gets a refresh_token from reddit and keep it in our addon. this refresh_token is used to get 1-hour access tokens.
    #  getting a refresh_token is a one-time step
    
    #1st: use any webbrowser to  
    #  https://www.reddit.com/api/v1/authorize?client_id=hXEx62LGqxLj8w&response_type=code&state=RS&redirect_uri=http://localhost:8090/&duration=permanent&scope=read,mysubreddits
    #2nd: click allow and copy the code provided after reddit redirects the user 
    #  save this code in add-on settings.  A one-time use code that may be exchanged for a bearer token.
    code = addon.getSetting("reddit_code")
    
    if reddit_refresh_token and code:
        dialog = xbmcgui.Dialog()
        if dialog.yesno("Replace reddit refresh token", "You already have a refresh token.", "You only need to get this once.", "Are you sure you want to replace it?" ):
            pass
        else:
            return
        
    try:
        log( "Requesting a reddit permanent token with code=" + code )
 
        req = urllib2.Request('https://www.reddit.com/api/v1/access_token')
         
        #http://stackoverflow.com/questions/6348499/making-a-post-call-instead-of-get-using-urllib2
        data = urllib.urlencode({'grant_type'  : 'authorization_code'
                                ,'code'        : code                     #'woX9CDSuw7XBg1MiDUnTXXQd0e4'
                                ,'redirect_uri': reddit_redirect_uri})    #http://localhost:8090/
 
        #http://stackoverflow.com/questions/2407126/python-urllib2-basic-auth-problem
        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')  
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', userAgent)
         
        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()
        log( response )

        #response='{"access_token": "xmOMpbJc9RWqjPS46FPcgyD_CKc", "token_type": "bearer", "expires_in": 3600, "refresh_token": "56706164-ZZiEqtAhahg9BkpINvrBPQJhZL4", "scope": "identity read"}'
        status=reddit_set_addon_setting_from_response(response)
        
        if status=='ok':
            r1="Click 'OK' when done"
            r2="Settings will not be saved"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( r1, r2)  )
        else:
            r2="Requesting a reddit permanent token"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( status, r2)  )     
            

#    This is a 2nd option reddit oauth. user needs to request access token every hour
#         #user enters this on their webbrowser. note that there is no duration=permanent response_type=token instead of code 
#         request_url='https://www.reddit.com/api/v1/authorize?client_id=hXEx62LGqxLj8w&response_type=token&state=RS&redirect_uri=http://localhost:8090/&scope=read,identity'
#         #click on "Allow"
#         #copy the redirect url code    #enters it on settings. e.g.: LVQu8vitbEXfMPcK1sGlVVQZEpM
# 
#         #u='https://oauth.reddit.com/new.json'
#         u='https://oauth.reddit.com//api/v1/me.json'
# 
#         req = urllib2.Request(u)
#         #req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
#         req.add_header('User-Agent', userAgent)
#         req.add_header('Authorization','bearer LVQu8vitbEXfMPcK1sGlVVQZEpM')
#         page = read,identity.urlopen(req)
#         response=page.read();page.close()
    
    except urllib2.HTTPError, err:
        xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, u)  )
        log( err.reason )         
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        log( err.reason ) 
    
def reddit_get_access_token(url="", name="", type=""):
    try:
        log( "Requesting a reddit 1-hour token" )
 
        req = urllib2.Request('https://www.reddit.com/api/v1/access_token')
          
        #http://stackoverflow.com/questions/6348499/making-a-post-call-instead-of-get-using-urllib2
        data = urllib.urlencode({'grant_type'    : 'refresh_token'
                                ,'refresh_token' : reddit_refresh_token })                    #'woX9CDSuw7XBg1MiDUnTXXQd0e4'
  
        #http://stackoverflow.com/questions/2407126/python-urllib2-basic-auth-problem
        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')  
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', userAgent)
          
        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()
        #log( response )

        #response='{"access_token": "lZN8p1QABSr7iJlfPjIW0-4vBLM", "token_type": "bearer", "device_id": "None", "expires_in": 3600, "scope": "identity read"}'
        status=reddit_set_addon_setting_from_response(response)
        
        if status=='ok':
            #log( '    ok new access token '+ reddit_access_token )
            #r1="Click 'OK' when done"
            #r2="Settings will not be saved"
            #xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( r1, r2)  )
            return True
        else:
            r2="Requesting 1-hour token"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( status, r2)  )     
    
    except urllib2.HTTPError, err:
        xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, req.get_full_url())  )
        log( err.reason )         
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        log( err.reason )
    
    return False 

def reddit_set_addon_setting_from_response(response):
    global reddit_access_token    #specify "global" if you wanto to change the value of a global variable
    global reddit_refresh_token
    try:
        response = json.loads(response.replace('\\"', '\''))
        log( json.dumps(response, indent=4) )
        
        if 'error' in response:
            #Error                      Cause                                                                Resolution
            #401 response               Client credentials sent as HTTP Basic Authorization were invalid     Verify that you are properly sending HTTP Basic Authorization headers and that your credentials are correct
            #unsupported_grant_type     grant_type parameter was invalid or Http Content type was not set correctly     Verify that the grant_type sent is supported and make sure the content type of the http message is set to application/x-www-form-urlencoded
            #NO_TEXT for field code     You didn't include the code parameter                                Include the code parameter in the POST data
            #invalid_grant              The code has expired or already been used                            Ensure that you are not attempting to re-use old codes - they are one time use.            
            return response['error'] 
        else:
            if 'refresh_token' in response:  #refresh_token only returned when getting reddit_get_refresh_token. it is a one-time step
                reddit_refresh_token = response['refresh_token']
                addon.setSetting('reddit_refresh_token', reddit_refresh_token)
            
            reddit_access_token = response['access_token']
            addon.setSetting('reddit_access_token', reddit_access_token)
            #log( '    new access token '+ reddit_access_token )
            
            addon.setSetting('reddit_access_token_scope', response['scope'])
            
            unix_time_now = int(time.time())
            unix_time_now += int( response['expires_in'] )
            addon.setSetting('reddit_access_token_expires', convert_date(unix_time_now))
            
    except Exception as e:
        log("  parsing reddit token response EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )    
        return str(e)
    
    return "ok"

def reddit_revoke_refresh_token(url, name, type):    
    global reddit_access_token    #specify "global" if you wanto to change the value of a global variable
    global reddit_refresh_token
    try:
        log( "Revoking refresh token " )
 
        req = urllib2.Request('https://www.reddit.com/api/v1/revoke_token')
          
        data = urllib.urlencode({'token'          : reddit_refresh_token
                                ,'token_type_hint': 'refresh_token'       }) 
  
        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')  
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', userAgent)
          
        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()
        
        #no response for success. 
        log( "response:" + response )

        #response = json.loads(response.replace('\\"', '\''))
        #log( json.dumps(response, indent=4) )

        addon.setSetting('reddit_refresh_token', "")
        addon.setSetting('reddit_access_token', "")
        addon.setSetting('reddit_access_token_scope', "")
        addon.setSetting('reddit_access_token_expires', "")
        reddit_refresh_token=""
        reddit_access_token=""
        
        r2="Revoking refresh token"
        xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( 'Token revoked', r2)  )
    
    except urllib2.HTTPError, err:
        xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, req.get_full_url() )  )
        log( "http error:" + err.reason )         
    except Exception as e:
        xbmc.executebuiltin('XBMC.Notification("%s", "%s" )' %( str(e), 'Revoking refresh token' )  )
        log("  Revoking refresh token EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )    
    

def markdown_to_bbcode(s):
    #https://gist.github.com/sma/1513929
    links = {}
    codes = []
    try:
        #def gather_link(m):
        #    links[m.group(1)]=m.group(2); return ""
        #def replace_link(m):
        #    return "[url=%s]%s[/url]" % (links[m.group(2) or m.group(1)], m.group(1))
        #def gather_code(m):
        #    codes.append(m.group(3)); return "[code=%d]" % len(codes)
        #def replace_code(m):
        #    return "%s" % codes[int(m.group(1)) - 1]
        
        def translate(p="%s", g=1):
            def inline(m):
                s = m.group(g)
                #s = re.sub(r"(`+)(\s*)(.*?)\2\1", gather_code, s)
                #s = re.sub(r"\[(.*?)\]\[(.*?)\]", replace_link, s)
                #s = re.sub(r"\[(.*?)\]\((.*?)\)", "[url=\\2]\\1[/url]", s)
                #s = re.sub(r"<(https?:\S+)>", "[url=\\1]\\1[/url]", s)
                s = re.sub(r"\B([*_]{2})\b(.+?)\1\B", "[B]\\2[/B]", s)
                s = re.sub(r"\B([*_])\b(.+?)\1\B", "[I]\\2[/I]", s)
                return p % s
            return inline
        
        #s = re.sub(r"(?m)^\[(.*?)]:\s*(\S+).*$", gather_link, s)
        #s = re.sub(r"(?m)^    (.*)$", "~[code]\\1[/code]", s)
        #s = re.sub(r"(?m)^(\S.*)\n=+\s*$", translate("~[size=200][b]%s[/b][/size]"), s)
        #s = re.sub(r"(?m)^(\S.*)\n-+\s*$", translate("~[size=100][b]%s[/b][/size]"), s)
        s = re.sub(r"(?m)^#{4,6}\s*(.*?)\s*#*$", translate("[LIGHT]%s[/LIGHT]"), s)       #heading4-6 becomed light
        s = re.sub(r"(?m)^#{1,3}\s*(.*?)\s*#*$", translate("[B]%s[/B]"), s)               #heading1-3 becomes bold
        #s = re.sub(r"(?m)^##\s+(.*?)\s*#*$", translate("[B]%s[/B]"), s)
        #s = re.sub(r"(?m)^###\s+(.*?)\s*#*$", translate("[B]%s[/B]"), s)
    
        s = re.sub(r"(?m)^>\s*(.*)$", translate("|%s"), s)                                #quotes  get pipe character beginning
        #s = re.sub(r"(?m)^[-+*]\s+(.*)$", translate("~[list]\n[*]%s\n[/list]"), s)
        #s = re.sub(r"(?m)^\d+\.\s+(.*)$", translate("~[list=1]\n[*]%s\n[/list]"), s)
        s = re.sub(r"(?m)^((?!~).*)$", translate(), s)
        #s = re.sub(r"(?m)^~\[", "[", s)
        #s = re.sub(r"\[/code]\n\[code(=.*?)?]", "\n", s)
        #s = re.sub(r"\[/quote]\n\[quote]", "\n", s)
        #s = re.sub(r"\[/list]\n\[list(=1)?]\n", "", s)
        #s = re.sub(r"(?m)\[code=(\d+)]", replace_code, s)
        
        return s
    except:
        return s
    
DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')

def convert_date(stamp):
    #http://forum.kodi.tv/showthread.php?tid=221119
    date_time = time.localtime(stamp)
    if DATEFORMAT[1] == 'd':
        localdate = time.strftime('%d-%m-%Y', date_time)
    elif DATEFORMAT[1] == 'm':
        localdate = time.strftime('%m-%d-%Y', date_time)
    else:
        localdate = time.strftime('%Y-%m-%d', date_time)
    if TIMEFORMAT != '/':
        localtime = time.strftime('%I:%M%p', date_time)
    else:
        localtime = time.strftime('%H:%M', date_time)
    return localtime + '  ' + localdate

    
def downloadurl( source_url, destination=""):
    try:
        filename,ext=parse_filename_and_ext_from_url(source_url)
        if destination=="":
            urllib.urlretrieve(source_url, filename+"."+ext)
        else:
            urllib.urlretrieve(source_url, destination)
        
    except:
        log("download ["+source_url+"] failed")

def log(message, level=xbmc.LOGNOTICE):
    xbmc.log("reddit_viewer:"+message, level=level)



if __name__ == '__main__':
    dbPath = getDbPath()
    if dbPath:
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
    
    params = parameters_string_to_dict(sys.argv[2])
    mode   = urllib.unquote_plus(params.get('mode', ''))
    url    = urllib.unquote_plus(params.get('url', ''))
    typez  = urllib.unquote_plus(params.get('type', '')) #type is a python function, try not to use a variable name same as function
    name   = urllib.unquote_plus(params.get('name', ''))
    #xbmc supplies this additional parameter if our <provides> in addon.xml has more than one entry e.g.: <provides>video image</provides>
    #xbmc only does when the add-on is started. we have to pass it along on subsequent calls   
    # if our plugin is called as a pictures add-on, value is 'image'. 'video' for video 
    #content_type=urllib.unquote_plus(params.get('content_type', ''))   
    #ctp = "&content_type="+content_type   #for the lazy
    #log("content_type:"+content_type)
    
    if HideImagePostsOnVideo: # and content_type=='video':
        setting_hide_images=True
    #log("HideImagePostsOnVideo:"+str(HideImagePostsOnVideo)+"  setting_hide_images:"+str(setting_hide_images))
    # log("params="+sys.argv[2]+"  ")
#     log("----------------------")
#     log("params="+ str(params))
#     log("mode="+ mode)
#     log("type="+ typez) 
#     log("name="+ name)
#     log("url="+  url)
#     log("pluginhandle:" + str(pluginhandle) )
#     log("-----------------------")
    
    if mode=='':mode='index'  #default mode is to list start page (index)
    #plugin_modes holds the mode string and the function that will be called given the mode
    plugin_modes = {'index'                 : index
                    ,'listVideos'           : listVideos
                    ,'playVideo'            : playVideo           
                    ,'playLiveLeakVideo'    : playLiveLeakVideo  
                    ,'playGfycatVideo'      : playGfycatVideo   
                    ,'downloadLiveLeakVideo': downloadLiveLeakVideo
                    ,'addSubreddit'         : addSubreddit         
                    ,'editSubreddit'        : editSubreddit         
                    ,'removeSubreddit'      : removeSubreddit      
                    ,'autoPlay'             : autoPlay       
                    ,'queueVideo'           : queueVideo     
                    ,'addToFavs'            : addToFavs      
                    ,'removeFromFavs'       : removeFromFavs
                    ,'searchReddits'        : searchReddits          
                    ,'openSettings'         : openSettings        
                    ,'toggleNSFW'           : toggleNSFW 
                    ,'listImgurAlbum'       : listImgurAlbum    
                    ,'playSlideshow'        : playSlideshow
                    ,'listLinksInComment'   : listLinksInComment
                    ,'playVineVideo'        : playVineVideo
                    ,'playYTDLVideo'        : playYTDLVideo
                    ,'playVidmeVideo'       : playVidmeVideo
                    ,'listTumblrAlbum'      : listTumblrAlbum
                    ,'playStreamable'       : playStreamable
                    ,'playInstagram'        : playInstagram
                    ,'playFlickr'           : playFlickr
                    ,'listFlickrAlbum'      : playFlickr 
                    ,'get_refresh_token'    : reddit_get_refresh_token
                    ,'get_access_token'     : reddit_get_access_token
                    ,'revoke_refresh_token' : reddit_revoke_refresh_token
                    }
    #whenever a list item is clicked, this part handles it.
    plugin_modes[mode](url,name,typez)

#    usually this plugin is called by a list item constructed like the one below
#         u = sys.argv[0]+"?url=&mode=addSubreddit&type="   #these are the arguments that is sent to our plugin and processed by plugin_modes
#         liz = xbmcgui.ListItem("Add Subreddit",label2="aaa", iconImage="DefaultFolder.png", thumbnailImage="")
#         liz.setInfo(type="Video", infoLabels={"Title": "aaaaaaa", "Plot": "description", "Aired": "daate", "mpaa": "aa"})
#         xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)



'''
github notes:  (6-27-2016)

# Clone your fork of kodi's repo into the current directory in terminal
git clone git@github.com:gedisony/repo-plugins.git repo-plugins

# Navigate to the newly cloned directory
cd repo-plugins

# Assign the original repo to a remote called "upstream"
git remote add upstream https://github.com/xbmc/repo-plugins.git

#
git checkout jarvis


If you cloned a while ago, get the latest changes from upstream:

# Fetch upstream changes
git fetch upstream
# Make sure you are on your 'master' branch
git checkout master
# Merge upstream changes
git merge upstream/master

'master' is only used as example here. Please replace it with the correct branch you want to submit your add-on towards.
*** i think you need to use 'origin/jarvis' instead of 'master'



#Create a new branch to contain your new add-on or subsequent update:
git checkout -b <add-on-branch-name>                       <------while testing, i ended up naming the branch name as "add-on-branch-name"
#The branch name isn't really relevant however a good suggestion is to name it like the addon ID.


#Commit your changes in a single commit, or your pull request is unlikely to be merged into the main repository.
#Use git's interactive rebase feature to tidy up your commits before making them public. The commit for your add-on should have the following naming convention as the following example:
*** don't know what it means "single commit" (how to commit?) 
*** go to repo-plugins and copy the entire folder plugin.video.reddit_viewer-master
*** remove the "-master"  --> plugin.video.reddit_viewer
*** 
*** this is what i did:
$ git commit -m "[plugin.video.reddit_viewer] 2.7.1"
On branch add-on-branch-name
Untracked files:
        plugin.video.reddit_viewer/                <------ error message

nothing added to commit but untracked files present

edipc@DESKTOP-5C55U1P MINGW64 ~/kodi stuff/repo-plugins (add-on-branch-name)
$ git add .    <---- did this to fix the error.

$ git commit -m "[plugin.video.reddit_viewer] 2.7.1"  <------- this will now work


#Push your topic branch up to your fork:

git push origin add-on-branch-name

#Open a pull request with a clear title and description.

*** on browser: click on pull request
upper left : base fork: xbmc/repo-plugins         base:    jarvis
upper right: head fork: gedisony/repo-plugins     compare: add-on-branch-name
*** the clear title till be [plugin.video.reddit_viewer] 2.7.1
*** (don't know what description) left it as blank

*** sent pull request on 6/27/2016

'''
'''
new github notes (7/1/2016) special thanks to Skipmode A1  http://forum.kodi.tv/showthread.php?tid=280882&pid=2365444#pid2365444

rem For a total restart: Delete repo-plugins from your repo on Github
rem For a total restart: Fork the official kodi repo to your repo on Github
rem Deleting C:\Kodi_stuff\repo-plugins and Cloning the kodi repo from your github to your pc
rem Ctrl-C to abort!!!!
pause
rmdir /s /q C:\Kodi_stuff\repo-plugins
cd C:\Kodi_stuff\
c:
rem Cloning the kodi repo from your github to your pc
git clone git@github.com:gedisony/repo-plugins.git repo-plugins
cd C:\Kodi_stuff\repo-plugins

rem Assign the official kodi repo to a remote called "upstream"
git remote add upstream https://github.com/xbmc/repo-plugins.git

rem Add the addon in your github as a remote
git remote add plugin.video.reddit_viewer git@github.com:gedisony/plugin.video.reddit_viewer

rem Fetch your addon from your github
git fetch plugin.video.reddit_viewer

rem Make a branch for your addon and go to that branch
git checkout -b branch_2.7.2 plugin.video.reddit_viewer/master

rem go to the jarvis branch
git checkout jarvis

rem delete the old version of the addon
git rm .\%1\ -r

rem get the new version of the addon from the branch you created
git read-tree --prefix=plugin.video.reddit_viewer/ -u branch_2.7.2

rem force remove .git files (not used for me)
git rm -f C:\Kodi_stuff\repo-plugins\plugin.video.reddit_viewer\.gitattributes
git rm -f C:\Kodi_stuff\repo-plugins\plugin.video.reddit_viewer\.gitignore

rem show the differences
git diff --staged

rem Commit the changes
Git commit -m "[plugin.video.reddit_viewer] 2.7.2"

rem push the stuff to the jarvis branch in your github (if everything went ok): 
git push origin jarvis

*** on browser: click on pull request (similar to one above) 
'''