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
#import SimpleDownloader
import requests

# import shelve
# import shutil

import threading
from Queue import Queue, Empty



#this used to be a plugin. not that we're a script, we don't get free sys.argv's
#this import for the youtube_dl addon causes our addon to start slower. we'll import it when we need to playYTDLVideo
if len(sys.argv) > 1:
    a=['mode=playYTDLVideo','mode=autoPlay']
    if any(x in sys.argv[1] for x in a):
        import YDStreamExtractor      #note: you can't just add this import in code, you need to re-install the addon with <import addon="script.module.youtube.dl"        version="16.521.0"/> in addon.xml
      
#     if 'mode=playYTDLVideo' in sys.argv[1] :
#         import YDStreamExtractor      #note: you can't just add this import in code, you need to re-install the addon with <import addon="script.module.youtube.dl"        version="16.521.0"/> in addon.xml
else:
    pass 


#YDStreamExtractor.disableDASHVideo(True) #Kodi (XBMC) only plays the video for DASH streams, so you don't want these normally. Of course these are the only 1080p streams on YouTube
from urllib import urlencode
reload(sys)
sys.setdefaultencoding("utf-8")

addon         = xbmcaddon.Addon()
addonID       = addon.getAddonInfo('id')  #script.reddit.reader
addon_path    = addon.getAddonInfo('path')     #where the addon resides
profile_path  = addon.getAddonInfo('profile')   #where user settings are stored

WINDOW        = xbmcgui.Window(10000)
#technique borrowed from LazyTV. 
#  WINDOW is like a mailbox for passing data from caller to callee. 
#    e.g.: addLink() needs to pass "image description" to viewImage()

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
reddit_userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"
reddit_clientID      ="ZEbDJ5DUrguDMA"    
reddit_redirect_uri  ='http://localhost:8090/'   #specified when registering for a clientID
reddit_refresh_token =addon.getSetting("reddit_refresh_token")
reddit_access_token  =addon.getSetting("reddit_access_token") #1hour token

opener.addheaders = [('User-Agent', reddit_userAgent)]
#API requests with a bearer token should be made to https://oauth.reddit.com, NOT www.reddit.com.
urlMain = "https://www.reddit.com"


#filter           = addon.getSetting("filter") == "true"
#filterRating     = int(addon.getSetting("filterRating"))
#filterThreshold  = int(addon.getSetting("filterThreshold"))

# settings for automatically play videos
# showAll              = addon.getSetting("showAll") == "true"
# showUnwatched        = addon.getSetting("showUnwatched") == "true"
# showUnfinished       = addon.getSetting("showUnfinished") == "true"
# showAllNewest        = addon.getSetting("showAllNewest") == "true"
# showUnwatchedNewest  = addon.getSetting("showUnwatchedNewest") == "true"
# showUnfinishedNewest = addon.getSetting("showUnfinishedNewest") == "true"

default_frontpage    = addon.getSetting("default_frontpage") 
no_index_page        = addon.getSetting("no_index_page") == "true"

# viewMode             = str(addon.getSetting("viewMode"))
# comments_viewMode    = str(addon.getSetting("comments_viewMode"))
# album_viewMode       = str(addon.getSetting("album_viewMode"))

show_nsfw            = addon.getSetting("show_nsfw") == "true"
domain_filter        = addon.getSetting("domain_filter")
subreddit_filter     = addon.getSetting("subreddit_filter")
main_gui_skin        = addon.getSetting("main_gui_skin")

sitemsPerPage        = addon.getSetting("itemsPerPage")
try: itemsPerPage = int(sitemsPerPage)
except: itemsPerPage = 50    

itemsPerPage          = ["10", "25", "50", "75", "100"][itemsPerPage]
TitleAddtlInfo        = addon.getSetting("TitleAddtlInfo") == "true"   #Show additional post info on title</string>

#--- settings related to context menu "Show Comments"
CommentTreshold          = addon.getSetting("CommentTreshold") 
try: int_CommentTreshold = int(CommentTreshold)
except: int_CommentTreshold = -1000    #if CommentTreshold can't be converted to int, show all comments 

ll_qualiy  = int(addon.getSetting("ll_qualiy"))
ll_qualiy  = ["480p", "720p"][ll_qualiy]
ll_downDir = str(addon.getSetting("ll_downDir"))

istreamable_quality =int(addon.getSetting("streamable_quality"))  #values 0 or 1
streamable_quality  =["full", "mobile"][istreamable_quality]       #https://streamable.com/documentation

gfy_downDir = str(addon.getSetting("gfy_downDir"))

use_ytdl_for_unknown = addon.getSetting("use_ytdl_for_unknown") == "true" 
use_ytdl_for_unknown_in_comments= addon.getSetting("use_ytdl_for_unknown_in_comments") == "true"

addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
subredditsFile      = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits")
nsfwFile            = xbmc.translatePath("special://profile/addon_data/"+addonID+"/nsfw")

#ytdl_psites_file         = xbmc.translatePath(profile_path+"/ytdl_sites_porn")
default_ytdl_psites_file = xbmc.translatePath(  addon_path+"/resources/ytdl_sites_porn" )
#ytdl_sites_file          = xbmc.translatePath(profile_path+"/ytdl_sites")
default_ytdl_sites_file  = xbmc.translatePath(  addon_path+"/resources/ytdl_sites" )

#C:\Users\myusername\AppData\Roaming\Kodi\userdata\addon_data\plugin.video.reddit_viewer

#last slash at the end is important
SlideshowCacheFolder    = xbmc.translatePath("special://profile/addon_data/"+addonID+"/slideshowcache/") #will use this to cache images for slideshow 

if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)

if not os.path.isdir(SlideshowCacheFolder):
    os.mkdir(SlideshowCacheFolder)


if show_nsfw:
    nsfw = ""
else:
    nsfw = "nsfw:no+"

def log(message, level=xbmc.LOGNOTICE):
    xbmc.log("reddit_reader:"+message, level=level)


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
    
def manage_subreddits(subreddit, name, type):
    log('manage_subreddits(%s, %s, %s)' %(subreddit, name, type) )
    #this funciton is called by the listSubRedditGUI when user presses left button when on the subreddits list 
    
    #http://forum.kodi.tv/showthread.php?tid=148568
    dialog = xbmcgui.Dialog()
    #funcs = (        addSubreddit,        editSubreddit,        removeSubreddit,    )
    #elected_index = dialog.select(subreddit, ['add new subreddi', 'edit   subreddit', 'remove subreddit'])
    selected_index = dialog.select(subreddit, [translation(32001), translation(32003), translation(32002)])

    #the if statements below is not as elegant as autoselecting the func from funcs but more flexible in the case with add subreddit where we should not send a subreddit parameter
    #    func = funcs[selected_index]
    #     #assign item from funcs to func
    #    func(subreddit, name, type)    
    log('selected_index ' + str(selected_index))
    if selected_index == 0:       # 0->first item
        addSubreddit('','','')
        pass
    elif selected_index == 1:     # 1->second item
        editSubreddit(subreddit,'','')
        pass
    elif selected_index == 2:     # 2-> third item
        removeSubreddit(subreddit,'','')
        pass
    else:                         #-1 -> escape pressed or [cancel] 
        pass
    
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    #this is a hack to force the subreddit listing to refresh.
    #   the calling gui needs to close after calling this function 
    #   after we are done editing the subreddits file, we call index() (the start of program) again. 
    index("","","")

    
def addSubreddit(subreddit, name, type):
    from resources.lib.utils import this_is_a_multihub, format_multihub
    log( 'addSubreddit ' + subreddit)
    alreadyIn = False
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    
    if subreddit:
        for line in content:
            #log('line=['+line+']toadd=['+subreddit+']')
            if line.strip()==subreddit.strip():
                #log('  MATCH '+line+'='+subreddit)
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
    log( 'removeSubreddit ' + subreddit)
     
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
    from resources.lib.utils import this_is_a_multihub, format_multihub
    log( 'editSubreddit ' + subreddit)
     
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



def index(url,name,type):
    ## this is where the __main screen is created

    from resources.lib.guis import indexGui
    from resources.lib.utils import assemble_reddit_filter_string, create_default_subreddits
    li=[]

    #ui = cGUI('DialogSelect.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, id=55)
    #ui.show()
    #xbmc.sleep(2000)

#     log( "sys.argv[0]="+ sys.argv[0] ) #plugin://plugin.video.reddit_viewer/
#     log( "addonID=" + addonID )     #plugin.video.reddit_viewer
#     log( "path=" + addon.getAddonInfo('path') )
#     log( "profile=" + addon.getAddonInfo('profile') )

    #testing code
    #h="as asd [S]asdasd[/S] asdas "
    #log(markdown_to_bbcode(h))
    #addDir('test', "url", "next_mode", "", "subreddit" )
    if not os.path.exists(subredditsFile):
        create_default_subreddits()

    #log( "  show_nsfw  "+str(show_nsfw) + "  [" + nsfw+"]")

    #log( "--------------------"+ addon.getAddonInfo('path') )
    #log( "--------------------"+ addon.getAddonInfo('profile') )
     
    #this part errors on android. comment out until feature is implemented
