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
import pprint

import requests

import threading

modes_that_use_ytdl=['mode=playYTDLVideo','mode=play']
try:
    if any(mode in sys.argv[2] for mode in modes_that_use_ytdl):   ##if 'mode=playYTDLVideo' in sys.argv[2] :
        import YDStreamExtractor      #note: you can't just add this import in code, you need to re-install the addon with <import addon="script.module.youtube.dl"        version="16.521.0"/> in addon.xml
        import urlresolver
except:
    pass

from urllib import urlencode


reload(sys)
sys.setdefaultencoding("utf-8")


addon         = xbmcaddon.Addon()
addon_path    = addon.getAddonInfo('path')
pluginhandle  = int(sys.argv[1])
addonID       = addon.getAddonInfo('id')  #plugin.video.reddit_viewer

WINDOW        = xbmcgui.Window(10000)

osWin         = xbmc.getCondVisibility('system.platform.windows')
osOsx         = xbmc.getCondVisibility('system.platform.osx')
osLinux       = xbmc.getCondVisibility('system.platform.linux')

if osWin:
    fd="\\"
else:
    fd="/"

socket.setdefaulttimeout(30)
opener = urllib2.build_opener()
reddit_userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"
reddit_clientID      ="hXEx62LGqxLj8w"
reddit_redirect_uri  ='http://localhost:8090/'   #specified when registering for a clientID
reddit_refresh_token =addon.getSetting("reddit_refresh_token")
reddit_access_token  =addon.getSetting("reddit_access_token") #1hour token


opener.addheaders = [('User-Agent', reddit_userAgent)]
urlMain = "https://www.reddit.com"

autoplayAll          = addon.getSetting("autoplayAll") == "true"
autoplayUnwatched    = addon.getSetting("autoplayUnwatched") == "true"
autoplayUnfinished   = addon.getSetting("autoplayUnfinished") == "true"
autoplayRandomize    = addon.getSetting("autoplayRandomize") == "true"

forceViewMode        = addon.getSetting("forceViewMode") == "true"
viewMode             = str(addon.getSetting("viewMode"))
comments_viewMode    = str(addon.getSetting("comments_viewMode"))
album_viewMode       = str(addon.getSetting("album_viewMode"))

hide_nsfw            = addon.getSetting("hide_nsfw") == "true"
domain_filter        = addon.getSetting("domain_filter")
subreddit_filter     = addon.getSetting("subreddit_filter")

r_AccessToken         = addon.getSetting("r_AccessToken")

sitemsPerPage        = addon.getSetting("itemsPerPage")
try: itemsPerPage = int(sitemsPerPage)
except: itemsPerPage = 50

itemsPerPage          = ["10", "25", "50", "75", "100"][itemsPerPage]
TitleAddtlInfo        = addon.getSetting("TitleAddtlInfo") == "true"   #Show additional post info on title</string>
HideImagePostsOnVideo = addon.getSetting("HideImagePostsOnVideo") == 'true' #<string id="30204">Hide image posts on video addon</string>
setting_hide_images = False

DoNotResolveLinks     = addon.getSetting("DoNotResolveLinks") == 'true'

CommentTreshold          = addon.getSetting("CommentTreshold")
try: int_CommentTreshold = int(CommentTreshold)
except: int_CommentTreshold = -1000    #if CommentTreshold can't be converted to int, show all comments

try:istreamable_quality=int(addon.getSetting("streamable_quality"))  #values 0 or 1
except:istreamable_quality=0
streamable_quality  =["full", "mobile"][istreamable_quality]       #https://streamable.com/documentation

cxm_show_comment_link     = addon.getSetting("cxm_show_comment_link") == "true"
cxm_show_comments         = addon.getSetting("cxm_show_comments") == "true"
cxm_show_go_to            = addon.getSetting("cxm_show_go_to") == "true"
cxm_show_new_from         = addon.getSetting("cxm_show_new_from") == "true"
cxm_show_add_shortcuts    = addon.getSetting("cxm_show_add_shortcuts") == "true"
cxm_show_filter_subreddit = addon.getSetting("cxm_show_filter_subreddit") == "true"
cxm_show_filter_domain    = addon.getSetting("cxm_show_filter_domain") == "true"
cxm_show_open_browser     = addon.getSetting("cxm_show_open_browser") == "true"

addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
subredditsFile      = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits")
subredditsPickle    = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits.pickle")  #new type of saving the settings

REQUEST_TIMEOUT=5 #requests.get timeout in seconds

if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)

def json_query(query, ret):
    try:
        xbmc_request = json.dumps(query)
        result = xbmc.executeJSONRPC(xbmc_request)
        if ret:
            return json.loads(result)['result']
        else:
            return json.loads(result)
    except:
        return {}

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
        str_sql='SELECT playCount FROM files WHERE strFilename LIKE ?'
        args=[url[:120]+'%']
        c.execute(str_sql,args)


        result = c.fetchone()
        if result:
            result = result[0]
            if result:
                return int(result)
            return 0
    return -1