#     if not os.path.exists(ytdl_psites_file): 
#         #copy over default file
#         #there is no os.copy() command. have to use shutil or just read and write to file ourself
#         #open(ytdl_psites_file, "w").write(open( default_ytdl_psites_file ).read())
#         log( "default ytdl_sites file not found. copying from addon installation.")
#         shutil.copy(default_ytdl_psites_file, ytdl_psites_file)
# 
#     if not os.path.exists(ytdl_sites_file): 
#         log( "default ytdl_sites file not found. copying from addon installation.")
#         shutil.copy(default_ytdl_sites_file, ytdl_sites_file)

    if no_index_page:   
        log( "   default_frontpage " +default_frontpage )
        if default_frontpage:
            #log( "   ssssssss " + assemble_reddit_filter_string("","")  )
            listSubReddit( assemble_reddit_filter_string("",default_frontpage) , default_frontpage, "") 
        else:
            listSubReddit( assemble_reddit_filter_string("","") , "Reddit-Frontpage", "") #https://www.reddit.com/.json?&&limit=10
    else:
        #subredditsFile loaded in gui    
        ui = indexGui('view_461_comments.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', subreddits_file=subredditsFile, id=55)
        ui.title_bar_text="Reddit Reader"
        ui.include_parent_directory_entry=False
    
        ui.doModal()
        del ui
    
    return
    
#MODE listSubReddit(url, name, type)  
def listSubReddit(url, title_bar_name, type):
    from resources.lib.domains import parse_filename_and_ext_from_url
    from resources.lib.utils import unescape, pretty_datediff, post_excluded_from, determine_if_video_media_from_reddit_json, has_multiple_subreddits
    from resources.lib.utils import assemble_reddit_filter_string,build_script,compose_list_item
    
    #url=r'https://www.reddit.com/r/videos/search.json?q=nsfw:yes+site%3Ayoutu.be+OR+site%3Ayoutube.com+OR+site%3Avimeo.com+OR+site%3Aliveleak.com+OR+site%3Adailymotion.com+OR+site%3Agfycat.com&sort=relevance&restrict_sr=on&limit=5&t=week'
    #url='https://www.reddit.com/search.json?q=site%3Adailymotion&restrict_sr=&sort=relevance&t=week'
    #url='https://www.reddit.com/search.json?q=site%3A4tube&sort=relevance&t=all'
    #url="https://www.reddit.com/domain/tumblr.com.json"
    #url="https://www.reddit.com/r/wiiu.json?&nsfw:no+&limit=13"

    #show_listSubReddit_debug=False
    show_listSubReddit_debug=True
    credate = ""
    is_a_video=False
    title_line2=""

    thumb_w=0
    thumb_h=0

    #the +'s got removed by url conversion 
    title_bar_name=title_bar_name.replace(' ','+')
    #log("  title_bar_name %s " %(title_bar_name) )

    log("listSubReddit r/%s url=%s" %(title_bar_name,url) )
    t_on = translation(32071)  #"on"
    #t_pts = u"\U0001F4AC"  # translation(30072) #"cmnts"  comment bubble symbol. doesn't work
    t_pts = u"\U00002709"  # translation(30072)   envelope symbol
    t_up = u"\U000025B4"  #u"\U00009650"(up arrow)   #upvote symbol
    
    li=[]

    currentUrl = url
    xbmc_busy()    
    content = reddit_request(url)  #content = opener.open(url).read()
    
    if not content:
        xbmc_busy(False)
        return
    
    #7-15-2016  removed the "replace(..." statement below cause it was causing error
    #content = json.loads(content.replace('\\"', '\''))
    content = json.loads(content) 
    
    #log("query returned %d items " % len(content['data']['children']) )
    posts_count=len(content['data']['children'])
    
    hms = has_multiple_subreddits(content['data']['children'])
    
    if hms==False:
        #r/random and r/randnsfw returns a random subreddit. we need to use the name of this subreddit for the "next page" link. 
        try: g=content['data']['children'][0]['data']['subreddit']
        except: g=""
        if g:
            title_bar_name=g
            #preserve the &after string so that functions like play slideshow and play all videos can 'play' the correct page 
            #  extract the &after string from currentUrl -OR- send it with the 'type' argument when calling this function.
            currentUrl=assemble_reddit_filter_string('',g) + '&after=' + type

    for idx, entry in enumerate(content['data']['children']):
        try:
            title = unescape(entry['data']['title'].encode('utf-8'))
            is_a_video = determine_if_video_media_from_reddit_json(entry)
            if show_listSubReddit_debug : log("  POST%cTITLE%.2d=%s" %( ("v" if is_a_video else " "), idx, title ))
            
            post_id = entry['kind'] + '_' + entry['data']['id']  #same as entry['data']['name']      
            #log('  %s  %s ' % (post_id, entry['data']['name'] ))
            
            try:    description = unescape(entry['data']['media']['oembed']['description'].encode('utf-8'))
            except: description = ''
            #log('    description  [%s]' %description)
            try:    post_selftext=unescape(entry['data']['selftext'].encode('utf-8'))
            except: post_selftext=''
            #log('    post_selftext[%s]' %post_selftext)
            
            description=post_selftext+'[CR]'+description if post_selftext else description
            #log('    combined     [%s]' %description)
                
            commentsUrl = urlMain+entry['data']['permalink'].encode('utf-8')
            #if show_listSubReddit_debug :log("commentsUrl"+str(idx)+"="+commentsUrl)
            
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
            
            if post_excluded_from( subreddit_filter, subreddit ):
                log( '    r/%s excluded by subreddit_filter' %subreddit )
                continue;
            
            try: author = entry['data']['author'].encode('utf-8')
            except: author = ""
            
            try: domain= entry['data']['domain'].encode('utf-8')
            except: domain = ""
            #log("     DOMAIN%.2d=%s" %(idx,domain))
            if post_excluded_from( domain_filter, domain ):
                log( '    %s excluded by domain_filter' %domain )
                continue;
            
            ups = entry['data']['score']       #downs not used anymore
            try:num_comments = entry['data']['num_comments']
            except:num_comments = 0
            
            #description = "[COLOR blue]r/"+ subreddit + "[/COLOR]  [I]" + str(ups)+" pts  |  "+str(comments)+" cmnts  |  by "+author+"[/I]\n"+description
            #description = "[COLOR blue]r/"+ subreddit + "[/COLOR]  [I]" + str(ups)+" pts.  |  by "+author+"[/I]\n"+description
            #description = title_line2+"\n"+description
            #if show_listSubReddit_debug :log("DESCRIPTION"+str(idx)+"=["+description+"]")
            try:
                media_url = entry['data']['url'].encode('utf-8')
            except:
                media_url = entry['data']['media']['oembed']['url'].encode('utf-8')
                
            #media_url=media_url.lower()  #!!! note: do not lowercase!!!     
            
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
                preview="" #a blank preview image will be replaced with poster_url from parse_reddit_link() for domains that support it

            #preview images are 'keep' stretched to fit inside 1080x1080. 
            #  if preview image is smaller than the box we have for thumbnail, we'll use that as thumbnail and not have a bigger stretched image  
            if thumb_w > 0 and thumb_w < 280:
                #log('*******preview is small ')
                thumb=preview
                thumb_w=0
                thumb_h=0
                preview=""

            try:
                over_18 = entry['data']['over_18']
            except:
                over_18 = False

            title_line2=""
            title_line2 = "[I][COLOR dimgrey]%d%c %s %s [COLOR teal]r/%s[/COLOR] (%d) %s[/COLOR][/I]" %(ups,t_up,pretty_date,t_on, subreddit,num_comments, t_pts)
            #title_line2 = "[I][COLOR dimgrey]%s by %s [COLOR darkslategrey]r/%s[/COLOR] %d pts.[/COLOR][/I]" %(pretty_date,author,subreddit,ups)
            #http://www.w3schools.com/colors/colors_names.asp
            #title_line2 = "[I][COLOR dimgrey]%s %s [COLOR teal]r/%s[/COLOR] (%d) %s[/COLOR][/I]" %(pretty_date,t_on, subreddit,num_comments, t_pts)
            #title_line2 = "[I]"+str(idx)+". [COLOR dimgrey]"+ media_url[0:50]  +"[/COLOR][/I] "  # +"    "+" [COLOR darkslategrey]r/"+subreddit+"[/COLOR] "+str(ups)+" pts.[/COLOR][/I]"
            #if show_listSubReddit_debug :log("      OVER_18"+str(idx)+"="+str(over_18))
            #if show_listSubReddit_debug :log("   IS_A_VIDEO"+str(idx)+"="+str(is_a_video))
            #if show_listSubReddit_debug :log("        THUMB"+str(idx)+"="+thumb)
            #if show_listSubReddit_debug :log("    MediaURL%.2d=%s" % (idx,media_url) )
            #if show_listSubReddit_debug :log("       HOSTER"+str(idx)+"="+hoster)
            #log("    VIDEOID"+str(idx)+"="+videoID)
            #log( "["+description+"]1["+ str(date)+"]2["+ str( count)+"]3["+ str( commentsUrl)+"]4["+ str( subreddit)+"]5["+ video_url +"]6["+ str( over_18))+"]"

            liz=addLink(title=title, 
                    title_line2=title_line2,
                    iconimage=thumb, 
                    previewimage=preview,
                    preview_w=thumb_w,
                    preview_h=thumb_h,
                    domain=domain,
                    description=description, 
                    credate=credate, 
                    reddit_says_is_video=is_a_video, 
                    site=commentsUrl, 
                    subreddit=subreddit, 
                    link_url=media_url, 
                    over_18=over_18,
                    posted_by=author,
                    num_comments=num_comments,
                    post_id=post_id,
                    post_index=idx,
                    post_total=posts_count,
                    many_subreddit=hms)
            
            li.append(liz)
            
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
        if after: 
            if "&after=" in currentUrl:
                nextUrl = currentUrl[:currentUrl.find("&after=")]+"&after="+after
            else:
                nextUrl = currentUrl+"&after="+after
            
            # plot shows up on estuary. etc. ( avoids the "No information available" message on description ) 
            info_label={ "plot": translation(32004) } 
             
            #addDir(translation(32004), nextUrl, 'listSubReddit', "", subreddit,info_label)   #Next Page
            
            liz = compose_list_item( translation(32004), "", "DefaultFolderNextSquare.png", "script", build_script("listSubReddit",nextUrl,title_bar_name,after), {'plot': translation(32004)} )
            
            li.append(liz)
        
        #if show_listSubReddit_debug :log("NEXT PAGE="+nextUrl) 
    except Exception as e:
        log(" EXCEPTzION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
        
        pass
    
    xbmc_busy(False)
    
    title_bar_name=urllib.unquote_plus(title_bar_name)
    skin_launcher('listSubReddit', title_bar_name=title_bar_name, li=li,subreddits_file=subredditsFile, currentUrl=currentUrl)    
    
    #ui.show()  #<-- interesting possibilities. you have to handle the actions outside of the gui class. 
    #xbmc.sleep(8000)

def skin_launcher(mode,**kwargs ):
    
    from resources.lib.utils import xbmcVersion
    from resources.lib.guis import listSubRedditGUI
        
    kodi_version = xbmcVersion()
    #log( ' kodi version:%f' % kodi_version )
    if kodi_version >= 17:  #krypton
        pass
    
    
    title_bar_text=kwargs.get('title_bar_name')
    li=kwargs.get('li')
    subreddits_file=kwargs.get('subreddits_file')
    currentUrl=kwargs.get('currentUrl')
    #log('********************* ' + repr(currentUrl))
    try:    
        ui = listSubRedditGUI(main_gui_skin , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, subreddits_file=subreddits_file, id=55)
        ui.title_bar_text='[B]'+ title_bar_text + '[/B]'
        ui.reddit_query_of_this_gui=currentUrl
        #ui.include_parent_directory_entry=True
    
        ui.doModal()
        del ui
    except Exception as e:
        log('  skin_launcher:%s(%s)' %( str(e), main_gui_skin ) )
        xbmc.executebuiltin('XBMC.Notification("%s","%s[CR](%s)")' %(  translation(32108), str(e), main_gui_skin)  )
        


def addLink(title, title_line2, iconimage, previewimage,preview_w,preview_h,domain, description, credate, reddit_says_is_video, site, subreddit, link_url, over_18, posted_by="", num_comments=0,post_id='', post_index=1,post_total=1,many_subreddit=False ):
    from resources.lib.utils import ret_info_type_icon, assemble_reddit_filter_string,build_script
    from resources.lib.domains import parse_reddit_link, sitesBase

    DirectoryItem_url=''
    post_title=title
    il_description=""
    
    preview_ar=0.0
    if preview_w==0 or preview_h==0:
        preview_ar=0.0
    else:
        preview_ar=float(preview_w) / preview_h

    if over_18: 
        mpaa="R"
        #description = "[B]" + hoster + "[/B]:[COLOR red][NSFW][/COLOR] "+title+"\n" + description
        #il_description = "[COLOR red][NSFW][/COLOR] "+ h+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"
        title_line2 = "[COLOR red][NSFW][/COLOR] "+title_line2
    else:
        mpaa=""
        #il_description = h+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"

    post_title=title
    if len(post_title) > 40:
        il_description='[B]%s[/B][CR][CR]%s' %( post_title, description )
    else:
        il_description='%s' %( description )

    #if title is long, put it in description so that it will trigger displaying under preview image
    #if len(title) > 100 :
    #il_description=title + description

        
    il={ "title": post_title, "plot": il_description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": domain, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin

    #if poster_url=="":
    #    poster_url=iconimage
    
    #log( "  PLOT:" +il_description )
    liz=xbmcgui.ListItem(label=post_title
                         ,label2=title_line2
                         ,iconImage=""
                         ,thumbnailImage=''
                         ,path='')   #path not used by gui.

    #liz.setArt({"thumb": iconimage, "poster":poster_url, "banner":poster_url, "fanart":poster_url, "landscape":poster_url   })
    
    #----- assign actions
    if preview_ar>0 and preview_ar < 0.7 and preview_h > 1090 :   #vertical image taken by 16:9 camera will have 0.5625 aspect ratio. anything narrower than that, we will zoom_n_slide
        #from resources.lib.utils import link_url_is_playable
        #log('*****%f '%preview_ar)
        #if link_url_is_playable(link_url):
        #log('*****has zoom_n_slide_action ')
        #liz.setProperty('zoom_n_slide_action', build_script('zoom_n_slide', link_url,str(preview_w),str(preview_h) ) )
        #actual ar check in parse_reddit_link     
        pass 
        
    if preview_ar>1.25:   #this measurement is related to control id 203's height
        #log('    ar and description criteria met') 
        #the gui checks for this: String.IsEmpty(Container(55).ListItem.Property(preview_ar))  to show/hide preview and description
        liz.setProperty('preview_ar', str(preview_ar) ) # -- $INFO[ListItem.property(preview_ar)] 
        liz.setInfo(type='video', infoLabels={"plotoutline": il_description, }  )

    #----- assign actions
    if num_comments > 0 or description:
        liz.setProperty('comments_action', build_script('listLinksInComment', site ) )
    liz.setProperty('goto_subreddit_action', build_script("listSubReddit", assemble_reddit_filter_string("",subreddit), subreddit) )
    liz.setProperty('link_url', link_url )
    liz.setProperty('post_id', post_id )
    
    liz.setInfo(type='video', infoLabels=il)
    #
    
    #liz.addStreamInfo('video', { 'codec': 'preview_ar','aspect': preview_ar, 'width': preview_w, 'height': preview_h } )  #how to retrieve?
    #liz.setProperty('aspectt', '2.0')   #retrieve this with $INFO[ListItem.property(aspectt)]
    #liz.setInfo(type='pictures', infoLabels={'exif:resolution': '%d,%d' %( preview_w, preview_h)  } ) $INFO[ListItem.PictureResolution]
    

    #use clearart to indicate if link is video, album or image. here, we default to unsupported.
    clearart=ret_info_type_icon('', '')
    liz.setArt({ "clearart": clearart  })

    
    #force all links to ytdl to see if they are playable 
    if use_ytdl_for_unknown:
        liz.setProperty('item_type','script')         
        liz.setProperty('onClick_action', build_script('playYTDLVideo', link_url,'',previewimage) )



    if previewimage: needs_preview=False  
    else:            needs_preview=True  #reddit has no thumbnail for this link. please get one
    
    ld=parse_reddit_link(link_url,reddit_says_is_video, needs_preview, False, preview_ar  )

    if previewimage=="":
        liz.setArt({"thumb": iconimage, "banner": ld.poster if ld else '' , })
    else:
        liz.setArt({"thumb": iconimage, "banner":previewimage,  })
        


#    log( '          reddit thumb[%s] ' %(iconimage ))
#    log( '          reddit preview[%s] ar=%f %dx%d' %(previewimage, preview_ar, preview_w,preview_h ))
#    if ld: log( '          new-thumb[%s] poster[%s] ' %( ld.thumb, ld.poster ))

    if ld:
        #log('###' + repr(ld.playable_url) )
        #url_for_DirectoryItem = build_script(ld.link_action, ld.playable_url, post_title , previewimage )
        #log('  ##is supported')

        #use clearart to indicate the type of link(video, album, image etc.)
        clearart=ret_info_type_icon(ld.media_type, ld.link_action, domain )
        liz.setArt({ "clearart": clearart  })

        
        if iconimage in ["","nsfw", "default"]:
            iconimage=ld.thumb

        if ld.link_action == sitesBase.DI_ACTION_PLAYABLE:
            property_link_type=ld.link_action
            DirectoryItem_url =ld.playable_url
        else:
            property_link_type='script'
            if ld.link_action=='viewTallImage' : #viewTallImage take different args
                DirectoryItem_url = build_script(mode=ld.link_action, 
                                                 url=ld.playable_url,
                                                 name=str(preview_w),
                                                 type=str(preview_h) ) 
            else:  
                DirectoryItem_url = build_script(mode=ld.link_action, 
                                                 url=ld.playable_url, 
                                                 name=post_title , 
                                                 type=previewimage ) 
        
        #log('    action %s--%s' %( ld.link_action, DirectoryItem_url) )
        
        liz.setProperty('item_type',property_link_type)
        #liz.setProperty('onClick_action',DirectoryItem_url)
        liz.setProperty('onClick_action',DirectoryItem_url)
        
    else:
        #unsupported type here:
        pass

    return liz





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





q = Queue()

#MODE autoPlay        - name not used
def autoPlay(url, name, type):
    from resources.lib.domains import sitesBase, parse_reddit_link 
    from resources.lib.utils import unescape, pretty_datediff, post_excluded_from, determine_if_video_media_from_reddit_json, remove_duplicates
    #collect a list of title and urls as entries[] from the j_entries obtained from reddit
    #then create a playlist from those entries
    #then play the playlist

    entries = []
    watchdog_counter=0
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    xbmc_busy()
    
    #content = opener.open(url).read()
    content = reddit_request(url)        
    if not content: return
    #log( str(content) )
    #content = json.loads(content.replace('\\"', '\''))
    content = json.loads(content)
    
    log("Autoplay %s - Parsing %d items" %( type, len(content['data']['children']) )    )
    
    for j_entry in content['data']['children']:
        try:
            title = unescape(j_entry['data']['title'].encode('utf-8'))
            
            try:
                media_url = j_entry['data']['url']
            except:
                media_url = j_entry['data']['media']['oembed']['url']

            is_a_video = determine_if_video_media_from_reddit_json(j_entry) 

            log("  %cTITLE:%s"  %( ("v" if is_a_video else " "), title  ) )

            ld=parse_reddit_link(link_url=media_url, assume_is_video=False, needs_preview=False, get_playable_url=True )

            if ld:
                
                log('      type:%s %s' %( ld.media_type, ld.link_action)   )
                if ld.media_type in [sitesBase.TYPE_VIDEO, sitesBase.TYPE_VIDS, sitesBase.TYPE_MIXED]:
                    if type.startswith("UNWATCHED_") and getPlayCount(url) < 0:
                        #log("      UNWATCHED_" )
                        entries.append([title,ld.playable_url, ld.link_action])
                    elif type.startswith("UNFINISHED_") and getPlayCount(url) == 0:
                        #log("      UNFINISHED_" )
                        entries.append([title,ld.playable_url, ld.link_action])
                    else:  # type.startswith("ALL_")
                        #log("      ALL_" )
                        entries.append([title,ld.playable_url, ld.link_action])
                    
                
        except Exception as e:
            log( '  autoPlay exception:' + str(e) )
            pass
    
     
    
    #for i,e in enumerate(entries): log('  e1-%d %s:' %(i, e[1]) )
    def k2(x): return x[1]
    entries=remove_duplicates(entries, k2)
    #for i,e in enumerate(entries): log('  e2-%d %s:' %(i, e[1]) )

    for i,e in enumerate(entries): 
        log('  possible playable items(%d) %s...%s' %(i, e[0].ljust(15)[:15], e[1]) )
        
    if len(entries)==0:
        log('  Play All: no playable items' )
        xbmc.executebuiltin('XBMC.Notification("%s","%s")' %(translation(32054), translation(32055)  ) )  #Play All     No playable items
        return
    
    entries_to_buffer=4
    #log('  entries:%d buffer:%d' %( len(entries), entries_to_buffer ) )
    if len(entries) < entries_to_buffer:
        entries_to_buffer=len(entries)
        #log('entries to buffer reduced to %d' %entries_to_buffer )

    #if type.endswith("_RANDOM"):
    #    random.shuffle(entries)

    #for title, url in entries:
    #    log("  added to playlist:"+ title + "  " + url )

    log("**********autoPlay*************")
    
    #play_list=[]
    ev = threading.Event()
    
    t = Worker(entries, q, ev)
    t.daemon = True
    t.start()
    #t.run()

    #wait for worker to finish processing 1st item
    #e.wait(200)
    
    while True:
        #log( '  c-wait+get buffer(%d) wdt=%d ' %(playlist.size(), watchdog_counter)  )
        try:
            #playable_url = q.get(True, 10)
            playable_entry = q.get(True, 10)
            #playable_url=playable_entry[1]
            q.task_done()
            #play_list.append(playable_entry[1])
            playlist.add(playable_entry[1], xbmcgui.ListItem(playable_entry[0]))
            log( '    c-buffered(%d):%s...%s' %(playlist.size(), playable_entry[0].ljust(15)[:15], playable_entry[1])  )

        except:
            watchdog_counter+=1
            if ev.is_set():#p is done producing
                break
            #if got 3 empty from queue.
            pass
        watchdog_counter+=1    
        #log('  playlist:%d buffer:%d' %( playlist.size(), entries_to_buffer ) )
        if playlist.size() >= entries_to_buffer:  #q.qsize()
            log('  c-buffer count met')
            break
        if watchdog_counter > entries_to_buffer: 
            break
    
    log('  c-buffering done')
    
    #xbmc_busy(False)    
    
    xbmc.Player().play(playlist)    
    
    watchdog_counter=0
    while True:
        #log( '  c-get buffer(%d) wdt=%d ' %(playlist.size(), watchdog_counter)  )
        #q.join()  
        #log( ' c- join-ed, get... '  )
        try:        
            #playable_url = q.get(True,10)
            playable_entry = q.get(True,10)
            q.task_done()
            #log( '    c- got next item... ' + playable_entry[1] )
            #play_list.append(playable_entry[1])
            playlist.add(playable_entry[1], xbmcgui.ListItem(playable_entry[0]))
            log( '    c-got next item(%d):%s...%s' %(playlist.size(), playable_entry[0].ljust(15)[:15], playable_entry[1])  )
        except:
            watchdog_counter+=1
            if ev.isSet(): #p is done producing
                break
            
            pass
        #xbmc.PlayList(1).add(playable_url)

        if ev.isSet() and q.empty():
            log( ' c- ev is set and q.empty -->  break '  )
            break
        
        if watchdog_counter > 2:
            break

    log( ' c-all done '  )

    #for e in play_list: log( str(e) )
        
#     for title, url in entries:
#         listitem = xbmcgui.ListItem(title)
#         playlist.add(url, listitem)
#     xbmc.Player().play(playlist)

    
class Worker(threading.Thread):
    def __init__(self, entries, queue, ev):
        threading.Thread.__init__(self)
        self.queue = queue
        self.work_list=entries
        self.ev=ev
        #log('  p-init ' + str( self.work_list ))

    def stop(self):
        self.running=False

    def run(self):
#        threading.Thread.run(self)
        #log('  p-running ' + str( self.work_list ))
        self.running = True
        # Rather than running forever, check to see if it is still OK
        while self.running:
            try:
                # Don't block
                #item = self.queue.get(block=False)
                self.do_work()
                 
                self.ev.set()
                #work dome end
                log( '  p-all done '  ) 
                self.stop()
            except Empty:
                # Allow other stuff to run
                time.sleep(0.1)

    def do_work(self):
        #log( ' wor-ker (%(threadName)-10s)')
        
        url_to_check=""
        #for url in self.work_list:
        #    log('  worker task list:' + title.ljust(15)[:15] +'... '+ url )
        
        #for title, w_url, modecommand in self.work_list:
        for entry in self.work_list:
            #work  
            #xbmc.sleep(2000)
            title=entry[0]
            url_to_check=entry[1]
            if url_to_check.startswith('plugin://'):
                playable_url=url_to_check
                pass
            else:
                playable_url = ydtl_get_playable_url( url_to_check )  #<-- will return a playable_url or a list of playable urls
            #playable_url= '(worked)' + title.ljust(15)[:15] + '... '+ w_url
            #work
            if playable_url:
                if isinstance(playable_url, basestring):
                    entry[1]=playable_url
                    log('    p-%d %s... %s' %(self.queue.qsize(), title.ljust(15)[:15], playable_url)  )
                    self.queue.put(entry)
                else:
                    for u in playable_url:
                        log('    p-(multiple)%d %s... %s' %(self.queue.qsize(), title.ljust(15)[:15], u)  )
                        self.queue.put( [title, u] )
            else:
                log('      p-(ytdl-failed) %s' %( title )  )


#MODE playVideo       - name, type not used
def playVideo(url, name, type):
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    #log("playVideo:"+url)
    
    if url : #sometimes url is a list of url or just a single string
        if isinstance(url, basestring):
            pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pl.clear()
            pl.add(url, xbmcgui.ListItem(name))
            xbmc.Player().play(pl, windowed=False)  #scripts play video like this.
        	#listitem = xbmcgui.ListItem(path=url)   #plugins play video like this.
            #xbmcplugin.setResolvedUrl(pluginhandle, True, listitem) 
        else:
            pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pl.clear()
            for u in url:
                #log('u='+ repr(u))
                #pl.add(u)
                pl.add(u, xbmcgui.ListItem(name))
            xbmc.Player().play(pl, windowed=False)  
    else:
        log("playVideo(url) url is blank")
        
def ydtl_get_playable_url( url_to_check ):
    from resources.lib.utils import link_url_is_playable
    #log('ydtl_get_playable_url:' +url_to_check )
    if link_url_is_playable(url_to_check)=='video':
        return url_to_check

    choices = []
    
    if YDStreamExtractor.mightHaveVideo(url_to_check,resolve_redirects=True):
        log('      YDStreamExtractor.mightHaveVideo[true]=' + url_to_check)
        #xbmc_busy()
        #https://github.com/ruuk/script.module.youtube.dl/blob/master/lib/YoutubeDLWrapper.py
        vid = YDStreamExtractor.getVideoInfo(url_to_check,0,True)  #quality is 0=SD, 1=720p, 2=1080p and is a maximum
        if vid:
            log("        getVideoInfo playableURL="+vid.streamURL())
            #log("        %s  %s %s" %( vid.sourceName , vid.description, vid.thumbnail ))   #usually just 'generic' and blank on everything else
            if vid.hasMultipleStreams():
                #vid.info  <-- The info property contains the original youtube-dl info
                log("          vid hasMultipleStreams %d" %len(vid._streams) )
                for s in vid.streams():
                    title = s['title']
                    #log('            choices: %s... %s' %( title.ljust(15)[:15], s['xbmc_url']  )   )
                    choices.append(s['xbmc_url'])
                #index = some_function_asking_the_user_to_choose(choices)
                #vid.selectStream(0) #You can also pass in the the dict for the chosen stream
                return choices  #vid.streamURL()   
    
            return vid.streamURL()                         #This is what Kodi (XBMC) will play    
        
def playYTDLVideo(url, name, type):
    #url = "http://www.youtube.com/watch?v=_yVv9dx88x0"   #a youtube ID will work as well and of course you could pass the url of another site
    #log("playYTDLVideo="+url)
    #url='https://www.youtube.com/shared?ci=W8n3GMW5RCY'
    #url='http://burningcamel.com/video/waster-blonde-amateur-gets-fucked'
    #url='http://www.3sat.de/mediathek/?mode=play&obj=51264'
    #url='http://www.rappler.com/nation/141700-full-text-leila-de-lima-privilege-speech-extrajudicial-killings'
    #url='https://www.vidble.com/album/KtAymux9' 

    #from BeautifulsSoup import BeautifulSoup
    #r = urllib.urlopen('http://www.aflcio.org/Legislation-and-Politics/Legislative-Alerts').read() 
    #soup = BeautifulSoup(r) 
    #text =  soup.get_text() 
    

#these checks done in around May 2016
#does not work:  18porn.xyz 5min.com alphaporno.com analxtv.com aniboom.com asiantubesex.com asianxtv.com bdsmstreak.com bigtits.com bondagetube.tv bustnow.com camwhores.tv chumleaf.com dailee.com dailygirlscute.com
# desianalporn.com dirtydirtyangels.com eporner.com eroshare.com fapgod.com fapxl.com flingtube.com flyflv.com fookgle.com foxgay.com freudbox.com fucktube.com fux.com fux.com goshgay.com gotporn.com hdpornstar.com
# hdvideos.porn hdvideos.porn hentaidream.me hvdporn.com indianxxxhd.com jizzbox.com jizzxman.com kalporn.com kuntfutube.com lubetube.com lxxlx.com lxxlx.com maxjizztube.com moviesand.com moviesguy.com
# nosvideo.com nurglestube.com onlypron.com openload.online orgasm.com pk5.net played.to(site is gone) player.moviefap.com(www.moviefap.com works) porn.com pornative.com porncor.com porndig.com pornerbros.com
# porness.tv porness.tv pornheed.com pornhvd.com pornmax.xyz pornovo.com pornsharia.com porntube pornurl.pw pornvil.com pornwaiter.com pornwebms.com pornworms.com redclip.xyz sexix.net sextvx.com sexu.com
# sherloxxx.com shooshtime.com sluttyred.com spankingtube.tv stickyxtube.com thumbzilla.com userporn.com vidmega.net vidshort.net vidxnet.com virtualtaboo.com voyeurweb.com watchersweb.com watchxxxfree.com
# woporn.net x1xporn.com xfapzap.com xfig.net xpornvid.com xrhub.com xstigma.com xxxbunker.com yazum.com yobt.com younow.com youpunish.com yourdailypornvideos.com yourfreeporn.us yourlust yporn.tv yteenporn.com
# yuvutu.com zoig.com zuzandra.com
 
 
# also does not work (non porn)
#  163.com 1tv.ru 1up.com 220.ro 24video.xxx 3sat.de 56.com adultswim.com afreeca.com akb48ma.com atresplayer.com azubu.tv bet.com biobiochile.cl biqle.com blinkx.com blip.tv blogtv.com bloomberg.com/news/videos
# bpb.de brainpop.com bravotv.com byutv.org cbc.ca chirbit.com cloudtime.to(almost) cloudyvideos.com cracked.com crackle.com crackle.com criterion.com ctv.ca culturebox.francetvinfo.fr cultureunplugged.com cwtv.com
# daum.net dctp.tv democracynow.org douyutv.com dumpert.nl eitb.tv engagemedia.org ex.fm expotv.com fc-zenit.ru flickr.com Flipagram.com Formula1.com fotki.com fox.com/watch(few works) foxsports.com france2.fr
# franceculture.fr franceinter.fr francetv.fr/videos francetvinfo.fr ft.dk giantbomb.com hbo.com History.com hitbox.tv hlamer.ru howcast.com HowStuffWorks.com hrt.hr hulu.com iconosquare.com ikudonsubs.com
# infoq.com ivi.ru izlesene.com kamcord.com/v karrierevideos.at KrasView.ru kuwo.cn la7.it lafango.com laola1.tv le.com mail.ru media.ccc.de mefeedia.com metacafe.com metacritic.com mitele.es moevideo.net,playreplay.net,videochart.net
# motionpictur.com movieclips.com mtv.de mtviggy.com muenchen.tv myspace.com myvi.ru myvideo.de myvideo.de myvideo.ge nbcolympics.com netzkino.de nfb.ca nicovideo.jp nicovideo.jp normalboots.com nowness.com
# nrk.no ntr.nl ntv.ru/video ocw.mit.edu odnoklassniki.ru/video olympics.cbc.ca onet.tv onionstudios.com/videos openload.co orf.at parliamentlive.tv patas.in periscope.tv play.fm pluzz.francetv.fr rutube.ru
# sciencestage.com sevenload.com techchannel.att.com trilulilu.ro tudou.com v.baidu.com vbox7.com video.foxnews.com video.kankan.com video.yahoo.com videohive.net videojug.com videos.sapo.pt(many but not all)
# vidoosh.tv vidspot.net(might work, can't find recent post) vzaar.com www.bbc.co.uk/iplayer



# news site (can't find sample to test) 
# bleacherreport.com crooksandliars.com DailyMail.com channel5.com Funimation.com gamersyde.com gamespot.com gazeta.pl helsinki.fi hotnewhiphop.com lemonde.fr mnet.com motorsport.com MSN.com
# n-tv.de ndr.de NDTV.com NextMedia.com noz.de pcmag.com people.com idnes.cz lidovky.cz pluralsight.com plus.google.com


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
    xbmc_busy()
    from urlparse import urlparse
    parsed_uri = urlparse( url )
    domain = '{uri.netloc}'.format(uri=parsed_uri)

    try:
        stream_url = ydtl_get_playable_url(url)
        #log( ' ytdl stream url ' + repr(stream_url ))
        #if len(stream_url) == 1:
        #    playVideo(stream_url, name, type)
        
        if stream_url:
            playVideo(stream_url, name, type)

        else:
            #log("getVideoInfo failed==" )
            xbmc.executebuiltin('XBMC.Notification("%s", "%s (YTDL)" )'  %( translation(32010), domain )  )  

    
    except Exception as e:
        #log( "zz   " + str(e) )
        xbmc.executebuiltin('XBMC.Notification("%s(YTDL)","%s")' %(  domain, str(e))  )

    #xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        
        
        #xbmc.executebuiltin('XBMC.Notification("%s","%s")' %(  Gfycat.com, translation(32010) )  )

def listLinksInComment(url, name, type):
    from resources.lib.domains import parse_reddit_link, sitesBase
    from resources.lib.utils import markdown_to_bbcode, unescape, ret_info_type_icon, build_script

    log('listLinksInComment:%s:%s' %(type,url) )

    directory_items=[]
    author=""
    post_title=''
    ShowOnlyCommentsWithlink=False

    if type=='linksOnly':
        ShowOnlyCommentsWithlink=True
        using_custom_gui=False #for now, our custom gui cannot handle links very well. we will let kodi handle it
    else:
        using_custom_gui=True
        
    #sometimes the url has a query string. we discard it coz we add .json at the end
    #url=url.split('?', 1)[0]+'.json'

    #url='https://www.reddit.com/r/Music/comments/4k02t1/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/' + '.json'
    #only get up to "https://www.reddit.com/r/Music/comments/4k02t1". 
    #   do not include                                            "/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/"
    #   because we'll have problem when it looks like this: "https://www.reddit.com/r/Overwatch/comments/4nx91h/ever_get_that_feeling_dÃ©jÃ _vu/"
    #url=re.findall(r'(.*/comments/[A-Za-z0-9]+)',url)[0]
    #UPDATE you need to convert this: https://www.reddit.com/r/redditviewertesting/comments/4x8v1k/test_test_what_is_déjà_vu/
    #                        to this: https://www.reddit.com/r/redditviewertesting/comments/4x8v1k/test_test_what_is_d%C3%A9j%C3%A0_vu/
    #
    #use safe='' argument in quoteplus to encode only the weird chars part 
    
    url=  urllib.quote_plus(url,safe=':/') 
    url+= '.json'
    xbmc_busy()
    content = reddit_request(url)        
    if not content: return
    #content = r''
    
    #log(content)
    #content = json.loads(content.replace('\\"', '\''))  #some error here ?      TypeError: 'NoneType' object is not callable
    try:
        xbmc_busy()
        content = json.loads(content)
        
        del harvest[:]
        #harvest links in the post text (just 1) 
        r_linkHunter(content[0]['data']['children'])
        
        try:submitter=content[0]['data']['children'][0]['data']['author']
        except: submitter=''
        
        
        #the post title is provided in json, we'll just use that instead of messages from addLink()
        try:post_title=content[0]['data']['children'][0]['data']['title']
        except:post_title=''
        #for i, h in enumerate(harvest):
        #    log("aaaaa first harvest "+link_url)
    
        #harvest links in the post itself    
        r_linkHunter(content[1]['data']['children'])
    
        #for i, h in enumerate(harvest):
        #    log( '  %d %s %d -%s   link[%s]' % ( i, h[7].ljust(8)[:8], h[0], h[3].ljust(20)[:20],h[2] ) )
    
#         h[0]=score, 
#         h[1]=link_desc, 
#         h[2]=link_http, 
#         h[3]=post_text, 
#         h[4]=post_html, 
#         h[5]=d, 
#         h[6]="t1",
#         h[7]=author,
#         h[8]=created_utc,
    
        comment_score=0
        for i, h in enumerate(harvest):
            #log(str(i)+"  score:"+ str(h[0]).zfill(5)+" "+ h[1] +'|'+ h[3] )
            comment_score=h[0]
            #log("score %d < %d (%s)" %(comment_score,int_CommentTreshold, CommentTreshold) )
            link_url=h[2]
            desc100=h[3].replace('\n',' ')[0:100] #first 100 characters of description

            kind=h[6] #reddit uses t1 for user comments and t3 for OP text of the post. like a poster describing the post.  
            d=h[5]   #depth of the comment
            
            tab=" "*d if d>0 else "-"
            
            author=h[7]
            
            from urlparse import urlparse
            domain = '{uri.netloc}'.format( uri=urlparse( link_url ) )
            
            #log( '  %s TITLE:%s... link[%s]' % ( str(comment_score).zfill(4), desc100.ljust(20)[:20],link_url ) )
            if comment_score < int_CommentTreshold:
                #log('    comment score %d < %d, skipped' %(comment_score,int_CommentTreshold) )
                continue
            
            #hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, property_link_type =make_addon_url_from(link_url, False, True)
            
            if link_url:
                log( '  comment %s TITLE:%s... link[%s]' % ( str(d).zfill(3), desc100.ljust(20)[:20],link_url ) )
                
            ld=parse_reddit_link(link_url=link_url, assume_is_video=False, needs_preview=True, get_playable_url=True )


            
            
            if author==submitter:#add a submitter tag
                author="[COLOR cadetblue][B]%s[/B][/COLOR][S]" %author 
            else:
                author="[COLOR cadetblue]%s[/COLOR]" %author
            
            if kind=='t1':
                t_prepend=r"%s" %( tab )
            elif kind=='t3':
                t_prepend=r"[B]Post text:[/B]"
    
            
                
            
    
            #helps the the textbox control treat [url description] and (url) as separate words. so that they can be separated into 2 lines 
            plot=h[3].replace('](', '] (')
            plot= markdown_to_bbcode(plot)
            plot=unescape(plot)  #convert html entities e.g.:(&#39;)
    
            liz=xbmcgui.ListItem(label=t_prepend + author + ': '+ desc100 , 
                                 label2="",
                                 iconImage="", 
                                 thumbnailImage="")
    
            liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": plot, "studio": domain, "votes": str(comment_score), "director": author } )

            

            #force all links to ytdl to see if it can be played
            if link_url:
                #log('      there is a link from %s' %domain)
                if not ld: 
                    #log('      link is not supported ')
                    if use_ytdl_for_unknown_in_comments:
                        log('      ********* activating unsupported link:' + link_url)
                        #domain='[?]'
                        liz.setProperty('item_type','script')         
                        liz.setProperty('onClick_action', build_script('playYTDLVideo', link_url) )
                        plot= "[COLOR greenyellow][%s] %s"%('?', plot )  + "[/COLOR]"
                        liz.setLabel(tab+plot)
                        liz.setProperty('link_url', link_url )  #just used as text at bottom of the screen

                        clearart=ret_info_type_icon('', '')
                        liz.setArt({ "clearart": clearart  })

            
            if ld:
                #use clearart to indicate if link is video, album or image. here, we default to unsupported.
                #clearart=ret_info_type_icon(setInfo_type, mode_type)
                clearart=ret_info_type_icon(ld.media_type, ld.link_action, domain )
                liz.setArt({ "clearart": clearart  })
            
                if ld.link_action == sitesBase.DI_ACTION_PLAYABLE:
                    property_link_type=ld.link_action
                    DirectoryItem_url =ld.playable_url
                else:
                    property_link_type='script'
                    DirectoryItem_url = build_script(mode=ld.link_action, 
                                                     url=ld.playable_url, 
                                                     name='' , 
                                                     type='' ) 
                
                #(score, link_desc, link_http, post_text, post_html, d, )
                #list_item_name=str(h[0]).zfill(3)
                
                #log(str(i)+"  score:"+ str(h[0]).zfill(5)+" desc["+ h[1] +']|text:['+ h[3]+']' +link_url + '  videoID['+videoID+']' + 'playable:'+ setProperty_IsPlayable )
                #log( h[4] + ' -- videoID['+videoID+']' )
                #log("sss:"+ supportedPluginUrl )
                
                #fl= re.compile('\[(.*?)\]\(.*?\)',re.IGNORECASE) #match '[...](...)' with a capture group inside the []'s as capturegroup1
                #result = fl.sub(r"[B]\1[/B]", h[3])              #replace the match with [B] [/B] with capturegroup1 in the middle of the [B]'s


    
                #turn link green  
                if DirectoryItem_url:          
                    plot= "[COLOR greenyellow][%s] %s"%(domain, plot )  + "[/COLOR]"
                    liz.setLabel(tab+plot)
        
                    #if poster_url:
                    #    thumb_url=poster_url
                        
                    #if thumb_url: pass
                    #else: thumb_url="DefaultVideo.png"
                    
                    #liz.setArt({"thumb": thumb_url, "poster":thumb_url, "banner":thumb_url, "fanart":thumb_url, "landscape":thumb_url   })
                    liz.setArt({"thumb": ld.poster })
        
                    liz.setProperty('item_type',property_link_type)   #script or playable
                    liz.setProperty('onClick_action', DirectoryItem_url)  #<-- needed by the xml gui skin
                    liz.setProperty('link_url', link_url )  #just used as text at bottom of the screen
                    #liz.setPath(DirectoryItem_url) 
        
                    directory_items.append( (DirectoryItem_url, liz,) )
                    
                #xbmcplugin.addDirectoryItem(handle=pluginhandle,url=DirectoryItem_url,listitem=liz,isFolder=isFolder)
            else:
                #this section are for comments that have no links or unsupported links
                if not ShowOnlyCommentsWithlink:
                    #liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": plot, "studio": domain, "votes": str(h[0]), "director": author } )
                    #liz.setProperty('IsPlayable', 'false')
                    
                    directory_items.append( ("", liz, ) )
                    #xbmcplugin.addDirectoryItem(handle=pluginhandle,url="",listitem=liz,isFolder=False)
                
                #END section are for comments that have no links or unsupported links
    
    except Exception as e:
        log('  ' + str(e) )
        #xbmc.executebuiltin('XBMC.Notification("%s", "%s" )' %( e, 'Flickr' )  )        
        
    xbmc_busy(False)
    #for di in directory_items:
    #    log( str(di) )

    from resources.lib.guis import commentsGUI
    
    li=[]
    for di in directory_items:
        #log( '   %s-%s'  %(di[1].getLabel(), di[1].getProperty('onClick_action') ) )
        li.append( di[1] )
    
#     li.sort( key=getKey )
#     log("  sorted")
#     
#     for l in li:
#         log( '   %s-%s'  %(l.getLabel(), l.getProperty('onClick_action') ) )
            
        
    ui = commentsGUI('view_461_comments.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, id=55)
    #NOTE: the subreddit selection screen and comments screen use the same gui. there is a button that is only for the comments screen
    ui.setProperty('comments', 'yes')   #i cannot get the links button to show/hide in the gui class. I resort to setting a property and having the button xml check for this property to show/hide
    
    #ui = commentsGUI('view_463_comments.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, id=55)
    ui.title_bar_text=post_title
    ui.include_parent_directory_entry=False

    ui.doModal()
    del ui

harvest=[]
def r_linkHunter(json_node,d=0):
    from resources.lib.domains import url_is_supported
    from resources.lib.utils import unescape
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
            
            try: post_text=unescape( e['data']['body'].encode('utf-8') )
            except: post_text=""
            post_text=post_text.replace("\n\n","\n")
            
            try: post_html=unescape( e['data']['body_html'].encode('utf-8') )
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

            try: self_text=unescape( e['data']['selftext'].encode('utf-8') )
            except: self_text=""
            
            try: self_text_html=unescape( e['data']['selftext_html'].encode('utf-8') )
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
    keyboard = xbmc.Keyboard('sort=new&t=week&q=', translation(32005))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():  
        
        #search_string = urllib.quote_plus(keyboard.getText().replace(" ", "+"))
        search_string = keyboard.getText().replace(" ", "+")
        
        #sites_filter = site_filter_for_reddit_search()
        url = urlMain +"/search.json?" +search_string    #+ '+' + nsfw  # + sites_filter skip the sites filter

        listSubReddit(url, name, "")
        

def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')

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

def viewTallImage(image_url, width, height):
    from resources.lib.utils import unescape
    log( 'viewTallImage %s: %sx%s' %(image_url, width, height))
    #image_url=unescape(image_url) #special case for handling reddituploads urls
    #log( 'viewTallImage %s: %sx%s' %(image_url, width, height))

    xbmc_busy(False)
        
    can_quit=True
    if can_quit==True:
        useWindow=xbmcgui.WindowDialog()
        useWindow.setCoordinateResolution(0)
    
        try:
            w=int(float(width))
            h=int(float(height))
            optimal_h=int(h*1.5)
            #log( '    **' + repr(h))
            loading_img = xbmc.validatePath('/'.join((addon_path, 'resources', 'skins', 'Default', 'media', 'srr_busy.gif' )))
            
            img_control = xbmcgui.ControlImage(0, 800, 1920, optimal_h, '', aspectRatio=2)  #(values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)
            img_loading = xbmcgui.ControlImage(1820, 0, 100, 100, loading_img, aspectRatio=2)
    
            #the cached image is of lower resolution. we force nocache by using setImage() instead of defining the image in ControlImage()
            img_control.setImage(image_url, False)
                    
            useWindow.addControls( [ img_loading, img_control])
            #useWindow.addControl(  img_control )
            
            scroll_time=(int(h)/int(w))*20000
            
            img_control.setAnimations( [ 
                                        ('conditional', "condition=true effect=fade  delay=0    start=0   end=100   time=4000 "  ) ,
                                        ('conditional', "condition=true effect=slide delay=2000 start=0,-%d end=0,0 tween=sine easing=in time=%d pulse=true" %( (h*1.4), scroll_time) ),
                                        ]  )
            
            useWindow.doModal()
            useWindow.removeControls( [img_control,img_loading] )
            del useWindow
        except Exception as e:
            log("  EXCEPTION viewTallImage:="+ str( sys.exc_info()[0]) + "  " + str(e) )    
    
    else:
        # can be done this way but can't get keypress to exit animation
        useWindow = xbmcgui.Window( xbmcgui.getCurrentWindowId() )
        xbmc_busy(False)
        w=int(float(width))
        h=int(float(height))
        optimal_h=int(h*1.5)
        #log( '    **' + repr(h))
        loading_img = xbmc.validatePath('/'.join((addon_path, 'resources', 'skins', 'Default', 'media', 'srr_busy.gif' )))
         
        img_control = xbmcgui.ControlImage(0, 1080, 1920, optimal_h, '', aspectRatio=2)  #(values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)
        img_loading = xbmcgui.ControlImage(1820, 0, 100, 100, loading_img, aspectRatio=2)
     
        #the cached image is of lower resolution. we force nocache by using setImage() instead of defining the image in ControlImage()
        img_control.setImage(image_url, False)
        useWindow.addControls( [ img_loading, img_control])
        scroll_time=int(h)*(int(h)/int(w))*10
        img_control.setAnimations( [ 
                                    ('conditional', "condition=true effect=fade  delay=0    start=0   end=100   time=4000 "  ) ,
                                    ('conditional', "condition=true effect=slide delay=2000 start=0,0 end=0,-%d time=%d pulse=true" %( (h*1.6) ,scroll_time) ),
                                    ('conditional', "condition=true effect=fade  delay=%s   start=100 end=0     time=2000 " %(scroll_time*1.8) ) ,
                                    ]  )
        xbmc.sleep(scroll_time*2)
        useWindow.removeControls( [img_control,img_loading] )
    


def zoom_n_slide(image, width, height):
    from resources.lib.utils import calculate_zoom_slide
    #url=image, name=width, type=height
    log( 'zoom_n_slide %s: %sx%s' %(image, width, height))
    
    try:
        w=int(width)
        h=int(height)
        zoom,slide=calculate_zoom_slide(w,h)

        newWindow=xbmcgui.Window()
        newWindow.setCoordinateResolution(0)
        #ctl3=xbmcgui.ControlImage(0, 0, 1920, 1080, 'http://i.imgur.com/E0qPa3D.jpg', aspectRatio=2)
        ctl3=xbmcgui.ControlImage(0, 0, 1920, 1080, image, aspectRatio=2)
        newWindow.addControl(ctl3)

        scroll_time=int(height)*(int(height)/int(width))*2
        
        zoom_effect="effect=zoom loop=true delay=1000 center=960 end=%d time=1000" %zoom
        fade_effect="condition=true effect=slide delay=2000 start=0,0 end=0,-%d time=%d pulse=true" %(slide,scroll_time)
        
        ctl3.setAnimations([('WindowOpen', zoom_effect), ('conditional', fade_effect,) ])
        
        #newWindow.show()
        #xbmc.sleep(8000)
        newWindow.doModal()
        del newWindow
    except Exception as e:
        log("  EXCEPTION zoom_n_slide:="+ str( sys.exc_info()[0]) + "  " + str(e) )    
    

def callwebviewer(url, name, type):
    log( " callwebviewer")

    #this is how you call the webviewer addon. 
    #u="script.web.viewer, http://m.reddit.com/login"
    #xbmc.executebuiltin('RunAddon(%s)' %u )
    
    import resources.pyxbmct as pyxbmct

    # Create a window instance.
    window = pyxbmct.AddonFullWindow('Hello, World!')
    # Set the window width, height and the grid resolution: 2 rows, 3 columns.
    window.setGeometry(1920, 1080, 9, 16)
    
    #image is 1200x2220
    image=pyxbmct.Image('http://i.imgur.com/lYdRVRi.png', aspectRatio=2)
    
    window.placeControl(image, 0, 0, 9, 16 )
    
    #doesn't work. leaving it alone for now (7/27/2016)
    image.setAnimations([('WindowOpen', 'effect type="zoom" end="150" center="0" time="1800"')])
    
    #image.setAnimations([('WindowOpen', 'effect type="zoom" end="150" center="0" time="1800"',), 
    #                     ('WindowOpen', 'effect type="slide" end="2220"  delay="1800" time="1800"',)])

    
    # Connect a key action to a function.
    window.connect(pyxbmct.ACTION_NAV_BACK, window.close)
    # Show the created window.
    window.doModal()
    # Delete the window instance when it is no longer used.
    del window 

    log( " done callwebviewer")

def test_menu(url, name, type):
    log( "  test_menu:" + url)

    
    #liz = xbmcgui.ListItem("open webviewer", label2="", iconImage="DefaultFolder.png", thumbnailImage="", path="")
    #u=sys.argv[0]+"mode=callwebviewer&type="
    #xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=False)
    
    

#     from resources.lib.httpd import TinyWebServer
#       
#     log( "*******************starting httpd")
#     httpd = TinyWebServer('xyz')
#     httpd.create("localhost", 8090)
#     httpd.start()
#       
#     xbmc.sleep(30000)
#       
#     log( "*******************stopping httpd")    
#     httpd.stop()

def reddit_request( url ):
    #this function replaces     content = opener.open(url).read()
    #  for calls to reddit  

    
    #if there is a refresh_token, we use oauth.reddit.com instead of www.reddit.com
    if reddit_refresh_token:
        url=url.replace('www.reddit.com','oauth.reddit.com' )
        url=url.replace( 'np.reddit.com','oauth.reddit.com' )
        url=url.replace(       'http://',        'https://' )
        log( "  replaced reqst." + url + " + access token=" + reddit_access_token)
        
    req = urllib2.Request(url)

    #req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
    req.add_header('User-Agent', reddit_userAgent)   #userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"
    
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
        xbmc.executebuiltin('XBMC.Notification("%s", "%s" )' %( err.reason, url)  )
        log( str(err.reason) ) 
    
def reddit_get_refresh_token(url, name, type):
    #this function gets a refresh_token from reddit and keep it in our addon. this refresh_token is used to get 1-hour access tokens.
    #  getting a refresh_token is a one-time step
    
    #1st: use any webbrowser to  
    #  https://www.reddit.com/api/v1/authorize?client_id=hXEx62LGqxLj8w&response_type=code&state=RS&redirect_uri=http://localhost:8090/&duration=permanent&scope=read,mysubreddits
    #2nd: click allow and copy the code provided after reddit redirects the user 
    #  save this code in add-on settings.  A one-time use code that may be exchanged for a bearer token.
    code = addon.getSetting("reddit_code")
    #log("  user refresh token:"+reddit_refresh_token)
    #log("  user          code:"+code)
    
    if reddit_refresh_token and code:
        #log("  user already have refresh token:"+reddit_refresh_token)
        dialog = xbmcgui.Dialog()
        if dialog.yesno(translation(32411), translation(32412), translation(32413), translation(32414) ):
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
        req.add_header('User-Agent', reddit_userAgent)
         
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
#         req.add_header('User-Agent', reddit_userAgent)
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
        req.add_header('User-Agent', reddit_userAgent)
          
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
    from resources.lib.utils import convert_date
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
        req.add_header('User-Agent', reddit_userAgent)
          
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
    
    
def xbmc_busy(busy=True):
    if busy:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
    else:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        
    
def downloadurl( source_url, destination=""):
    try:
        filename,ext=parse_filename_and_ext_from_url(source_url)
        if destination=="":
            urllib.urlretrieve(source_url, filename+"."+ext)
        else:
            urllib.urlretrieve(source_url, destination)
        
    except:
        log("download ["+source_url+"] failed")


def dump(obj):
    for attr in dir(obj):
        if hasattr( obj, attr ):
            log( "obj.%s = %s" % (attr, getattr(obj, attr)))

def parameters_string_to_dict(parameters):
    #log('   ######' + str( urlparse.parse_qsl(parameters) )  )
    return dict( urlparse.parse_qsl(parameters) )
#     paramDict = {}
#     if parameters:
#         paramPairs = parameters[1:].split("&")
#         for paramsPair in paramPairs:
#             paramSplits = paramsPair.split('=')
#             if (len(paramSplits)) == 2:
#                 paramDict[paramSplits[0]] = paramSplits[1]
#     #log('   ######' + str( paramDict )  )
#     return paramDict

if __name__ == '__main__':
    # (10/2/2016) --- directly connecting to our databases is not allowed.
    #dbPath = getDbPath()
    #if dbPath:
    #    conn = sqlite3.connect(dbPath)
    #    c = conn.cursor()

    if len(sys.argv) > 1: 
        params=parameters_string_to_dict(sys.argv[1])
        #log("sys.argv[1]="+sys.argv[1]+"  ")        
    else: params={}

    mode   = params.get('mode', '')
    url    = params.get('url', '')
    typez  = params.get('type', '') #type is a python function, try not to use a variable name same as function
    name   = params.get('name', '')
    #xbmc supplies this additional parameter if our <provides> in addon.xml has more than one entry e.g.: <provides>video image</provides>
    #xbmc only does when the add-on is started. we have to pass it along on subsequent calls   
    # if our plugin is called as a pictures add-on, value is 'image'. 'video' for video 
    #content_type=urllib.unquote_plus(params.get('content_type', ''))   
    #ctp = "&content_type="+content_type   #for the lazy
    #log("content_type:"+content_type)
    
    #log("params="+sys.argv[1]+"  ")
#     log("----------------------")
#     log("params="+ str(params))
#     log("mode="+ mode)
#     log("type="+ typez) 
#     log("name="+ name)
#     log("url="+  url)
#     log("-----------------------")
    #from resources.lib.domains import playVineVideo, playVidmeVideo, playStreamable, playGfycatVideo
    #from resources.lib.domains import viewImage, playFlickr, listImgurAlbum, listTumblrAlbum, playInstagram, listEroshareAlbum, listVidbleAlbum, listImgboxAlbum, listAlbum
    from resources.lib.domains import viewImage, listAlbum
    from resources.lib.slideshow import autoSlideshow
    
    if mode=='':mode='index'  #default mode is to list start page (index)
    #plugin_modes holds the mode string and the function that will be called given the mode
    plugin_modes = {'index'                 : index
                    ,'listSubReddit'        : listSubReddit
                    ,'playVideo'            : playVideo           
                    ,'addSubreddit'         : addSubreddit         
                    ,'editSubreddit'        : editSubreddit         
                    ,'removeSubreddit'      : removeSubreddit      
                    ,'autoPlay'             : autoPlay
                    ,'autoSlideshow'        : autoSlideshow                           
                    ,'searchReddits'        : searchReddits          
                    ,'listAlbum'            : listAlbum        #slideshowAlbum
                    ,'viewImage'            : viewImage
                    ,'viewTallImage'        : viewTallImage                    
                    ,'listLinksInComment'   : listLinksInComment
                    ,'playYTDLVideo'        : playYTDLVideo
                    ,'zoom_n_slide'         : zoom_n_slide
                    ,'manage_subreddits'    : manage_subreddits
                    ,'callwebviewer'        : callwebviewer
                    ,'get_refresh_token'    : reddit_get_refresh_token
                    ,'get_access_token'     : reddit_get_access_token
                    ,'revoke_refresh_token' : reddit_revoke_refresh_token
                    }
    
    #'playYTDLVideo','listLinksInComment' takes a long time to complete. when these modes are called from the gui, a long xbmc.executebuiltin("ActivateWindow(busydialog)") is run
    #   we close the busy dialog if running other modes 
    #if not mode in ['playYTDLVideo','listLinksInComment']:
    #    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    
    #whenever a list item is clicked, this part handles it.
    plugin_modes[mode](url,name,typez)


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
$ git commit -m "[script.reddit.reader] 0.5.7"

On branch add-on-branch-name
Untracked files:
        plugin.video.reddit_viewer/                <------ error message

nothing added to commit but untracked files present

edipc@DESKTOP-5C55U1P MINGW64 ~/kodi stuff/repo-plugins (add-on-branch-name)
$ git add .    <---- did this to fix the error.

$ git commit -m "[script.reddit.reader] 0.5.7"  <------- this will now work


#Push your topic branch up to your fork:

git push origin add-on-branch-name

#Open a pull request with a clear title and description.

*** on browser: click on pull request
upper left : base fork: xbmc/repo-plugins         base:    jarvis
upper right: head fork: gedisony/repo-plugins     compare: add-on-branch-name
(click on green button create pull request)

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