def addSubreddit(subreddit, name, type):
    from resources.lib.utils import this_is_a_multireddit, format_multihub, colored_subreddit
    alreadyIn = False
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    if subreddit:
        for line in content:
            if line.lower()==subreddit.lower():
                alreadyIn = True
        if not alreadyIn:
            with open(subredditsFile, 'a') as fh:
                fh.write(subreddit+'\n')

            get_subreddit_entry_info(subreddit)
        xbmc.executebuiltin('XBMC.Notification("%s", "%s" )' %( colored_subreddit(subreddit), translation(30019)  ) )
    else:
        keyboard = xbmc.Keyboard('', translation(30001))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            subreddit = keyboard.getText()

            #cleanup user input. make sure /user/ and /m/ is lowercase
            if this_is_a_multireddit(subreddit):
                subreddit = format_multihub(subreddit)
            else:
                get_subreddit_entry_info(subreddit)

            for line in content:
                if line.lower()==subreddit.lower()+"\n":
                    alreadyIn = True

            if not alreadyIn:
                fh = open(subredditsFile, 'a')
                fh.write(subreddit+'\n')
                fh.close()
        xbmc.executebuiltin("Container.Refresh")

def get_subreddit_entry_info(subreddit):
    if subreddit.lower() in ['all','random','randnsfw']:
        return
    s=[]
    if '/' in subreddit:  #we want to get diy from diy/top or diy/new
        subreddit=subreddit.split('/')[0]

    if '+' in subreddit:
        s.extend(subreddit.split('+'))
    else:
        s.append(subreddit)

    t = threading.Thread(target=get_subreddit_entry_info_thread, args=(s,) )
    t.start()

def get_subreddit_entry_info_thread(sub_list):
    from resources.lib.utils import get_subreddit_info, load_dict, save_dict

    subreddits_dlist=[]
    if os.path.exists(subredditsPickle):
        subreddits_dlist=load_dict(subredditsPickle)

    for subreddit in sub_list:
        subreddits_dlist=[x for x in subreddits_dlist if x.get('entry_name') != subreddit.lower() ]

        sub_info=get_subreddit_info(subreddit)

        log('****sub_info ' + repr( sub_info ))

        if sub_info:
            subreddits_dlist.append(sub_info)
            save_dict(subreddits_dlist, subredditsPickle)

def removeSubreddit(subreddit, name, type):
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    contentNew = ""
    for line in content:
        if line!=subreddit+'\n':
            contentNew+=line
    fh = open(subredditsFile, 'w')
    fh.write(contentNew)
    fh.close()
    xbmc.executebuiltin("Container.Refresh")

def editSubreddit(subreddit, name, type):
    from resources.lib.utils import this_is_a_multireddit, format_multihub
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    contentNew = ""

    keyboard = xbmc.Keyboard(subreddit, translation(30003))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        newsubreddit = keyboard.getText()
        if this_is_a_multireddit(newsubreddit):
            newsubreddit = format_multihub(newsubreddit)
        else:
            get_subreddit_entry_info(newsubreddit)

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
    from resources.lib.utils import load_subredditsFile, parse_subreddit_entry, create_default_subreddits, assemble_reddit_filter_string,xstr, ret_sub_info, samealphabetic, hassamealphabetic

    ## this is where the main screen is created
    content = ""
    if not os.path.exists(subredditsFile):  #if not os.path.exists(subredditsFile):
        create_default_subreddits()

    subredditsFile_entries=load_subredditsFile()

    subredditsFile_entries.sort(key=lambda y: y.lower())

    addtl_subr_info={}

    xbmcplugin.setContent(pluginhandle, "mixed") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos

    next_mode='listSubReddit'

    for subreddit_entry in subredditsFile_entries:
        addtl_subr_info=ret_sub_info(subreddit_entry)

        entry_type, subreddit, alias, shortcut_description=parse_subreddit_entry(subreddit_entry)

        #url= urlMain+"/r/"+subreddit+"/.json?"+nsfw+allHosterQuery+"&limit="+itemsPerPage
        url= assemble_reddit_filter_string("",subreddit, "yes")
        if subreddit.lower() == "all":
            addDir(subreddit, url, next_mode, "", subreddit, { "plot": translation(30009) } )  #Displays the currently most popular content from all of reddit....
        else:
            if addtl_subr_info: #if we have additional info about this subreddit
                title=addtl_subr_info.get('title')+'\n'
                display_name=xstr(addtl_subr_info.get('display_name'))
                if samealphabetic( title, display_name): title=''

                header_title=xstr(addtl_subr_info.get('header_title'))
                public_description=xstr( addtl_subr_info.get('public_description'))

                if samealphabetic( header_title, public_description): public_description=''
                if samealphabetic(title,public_description): public_description=''

                shortcut_description='[COLOR cadetblue][B]r/%s[/B][/COLOR]\n%s[I]%s[/I]\n%s' %(display_name,title,header_title,public_description )

                icon=addtl_subr_info.get('icon_img')
                banner=addtl_subr_info.get('banner_img')
                header=addtl_subr_info.get('header_img')  #usually the small icon on upper left side on subreddit screen

                icon=next((item for item in [icon,banner,header] if item ), '')

                addDirR(alias, url, next_mode, icon,
                        type=subreddit,
                        listitem_infolabel={ "plot": shortcut_description },
                        file_entry=subreddit_entry,
                        banner_image=banner )
            else:
                addDirR(alias, url, next_mode, "", subreddit, { "plot": shortcut_description }, subreddit_entry )

    addDir("[B]- "+translation(30001)+"[/B]", "", 'addSubreddit', "", "", { "plot": translation(30006) } ) #"Customize this list with your favorite subreddit."
    addDir("[B]- "+translation(30005)+"[/B]", "",'searchReddits', "", "", { "plot": translation(30010) } ) #"Search reddit for a particular post or topic

    xbmcplugin.endOfDirectory(pluginhandle)

def listSubReddit(url, name, subreddit_key):
    from resources.lib.utils import unescape, strip_emoji, pretty_datediff, post_is_filtered_out, ret_sub_icon, has_multiple_subreddits

    show_listVideos_debug=True
    credate = ""
    is_a_video=False
    title_line2=""
    log("listSubReddit subreddit=%s url=%s" %(subreddit_key,url) )
    t_on = translation(30071)  #"on"
    t_pts='c'

    thumb_w=0
    thumb_h=0

    currentUrl = url
    xbmcplugin.setContent(pluginhandle, "movies") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos


    dialog_progress = xbmcgui.DialogProgressBG()
    dialog_progress_heading='Loading'
    dialog_progress.create(dialog_progress_heading )
    dialog_progress.update(0,dialog_progress_heading, subreddit_key  )

    content = reddit_request(url)

    if not content:
        return

    page_title="[COLOR cadetblue]%s[/COLOR]" %subreddit_key

    #setPluginCategory lets us show text at the top of window, we take advantage of this and put the subreddit name
    xbmcplugin.setPluginCategory(pluginhandle, page_title)

    info_label={ "plot": translation(30013) }  #Automatically play videos
    if autoplayAll:       addDir("[B]- "+translation(30016)+"[/B]", url, 'autoPlay', "", "ALL", info_label)
    if autoplayUnwatched: addDir("[B]- "+translation(30017)+"[/B]" , url, 'autoPlay', "", "UNWATCHED", info_label)

    content = json.loads(content)

    posts_count=len(content['data']['children'])

    hms = has_multiple_subreddits(content['data']['children'])

    for idx, entry in enumerate(content['data']['children']):
        try:
            if post_is_filtered_out( entry ):
                continue

            title = unescape(entry['data']['title'].encode('utf-8'))
            title = strip_emoji(title) #an emoji in the title was causing a KeyError  u'\ud83c'

            try:    description = unescape(entry['data']['media']['oembed']['description'].encode('utf-8'))
            except: description = ''
            try:    post_selftext=unescape(entry['data']['selftext'].encode('utf-8'))
            except: post_selftext=''

            description=post_selftext+'[CR]'+description if post_selftext else description

            commentsUrl = urlMain+entry['data']['permalink'].encode('utf-8')

            try:
                aaa = entry['data']['created_utc']
                credate = datetime.datetime.utcfromtimestamp( aaa )
                now_utc = datetime.datetime.utcnow()
                pretty_date=pretty_datediff(now_utc, credate)
                credate = str(credate)
            except:
                credate = ""
                credateTime = ""

            subreddit=entry['data']['subreddit'].encode('utf-8')

            try: author = entry['data']['author'].encode('utf-8')
            except: author = ""
            #if show_listVideos_debug :log("     AUTHOR"+str(idx)+"="+author)

            try: domain= entry['data']['domain'].encode('utf-8')
            except: domain = ""

            ups = entry['data']['score']       #downs not used anymore
            try:num_comments = entry['data']['num_comments']
            except:num_comments = 0

            try:
                media_url = entry['data']['url'].encode('utf-8')
            except:
                media_url = entry['data']['media']['oembed']['url'].encode('utf-8')

            thumb = entry['data']['thumbnail'].encode('utf-8')

            if thumb in ['nsfw','default','self']:  
                thumb=""

            if thumb=="":
                try: thumb = entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8').replace('&amp;','&')
                except: pass

            if thumb=="":  #use this subreddit's icon if thumb still empty
                try: thumb=ret_sub_icon(subreddit)
                except: pass

            try:
                preview=entry['data']['preview']['images'][0]['source']['url'].encode('utf-8').replace('&amp;','&')
                try:
                    thumb_h = float( entry['data']['preview']['images'][0]['source']['height'] )
                    thumb_w = float( entry['data']['preview']['images'][0]['source']['width'] )
                except:
                    thumb_w=0
                    thumb_h=0

            except Exception as e:
                thumb_w=0
                thumb_h=0
                preview="" 

            is_a_video = determine_if_video_media_from_reddit_json(entry)

            try:
                over_18 = entry['data']['over_18']
            except:
                over_18 = False

            title_line2=""

            title_line2 = "[I][COLOR dimgrey]%s %s [COLOR cadetblue]r/%s[/COLOR] (%d) %s[/COLOR][/I]" %(pretty_date,t_on, subreddit,num_comments, t_pts)

            if show_listVideos_debug : log("  POST%cTITLE%.2d=%s" %( ("v" if is_a_video else " "), idx, title ))

            loading_percentage=int((float(idx)/posts_count)*100)
            dialog_progress.update( loading_percentage,dialog_progress_heading, title  )

            addLink(title=title,
                    title_line2=title_line2,
                    iconimage=thumb,
                    previewimage=preview,
                    preview_w=thumb_w,
                    preview_h=thumb_h,
                    domain=domain,
                    description=description,
                    credate=credate,
                    reddit_says_is_video=is_a_video,
                    commentsUrl=commentsUrl,
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

    dialog_progress.update( 100,dialog_progress_heading  )
    dialog_progress.close() #it is important to close xbmcgui.DialogProgressBG

    try:
        after=""
        after = content['data']['after']
        if "&after=" in currentUrl:
            nextUrl = currentUrl[:currentUrl.find("&after=")]+"&after="+after
        else:
            nextUrl = currentUrl+"&after="+after
        info_label={ "plot": translation(30004) + '[CR]' + page_title}
        addDir(translation(30004), nextUrl, 'listSubReddit', "", subreddit_key,info_label)   #Next Page
    except:
        pass

    subreddit_key=subreddit_key.replace(' ','+')
    viewID=WINDOW.getProperty( "viewid-"+subreddit_key )

    if viewID:
        log("  custom viewid %s for %s " %(viewID,subreddit_key) )
        xbmc.executebuiltin('Container.SetViewMode(%s)' %viewID )
    else:
        if forceViewMode:
            xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

    xbmcplugin.endOfDirectory(handle=pluginhandle,
                              succeeded=True,
                              updateListing=False,   #setting this to True causes the ".." entry to quit the plugin
                              cacheToDisc=True)

def addLink(title, title_line2, iconimage, previewimage,preview_w,preview_h,domain,description, credate, reddit_says_is_video, commentsUrl, subreddit, media_url, over_18, posted_by="", num_comments=0,post_index=1,post_total=1,many_subreddit=False ):
    from resources.lib.domains import parse_reddit_link, build_DirectoryItem_url_based_on_media_type

    videoID=""
    post_title=title
    il_description=""
    n=""  #will hold red nsfw asterisk string
    h=""  #will hold bold hoster:  string
    t_Album = translation(30073) if translation(30073) else "Album"
    t_IMG =  translation(30074) if translation(30074) else "IMG"

    ok = False

    isFolder=True
    thumb_url=''

    h="[B]" + domain + "[/B]: "
    if over_18:
        mpaa="R"
        n = "[COLOR red]*[/COLOR] "
        il_description = "[COLOR red][NSFW][/COLOR] "+ h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"
    else:
        mpaa=""
        n=""
        il_description = h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"

    if TitleAddtlInfo:     
        log( repr(title_line2 ))
        post_title=n+title+"[CR]"+title_line2
    else:
        post_title=n+title
        il_description=title_line2+"[CR]"+il_description

    il={"title": post_title, "plot": il_description, "plotoutline": il_description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": domain, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin

    liz=xbmcgui.ListItem(label=post_title)

    liz.setInfo(type='video', infoLabels=il)

    if iconimage in ["","nsfw", "default"]:
        iconimage=thumb_url

    preview_ar=0.0
    if (preview_w==0 or preview_h==0) != True:
        preview_ar=float(preview_w) / preview_h

    if previewimage: needs_preview=False
    else:            needs_preview=True  

    if DoNotResolveLinks:
        ld=None
        DirectoryItem_url=sys.argv[0]\
            +"?url="+ urllib.quote_plus(media_url) \
            +"&name="+urllib.quote_plus(title) \
            +"&mode=play"
        setProperty_IsPlayable='true'
        isFolder=False
        title_prefix=''
    else:
        ld=parse_reddit_link(media_url,reddit_says_is_video, needs_preview, False, preview_ar  )

        if needs_preview and ld:
            queried_preview_image= next((i for i in [ld.poster,ld.thumb] if i ), '')
            previewimage=queried_preview_image

        arg_name=title
        arg_type=previewimage
        if ld:
            if iconimage in ["","nsfw", "default"]: iconimage=ld.thumb

        DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld,
                                                                                                                        media_url,
                                                                                                                        arg_name,
                                                                                                                        arg_type,
                                                                                                                        script_to_call="",
                                                                                                                        on_autoplay=False,
                                                                                                                        img_w=preview_w,
                                                                                                                        img_h=preview_h)
    if title_prefix:
        liz.setLabel( title_prefix+' '+post_title )

    liz.setProperty('IsPlayable', setProperty_IsPlayable)
    liz.setInfo('video', {"title": liz.getLabel(), } )

    liz.setArt({"thumb": iconimage, "poster":previewimage, "banner":iconimage, "fanart":previewimage, "landscape":previewimage, })

    entries = build_context_menu_entries(num_comments, commentsUrl, many_subreddit, subreddit, domain, media_url) #entries for listbox for when you type 'c' or rt-click

    liz.addContextMenuItems(entries)
    xbmcplugin.addDirectoryItem(pluginhandle, DirectoryItem_url, listitem=liz, isFolder=isFolder, totalItems=post_total)

    return ok

def build_context_menu_entries(num_comments,commentsUrl, many_subreddit, subreddit, domain, link_url):
    from resources.lib.utils import assemble_reddit_filter_string,subreddit_in_favorites, colored_subreddit

    s=(subreddit[:12] + '..') if len(subreddit) > 12 else subreddit     #crop long subreddit names in context menu
    colored_subreddit_short=colored_subreddit( s )
    colored_subreddit_full=colored_subreddit( subreddit )
    colored_domain_full=colored_subreddit( domain, 'tan',False )
    entries=[]

    if cxm_show_open_browser:
            entries.append( ( translation(30509),  #Open in browser
                              "XBMC.RunPlugin(%s?mode=openBrowser&url=%s)" % ( sys.argv[0],  urllib.quote_plus( link_url ) ) ) )

    if cxm_show_comment_link or cxm_show_comments:
        if num_comments > 0:
            if cxm_show_comment_link:
                entries.append( ( translation(30052) , #Show comment links
                                  "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s&type=linksOnly)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )
            if cxm_show_comments:
                entries.append( ( translation(30050) ,  #Show comments
                                  "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )
        else:
            entries.append( ( translation(30053) ,  #No comments
                          "xbmc.executebuiltin('Action(Close)')" ) )

    if many_subreddit and cxm_show_go_to:
        entries.append( ( translation(30051)+" %s" %colored_subreddit_full ,
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listSubReddit&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit,True)  ) ) ) )

    if cxm_show_new_from:
        entries.append( ( translation(30055)+" %s" %colored_subreddit_short ,
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listSubReddit&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit+'/new',True)  ) ) ) )

    if cxm_show_add_shortcuts: 
        if not subreddit_in_favorites(subreddit):
            entries.append( ( translation(30056) %colored_subreddit_short ,
                              "XBMC.RunPlugin(%s?mode=addSubreddit&url=%s)" % ( sys.argv[0], subreddit ) ) )

    if cxm_show_filter_subreddit:
            entries.append( ( translation(30057) %colored_subreddit_short ,
                              "XBMC.RunPlugin(%s?mode=addtoFilter&url=%s&type=%s)" % ( sys.argv[0], subreddit, 'subreddit' ) ) )
    if cxm_show_filter_domain:
            entries.append( ( translation(30057) %colored_domain_full ,
                              "XBMC.RunPlugin(%s?mode=addtoFilter&url=%s&type=%s)" % ( sys.argv[0], domain, 'domain' ) ) )
    return entries

def autoPlay(url, name, autoPlay_type):
    from resources.lib.domains import sitesBase, parse_reddit_link, ydtl_get_playable_url, build_DirectoryItem_url_based_on_media_type, setting_gif_repeat_count
    from resources.lib.utils import unescape, post_is_filtered_out

    gif_repeat_count=setting_gif_repeat_count()

    entries = []
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    log("**********autoPlay %s*************" %autoPlay_type)
    content = reddit_request(url)
    if not content: return

    content = json.loads(content.replace('\\"', '\''))

    log("Autoplay %s - Parsing %d items" %( autoPlay_type, len(content['data']['children']) )    )

    for j_entry in content['data']['children']:
        try:
            if post_is_filtered_out( j_entry ):
                continue

            title = unescape(j_entry['data']['title'].encode('utf-8'))

            try:
                media_url = j_entry['data']['url']
            except:
                media_url = j_entry['data']['media']['oembed']['url']

            is_a_video = determine_if_video_media_from_reddit_json(j_entry)

            ld=parse_reddit_link(link_url=media_url, assume_is_video=False, needs_preview=False, get_playable_url=True )

            DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld, media_url, title, on_autoplay=True)

            if ld:
                if ld.media_type not in [sitesBase.TYPE_VIDEO, sitesBase.TYPE_GIF, sitesBase.TYPE_VIDS, sitesBase.TYPE_MIXED]:
                    continue

            autoPlay_type_entries_append( entries, autoPlay_type, title, DirectoryItem_url)
            if ld.media_type == sitesBase.TYPE_GIF:
                for x in range( 0, gif_repeat_count ):
                    autoPlay_type_entries_append( entries, autoPlay_type, title, DirectoryItem_url)

        except Exception as e:
            log("  EXCEPTION Autoplay "+ str( sys.exc_info()[0]) + "  " + str(e) )

    if autoplayRandomize:
        random.shuffle(entries)

    for title, url in entries:
        listitem = xbmcgui.ListItem(title)
        playlist.add(url, listitem)
        log('add to playlist: %s %s' %(title.ljust(25)[:25],url ))
    xbmc.Player().play(playlist)

def autoPlay_type_entries_append( entries, autoPlay_type, title, playable_url):
    if autoPlay_type=="ALL":
        entries.append([title,playable_url])
    elif autoPlay_type=="UNWATCHED" and getPlayCount(playable_url) <= 0:
        entries.append([title,playable_url])

def determine_if_video_media_from_reddit_json( entry ):
    is_a_video=False

    try:
        media_url = entry['data']['media']['oembed']['url']   #+'"'
    except:
        media_url = entry['data']['url']   #+'"'

    media_url=media_url.split('?')[0] #get rid of the query string
    try:
        zzz = entry['data']['media']['oembed']['type']
        if zzz == None:   
            if ".gifv" in media_url.lower():  
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

def playVideo(url, name, type):
    if url :
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    else:
        log("playVideo(url) url is blank")

def playYTDLVideo(url, name, type):
    from urlparse import urlparse
    parsed_uri = urlparse( url )
    domain = '{uri.netloc}'.format(uri=parsed_uri)

    dialog_progress_YTDL = xbmcgui.DialogProgressBG()
    dialog_progress_YTDL.create('YTDL' )
    dialog_progress_YTDL.update(10,'YTDL','Checking link...' )

    try:
        from resources.lib.domains import ydtl_get_playable_url
        stream_url = ydtl_get_playable_url(url)
        if stream_url:
            dialog_progress_YTDL.update(80,'YTDL', 'Playing' )
            listitem = xbmcgui.ListItem(path=stream_url[0])   #plugins play video like this.
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
            dialog_progress_YTDL.update(40,'YTDL', 'Trying URLResolver' )
            log('YTDL Unable to get playable URL, Trying UrlResolver...' )

            #ytdl seems better than urlresolver for getting the playable url...
            media_url = urlresolver.resolve(url)
            if media_url:
                dialog_progress_YTDL.update(88,'YTDL', 'Playing' )
                #log( '------------------------------------------------urlresolver stream url ' + repr(media_url ))
                listitem = xbmcgui.ListItem(path=media_url)
                xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
            else:
                log('UrlResolver cannot get a playable url' )
                xbmc.executebuiltin('XBMC.Notification("%s", "%s" )'  %( translation(30192), domain )  )

    except Exception as e:
        xbmc.executebuiltin('XBMC.Notification("%s(YTDL)","%s")' %(  domain, str(e))  )
    finally:
        dialog_progress_YTDL.update(100,'YTDL' ) #not sure if necessary to set to 100 before closing dialogprogressbg
        dialog_progress_YTDL.close()

def listLinksInComment(url, name, type):
    from resources.lib.domains import parse_reddit_link, sitesBase, build_DirectoryItem_url_based_on_media_type
    from resources.lib.utils import markdown_to_bbcode, unescape, ret_info_type_icon, build_script
    log('listLinksInComment:%s:%s' %(type,url) )

    directory_items=[]
    author=""
    ShowOnlyCommentsWithlink=False

    if type=='linksOnly':
        ShowOnlyCommentsWithlink=True

    url=urllib.quote_plus(url,safe=':/')
    url+='.json'

    content = reddit_request(url)
    if not content: return

    content = json.loads(content)

    del harvest[:]
    #harvest links in the post text (just 1)
    r_linkHunter(content[0]['data']['children'])

    try:submitter=content[0]['data']['children'][0]['data']['author']
    except: submitter=''

    try:post_title=content[0]['data']['children'][0]['data']['title']
    except:post_title=''
    r_linkHunter(content[1]['data']['children'])

    comment_score=0
    for i, h in enumerate(harvest):
        try:
            comment_score=h[0]
            link_url=h[2]
            desc100=h[3].replace('\n',' ')[0:100] #first 100 characters of description

            kind=h[6] #reddit uses t1 for user comments and t3 for OP text of the post. like a poster describing the post.
            d=h[5]   #depth of the comment

            tab=" "*d if d>0 else "-"

            from urlparse import urlparse
            domain = '{uri.netloc}'.format( uri=urlparse( link_url ) )

            author=h[7]
            DirectoryItem_url=''

            if comment_score < int_CommentTreshold:
                continue

            ld=parse_reddit_link(link_url=link_url, assume_is_video=False, needs_preview=True, get_playable_url=True )

            if kind=='t1':
                list_title=r"[COLOR cadetblue]%3d[/COLOR] %s" %( h[0], tab )
            elif kind=='t3':
                list_title=r"[COLOR cadetblue]Title [/COLOR] %s" %( tab )
            plot=h[3].replace('](', '] (')
            plot= markdown_to_bbcode(plot)
            plot=unescape(plot)  #convert html entities e.g.:(&#39;)

            liz=xbmcgui.ListItem(label=list_title +': '+ desc100 )

            liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": plot, "studio": domain, "votes": str(comment_score), "director": author  } )
            isFolder=False

            if link_url:

                DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld, link_url)

                liz.setProperty('IsPlayable', setProperty_IsPlayable)
                liz.setProperty('url', DirectoryItem_url)  
                liz.setPath(DirectoryItem_url)

                if domain:
                    plot= "  [COLOR greenyellow][%s] %s"%(domain, plot )  + "[/COLOR]"
                else:
                    plot= "  [COLOR greenyellow][%s]"%( plot ) + "[/COLOR]"
                liz.setLabel(list_title+plot)

                if ld:
                    liz.setArt({"thumb": ld.poster, "poster":ld.poster, "banner":ld.poster, "fanart":ld.poster, "landscape":ld.poster   })

            if DirectoryItem_url:
                directory_items.append( (DirectoryItem_url, liz, isFolder,) )
            else:
                if not ShowOnlyCommentsWithlink:
                    result=h[3].replace('](', '] (')
                    result=markdown_to_bbcode(result)
                    liz=xbmcgui.ListItem(label=list_title + desc100)
                    liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": result, "studio": domain, "votes": str(h[0]), "director": author } )
                    liz.setProperty('IsPlayable', 'false')

                    directory_items.append( ("", liz, False,) )
        except Exception as e:
            log('  EXCEPTION:' + str(e) )

    log('  comments_view id=%s' %comments_viewMode)

    xbmcplugin.setContent(pluginhandle, "movies")    #files, songs, artists, albums, movies, tvshows, episodes, musicvideos
    xbmcplugin.setPluginCategory(pluginhandle,'Comments')

    xbmcplugin.addDirectoryItems(handle=pluginhandle, items=directory_items )
    xbmcplugin.endOfDirectory(pluginhandle)

    if comments_viewMode:
        xbmc.executebuiltin('Container.SetViewMode(%s)' %comments_viewMode)


harvest=[]
def r_linkHunter(json_node,d=0):
    from resources.lib.utils import unescape
    prog = re.compile('<a href=[\'"]?([^\'" >]+)[\'"]>(.*?)</a>')
    for e in json_node:
        link_desc=""
        link_http=""
        author=""
        created_utc=""
        if e['kind']=='t1':     #'t1' for comments   'more' for more comments (not supported)

            body=e['data']['body'].encode('utf-8')

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

            result = prog.findall(post_html)
            if result:
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )

                for link_http,link_desc in result:
                    harvest.append((score, link_desc, link_http, link_desc, post_html, d, "t1",author,created_utc,)   )
            else:
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )

            d+=1 #d tells us how deep is the comment in
            r_linkHunter(replies,d)
            d-=1

        if e['kind']=='t3':     #'t3' for post text (a description of the post)
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
                    harvest.append((score, link_desc, link_http, link_desc, self_text_html, d, "t3",author,created_utc, )   )
            else:
                if len(self_text) > 0: #don't post an empty titles
                    harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",author,created_utc,)   )

#This handles the links sent via jsonrpc (i.e.: links sent by kore to kodi by calling)
# videoUrl = "plugin://script.reddit.reader/?mode=play&url=" + URLEncoder.encode(videoUri.toString(), "UTF-8");
def parse_url_and_play(url, name, type):
    from resources.lib.domains import parse_reddit_link, sitesBase, ydtl_get_playable_url, build_DirectoryItem_url_based_on_media_type
    from resources.lib.domains import viewImage
    isFolder=False

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    ld=parse_reddit_link(url,True, False, False  )

    DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld, url)

    if setProperty_IsPlayable=='true':
        log( '---------IsPlayable---------->'+ DirectoryItem_url)
        playVideo(DirectoryItem_url,'','')
    else:
        if isFolder: #showing album
            log( '---------using ActivateWindow------>'+ DirectoryItem_url)
            xbmc.executebuiltin('ActivateWindow(Videos,'+ DirectoryItem_url+')')
        else:  #viewing image
            log( '---------using setResolvedUrl------>'+ DirectoryItem_url)
            listitem = xbmcgui.ListItem(path='')
            listitem.setProperty('IsPlayable', 'false')
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

            xbmc.executebuiltin('RunPlugin(%s)' % ( DirectoryItem_url ) )

def queueVideo(url, name, type):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)

def searchReddits(url, name, type):
    keyboard = xbmc.Keyboard('sort=new&t=week&q=', translation(30005))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():

        search_string = keyboard.getText().replace(" ", "+")

        url = urlMain +"/search.json?" +search_string    #+ '+' + nsfw  # + sites_filter skip the sites filter

        listSubReddit(url, name, "")


def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def addDir(name, url, mode, iconimage, type="", listitem_infolabel=None, label2=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type)
    ok = True
    liz = xbmcgui.ListItem(label=name, label2=label2)

    if listitem_infolabel==None:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    else:
        liz.setInfo(type="Video", infoLabels=listitem_infolabel)


    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def addDirR(name, url, mode, icon_image='', type="", listitem_infolabel=None, file_entry="", banner_image=''):

    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type)
    #log('addDirR='+u)
    ok = True
    liz = xbmcgui.ListItem(name)

    if icon_image:
        liz.setArt({ 'thumb': icon_image, 'icon': icon_image, 'clearlogo': icon_image  })  #thumb is used in 'shift' view (estuary)   thunb,icon are interchangeable in list view

    if banner_image:
        liz.setArt({ 'banner': banner_image  })
        liz.setArt({ 'fanart': banner_image  })

    if listitem_infolabel==None:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    else:
        liz.setInfo(type="Video", infoLabels=listitem_infolabel)

    if file_entry:
        liz.setProperty("file_entry", file_entry)

    liz.addContextMenuItems([(translation(30003), 'RunPlugin(plugin://'+addonID+'/?mode=editSubreddit&url='+urllib.quote_plus(file_entry)+')',)     ,
                             (translation(30002), 'RunPlugin(plugin://'+addonID+'/?mode=removeSubreddit&url='+urllib.quote_plus(file_entry)+')',)
                             ])

    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def reddit_request( url ):
    if reddit_refresh_token:
        url=url.replace('www.reddit.com','oauth.reddit.com' )
        log( "  replaced reqst." + url + " + access token=" + reddit_access_token)

    req = urllib2.Request(url)

    req.add_header('User-Agent', reddit_userAgent)   #userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"

    if reddit_refresh_token:
        req.add_header('Authorization','bearer '+ reddit_access_token )

    try:
        page = urllib2.urlopen(req)
        response=page.read();page.close()
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
                    log( err.msg )
                except urllib2.URLError, err:
                    log( err.msg )
            else:
                log( "*** failed to get new access token - don't know what to do " )


        xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, url)  )
        log( err.reason )
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        xbmc.executebuiltin('XBMC.Notification("%s", "%s" )' %( err.msg, url)  )
        log( err.msg )

def reddit_get_refresh_token(url, name, type):
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

        data = urllib.urlencode({'grant_type'  : 'authorization_code'
                                ,'code'        : code                     #'woX9CDSuw7XBg1MiDUnTXXQd0e4'
                                ,'redirect_uri': reddit_redirect_uri})    #http://localhost:8090/

        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', reddit_userAgent)

        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()
        log( response )

        status=reddit_set_addon_setting_from_response(response)

        if status=='ok':
            r1="Click 'OK' when done"
            r2="Settings will not be saved"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( r1, r2)  )
        else:
            r2="Requesting a reddit permanent token"
            xbmc.executebuiltin("XBMC.Notification(%s, %s)"  %( status, r2)  )

    except urllib2.HTTPError, err:
        xbmc.executebuiltin('XBMC.Notification("%s %s", "%s" )' %( err.code, err.msg, u)  )
        log( err.reason )
    except urllib2.URLError, err: # Not an HTTP-specific error (e.g. connection refused)
        log( err.reason )

def reddit_get_access_token(url="", name="", type=""):
    try:
        log( "Requesting a reddit 1-hour token" )

        req = urllib2.Request('https://www.reddit.com/api/v1/access_token')

        data = urllib.urlencode({'grant_type'    : 'refresh_token'
                                ,'refresh_token' : reddit_refresh_token })                    #'woX9CDSuw7XBg1MiDUnTXXQd0e4'
        import base64
        base64string = base64.encodestring('%s:%s' % (reddit_clientID, '')).replace('\n', '')
        req.add_header('Authorization',"Basic %s" % base64string)
        req.add_header('User-Agent', reddit_userAgent)

        page = urllib2.urlopen(req, data=data)
        response=page.read();page.close()
        #log( response )

        status=reddit_set_addon_setting_from_response(response)

        if status=='ok':
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
            return response['error']
        else:
            if 'refresh_token' in response:  #refresh_token only returned when getting reddit_get_refresh_token. it is a one-time step
                reddit_refresh_token = response['refresh_token']
                addon.setSetting('reddit_refresh_token', reddit_refresh_token)

            reddit_access_token = response['access_token']
            addon.setSetting('reddit_access_token', reddit_access_token)

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


DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')

def xbmc_busy(busy=True):
    if busy:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
    else:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

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

    if HideImagePostsOnVideo: # and content_type=='video':
        setting_hide_images=True

    log( "----------------v" + addon.getAddonInfo('version')  + ' ' + ( mode+': '+url if mode else '' ) +'-----------------')

    from resources.lib.domains import viewImage, listAlbum, viewTallImage, playURLRVideo, loopedPlayback,error_message
    from resources.lib.slideshow import autoSlideshow
    from resources.lib.utils import addtoFilter,open_web_browser
    

    if mode=='':mode='index'  #default mode is to list start page (index)
    plugin_modes = {'index'                 : index
                    ,'listSubReddit'        : listSubReddit
                    ,'playVideo'            : playVideo
                    ,'addSubreddit'         : addSubreddit
                    ,'editSubreddit'        : editSubreddit
                    ,'removeSubreddit'      : removeSubreddit
                    ,'autoPlay'             : autoPlay
                    ,'viewImage'            : viewImage
                    ,'viewTallImage'        : viewTallImage
                    ,'listAlbum'            : listAlbum
                    ,'addtoFilter'          : addtoFilter
                    ,'openBrowser'          : open_web_browser
                    ,'listLinksInComment'   : listLinksInComment
                    ,'playYTDLVideo'        : playYTDLVideo
                    ,'playURLRVideo'        : playURLRVideo
                    ,'loopedPlayback'       : loopedPlayback
                    ,'error_message'        : error_message
                    ,'get_refresh_token'    : reddit_get_refresh_token
                    ,'get_access_token'     : reddit_get_access_token
                    ,'revoke_refresh_token' : reddit_revoke_refresh_token
                    ,'play'                 : parse_url_and_play
                    }
    #whenever a list item is clicked, this part handles it.
    plugin_modes[mode](url,name,typez)

