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
import SimpleDownloader
import requests
import YDStreamExtractor      #note: you can't just add this import in code, you need to re-install the addon with <import addon="script.module.youtube.dl"        version="16.521.0"/> in addon.xml
from urllib import urlencode

#YDStreamExtractor.disableDASHVideo(True) #Kodi (XBMC) only plays the video for DASH streams, so you don't want these normally. Of course these are the only 1080p streams on YouTube

reload(sys)
sys.setdefaultencoding("utf-8")

addon         = xbmcaddon.Addon()
addon_path    = addon.getAddonInfo('path')
pluginhandle  = int(sys.argv[1])
addonID       = addon.getAddonInfo('id')  #plugin.video.reddit_viewer

osWin         = xbmc.getCondVisibility('system.platform.windows')
osOsx         = xbmc.getCondVisibility('system.platform.osx')
osLinux       = xbmc.getCondVisibility('system.platform.linux')

if osWin:
    fd="\\"
else:
    fd="/"

socket.setdefaulttimeout(30)
opener = urllib2.build_opener()
#https://github.com/reddit/reddit/wiki/API
userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"
opener.addheaders = [('User-Agent', userAgent)]
urlMain = "http://www.reddit.com"

cat_bypass= True  #addon.getSetting("cat_bypass") == "true"  permanently remove categories screen (allow user to specify new/controversial/hot day/week/month/year)

show_youtube     = addon.getSetting("show_youtube") == "true"
use_ytdl_for_yt  = addon.getSetting("use_ytdl_for_yt") == "true"    #let youtube_dl addon handle youtube videos. this bypasses the age restriction prompt
show_vimeo       = addon.getSetting("show_vimeo") == "true"
show_liveleak    = addon.getSetting("show_liveleak") == "true"
show_dailymotion = addon.getSetting("show_dailymotion") == "true"
show_gfycat      = addon.getSetting("show_gfycat") == "true"
show_imgur       = addon.getSetting("show_imgur") == "true"
show_i_redd_it   = addon.getSetting("show_i_redd_it") == "true"
show_reddituploads=addon.getSetting("show_reddituploads") == "true"
show_vine        = addon.getSetting("show_vine") == "true"
show_streamable  = addon.getSetting("show_streamable") == "true"
show_vidme       = addon.getSetting("show_vidme") == "true"
show_instagram   = addon.getSetting("show_instagram") == "true"
show_blogspot    = addon.getSetting("show_blogspot") == "true"
show_pornsites   = addon.getSetting("show_pornsites") == "true"
show_reddit_com  = addon.getSetting("show_reddit_com") == "true"
show_ytdl_misc   = addon.getSetting("show_ytdl_misc") == "true"
show_tumblr      = addon.getSetting("show_tumblr") == "true"
show_giphy       = addon.getSetting("show_giphy") == "true"
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

itemsPerPage = int(addon.getSetting("itemsPerPage"))
itemsPerPage = ["10", "25", "50", "75", "100"][itemsPerPage]
TitleAddtlInfo = addon.getSetting("TitleAddtlInfo") == "true"   #Show additional post info on title</string>
HideImagePostsOnVideo = addon.getSetting("HideImagePostsOnVideo") == 'true' #<string id="30204">Hide image posts on video addon</string>
setting_hide_images = False

searchSort = int(addon.getSetting("searchSort"))
searchSort = ["ask", "relevance", "new", "hot", "top", "comments"][searchSort]
searchTime = int(addon.getSetting("searchTime"))
searchTime = ["ask", "hour", "day", "week", "month", "year", "all"][searchTime]

#--- settings related to context menu "Show Comments"
ShowOnlyCommentsWithlink = addon.getSetting("ShowCommentsWithlink") == "true"
CommentTreshold          = addon.getSetting("CommentTreshold") 
try: int_CommentTreshold = int(CommentTreshold)
except: int_CommentTreshold = -1000    #if CommentTreshold can't be converted to int, show all comments 

showBrowser     = addon.getSetting("showBrowser") == "true"
browser_win     = int(addon.getSetting("browser_win"))
browser_wb_zoom = str(addon.getSetting("browser_wb_zoom"))

ll_qualiy  = int(addon.getSetting("ll_qualiy"))
ll_qualiy  = ["480p", "720p"][ll_qualiy]
ll_downDir = str(addon.getSetting("ll_downDir"))

istreamable_quality =int(addon.getSetting("streamable_quality"))  #values 0 or 1
streamable_quality = ["full", "mobile"][istreamable_quality]       #https://streamable.com/documentation

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

site00 = [show_youtube      , "playVideo"          ,'YouTube'      ,'(?:youtube(?:-nocookie)?\.com/(?:\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&;]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'    ,"plugin://plugin.video.youtube/play/?video_id=##vidID##"                , "site:youtu.be OR site:youtube.com" ]
#ite01 = [show_youtube      , "playVideo"          ,'YouTube'      ,'https?://www.youtube.com/attribution_link\?a=(.*)&'                                                          ,"plugin://plugin.video.youtube/play/?video_id=##vidID##"                , ""                      ] #leave the second site filter blank
site01 = [show_giphy        , "direct"             ,'Giphy'        ,'https?://(?:.+).giphy.com/'     ,"(not used)##vidID##"                                                   , "site:giphy.com"        ] 
site02 = [show_vimeo        , "playVideo"          ,'Vimeo'        ,'vimeo.com/(.*)'                 ,"plugin://plugin.video.vimeo/play/?video_id=##vidID##"                  , "site:vimeo.com"        ]
site03 = [show_dailymotion  , "playVideo"          ,'DailyMotion'  ,'dailymotion.com/video/(.*)_?'   ,"plugin://plugin.video.dailymotion_com/?mode=playVideo&url=##vidID##"   , "site:dailymotion.com"  ]
site04 = [show_dailymotion  , "playVideo"          ,'DailyMotion'  ,'dailymotion.com/.+?video=(.*)'  ,"plugin://plugin.video.dailymotion_com/?mode=playVideo&url=##vidID##"   , ""                      ]
site05 = [show_liveleak     , "playLiveLeakVideo"  ,'LiveLeak'     ,'liveleak.com/view\\?i=(.*)'     ,"##vidID##"                                                             , "site:liveleak.com"     ]
site06 = [show_gfycat       , "playGfycatVideo"    ,'Gfycat'       ,'gfycat.com/(.*)'                ,"##vidID##"                                                             , "site:gfycat.com"       ]
site07 = [show_imgur        , "playImgurVideo"     ,'Imgur'        ,'imgur\.com\/(.*)'               ,"##vidID##"                                                             , "site:imgur.com"        ]
site08 = [show_i_redd_it    , "playSlideshow"      ,'Redd.it'      ,'i.redd.it\/(.*)'                ,"##vidID##"                                                             , "site:redd.it"        ]
site09 = [show_reddituploads, "playSlideshow"      ,'RedditMedia'  ,'\.(?:reddituploads|redditmedia).com/(.+)'       ,"##vidID##"                                             , "site:redditmedia.com"        ]
site10 = [show_vine         , "playVineVideo"      ,'Vine'         ,'vine\.co\/(.*)'                 ,"(not used) ##vidID##"                                                  , "site:vine.co"        ]
site11 = [show_streamable   , "playStreamable"     ,'Streamable'   ,'streamable\.com/(.*)'           ,"(not used) ##vidID##"                                                  , "site:streamable.com"        ]
site12 = [show_vidme        , "playVidmeVideo"     ,'Vidme'        ,'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]*)' ,"(not used) ##vidID##"                                     , "site:vid.me"        ]
site13 = [show_instagram    , "playYTDLVideo"      ,'Instagram'    ,'(?P<url>https?://(?:www\.)?instagram\.com/p/(?P<id>[^/?#&]+))' ,"(not used) ##vidID##"                   , "site:Instagram.com"        ]
site14 = [show_blogspot     , "play"               ,'Blogspot'     ,'(https?://.*\.blogspot\.com/.*)(jpg|gif|png)'       ,"(not used) ##vidID##"                              , "site:blogspot.com"        ]
site15 = [show_reddit_com   , "playReddit"         ,'Reddit.com'   ,'reddit.com'                    ,"##vidID##"                                                              , "site:reddit.com"        ]
site16 = [show_tumblr       , "done in code"       ,'Tumblr'       ,'tumblr.com'                     ,"##vidID##"                                                             , "site:tumblr.com"        ]
site30 = [show_ytdl_misc    , "playYTDLVideo"      ,'misc'         ,"(funnyclips.me)|(engagemedia.org)|(videosift.com)|(break.com)|(veoh.com)|(viddler.com)|(schooltube.com)|(videos.sapo.pt)|(funnyordie.com)","(not used) ##vidID##", ""        ]
site31 = [show_pornsites    , "playYTDLVideo"      ,'porn'         ,"(3movs.com)|(anysex.com)|(cliphunter.com)|(crocotube.com)|(cutegirlsgifs.info)|(daporn.com)|(drtuber.com)|(efukt.com)|(eroshare.com)|(faapy.com)|(fapality.com)|(faptube.xyz)|(gyazo.com)|(hclips.com)|(hotgoo.com)|(japan-whores.com)|(mofosex.com)|(mylust.com)|(onlypron.com)|(panapin.com)|(porndoe.com)|(porneq.com)|(pornfun.com)|(pornhd.com)|(pornhub.com)|(porntrex.com)|(pussy.com)|(redclip.xyz)|(redtube.com)|(secret.sex)|(sendvid.com)|(sex24open.com)|(sex3.com)|(sexfactor.com)|(shameless.com)|(smotri.com)|(spankbang.com)|(stickyxxx.com)|(submityourflicks.com)|(teenfucktory.com)|(thisvid.com)|(tnaflix.com)|(tube8.com)|(txxx.com)|(vporn.com)|(worldsex.com)|(xbabe.com)|(xbabe.com)|(xcafe.com)|(xcum.com)|(xhamster.com)|(xnxx.com)|(xtube.com)|(xvideos.com)|(xvids.us)|(xxxymovies.com)|(xxxyours.com)|(youporn.com)|(zedporn.com)","(not used) ##vidID##", ""        ]
site18 = [0,''              , "video" ,''            ,''                               ,""                                                                      , ""                      ]
 
supported_sites = [site00,site01,site02,site03,site04,site05,site06,site07,site08,site09,site10,site11,site12,site13,site14,site15,site16,site30,site31]

#used to filter out image links if content_type is video (when this addon is called from pictures)
image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp'] #exclude 'gif' as we consider it as gifv

keys=[ 'li_label'           #  the text that will show for the list
      ,'li_label2'          #  
      ,'li_iconImage'       #
      ,'li_thumbnailImage'  #
      ,'DirectoryItem_url'  #  
      ,'is_folder'          # 
      ,'type'               # video pictures  liz.setInfo(type='pictures',
      ,'isPlayable'         # key:value       liz.setProperty('IsPlayable', 'true')  #there are other properties but we only use this 
      ,'infoLabels'         # {"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin
      ,'context_menu'       # ...
      ]


class ClassImgur:
    #use this header for interacting with the imgur api
    #get client id by registering at https://api.imgur.com/oauth2/addclient
    request_header={ "Authorization": "Client-Id a594f39e5d61396" }
    
    #when is_an_album() is called to check a /gallery/ link, we ask imgur; it returns more info than needed, we store some of it here   
    is_an_album_type=""
    is_an_album_link=""
    
    def __init__(self):
        #log("init")
        return

    def playImgurVideo(self, id, name, type):
        #  ***no longer used. left here for reference
        
        url='http://i.imgur.com/'+id   #the id could be aaa or aaa.gif or aaa.mp4 or aaa.jpg etc.
        idr=id.split('.')[0]
        try:
            id_ext=id.split('.')[1]    
        except:
            id_ext=''
        
        #log("playImgurVideo["+id+"]")
        content = opener.open("http://i.imgur.com/"+idr).read()
        if content :
            #log('content read ')
            match = re.compile('imgur_video=(.+?)&', re.DOTALL).findall(content)
            if match:
                url = urllib.unquote_plus(match[0])
                playVideo(url,name, type)
            
            else:    
                log('no match for imgur_video=(.+?)&')
                id=id.replace("/gallery/","/")
    
                xbmcplugin.setContent(pluginhandle, 'pictures')
                
                if id_ext =='jpg' or id_ext =='png' or id_ext =='gif' :
                    #log('detected image:'+id_ext)  
                    url ='http://i.imgur.com/'+id
                    listitem = xbmcgui.ListItem(path=url)
                    listitem.setProperty('IsPlayable', 'false')    
                    listitem.setInfo(type='image', infoLabels={})
                    xbmcplugin.setContent(pluginhandle, 'files')
                else:
                    #just append .mp4 or .webm  and animated gif will play 
                    #log('not jpg extension' + url)  
                    url ='http://i.imgur.com/'+id+'.jpg'             
                    listitem = xbmcgui.ListItem(path=url)
                    listitem.setProperty('IsPlayable', 'false')    
                    listitem.setInfo(type='image', infoLabels={})
        
                #attempt to display image/unknowntype anyway
                xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

    def is_an_album(self, media_url):
        #determins if an imgur url is an album
        
        #links with an /a/ is an album e.g: http://imgur.com/a/3SaoS
        if "/a/" in media_url:
            return True

        #links with /gallery/ is trickier. sometimes it is an album sometimes it is just one image
        #filename,ext=parse_filename_and_ext_from_url(media_url) #there is no need to check for filename if there is /gallery/
        if '/gallery/' in media_url:
            gallery_name = media_url.split("/gallery/",1)[1]
            if gallery_name=="": 
                return False
        else:  #'gallery' not found in media url
            return False
    
        request_url="https://api.imgur.com/3/gallery/"+gallery_name 
        #log("check is album- request_url---"+request_url )
        r = requests.get(request_url, headers=ClassImgur.request_header)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j = r.json()    #j = json.loads(r.text)
            #log(" is_album=" + str(j['data']['is_album'])    ) 
            #log(" in_gallery=" + str(j['data']['in_gallery'])    )

            #we already incurred the bandwidth asking imgur about album info. might as well use the data provided
            if 'type' in j['data']:
                self.is_an_album_type = j['data']['type']   #"image/png"
                
            if 'link' in j['data']:
                self.is_an_album_link= j['data']['link']
                
            #this link (https://imgur.com/gallery/VNPcuYP) returned an extra 'h' on j['data']['link']  ("http:\/\/i.imgur.com\/VNPcuYPh.gif") 
            #causing the video not to play. so, we grab mp4 link if present
            if 'mp4' in j['data']:
                self.is_an_album_link= j['data']['mp4']
            
            #sometimes 'is_album' key is not returned, so we also check for 'in_gallery' 
            if 'is_album' in j['data']:
                is_album_key=j['data']['is_album']
                return is_album_key
            else:
                try:in_gallery_key=j['data']['in_gallery']
                except: in_gallery_key=False
                return in_gallery_key
            
            
        else: #status code not 200... what to do... 
            return True  #i got a 404 on one item that turns out to be an album when checked in browser. i'll just return true

    def ask_imgur_for_link(self, media_url):
        #sometimes, imgur links are posted without the extension(gif,jpg etc.). we ask imgur for it.

        media_url=media_url.split('?')[0] #get rid of the query string
        img_id =media_url.split("com/",1)[1]  #.... just get whatever is after "imgur.com/"   hope nothing is beyond the id

        request_url="https://api.imgur.com/3/image/"+img_id
        #log("check link- request_url---"+request_url )
        r = requests.get(request_url, headers=ClassImgur.request_header)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j = r.json()    #j = json.loads(r.text)
        
            #log('link is ' + j['data'].get('link') )
            return j['data'].get('link')
        

    def ret_thumb_url(self, image_url, thumbnail_type='b'):
        #return the thumbnail url given the image url
        #accomplished by appending a 'b' at the end of the filename       
        #this won't work if there is a '/gallery/' in the url

        #possible thumbnail_types
        #    s = Small Square (90×90) 
        #    b = Big Square (160×160)
        #    t = Small Thumbnail (160×160)
        #    m = Medium Thumbnail (320×320)
        #    l = Large Thumbnail (640×640) 
        #    h = Huge Thumbnail (1024×1024)
        
        from urlparse import urlparse
        o=urlparse(image_url)    #from urlparse import urlparse
        filename,ext=parse_filename_and_ext_from_url(image_url) 
        #log("file&ext------"+filename+"--"+ext+"--"+o.netloc )
        
        #imgur url's sometimes do not have an extension and we don't know if it is an image or video
        if ext=="":
            #log("ret_thumb_url["+ o.path[1:] ) #starts with / use [1:] to skip 1st character
            filename = o.path[1:]
            ext = 'jpg'
        elif ext in {'gif', 'gifv', 'webm', 'mp4'}:
            ext = 'jpg'
        
        #return o.scheme+"://"+o.netloc+"/"+filename+ thumbnail_type +"."+ext  
        return ("%s://%s/%s%c.%s" % \
                ( o.scheme, o.netloc, filename, thumbnail_type, ext ) )

    def ret_album_list(self, album_url, thumbnail_size_code='b'):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem
        # see ret_thumb_url for thumbnail_size_code values

        #album_url="http://imgur.com/a/fsjam"
        #sometimes album name has "/new" at the end
        
        album_name=""
        dictList = []

        #m=re.match(r'imgur\.com/(?:a|gallery)/(.*)?/?', album_url)
        match = re.compile(r'imgur\.com/(?:a|gallery)/(.*)/?', re.DOTALL).findall(album_url)

        if match:
            album_name = match[0]  #album_url.split("/a/",1)[1]
        else:
            log(r"ret_album_list: Can't determine album name from["+album_url+"]" )
            return dictList
        #log('album name:'+album_name+' from ['+album_url+']')
        request_url="https://api.imgur.com/3/album/"+album_name+"/images"
        #log("listImgurAlbum-request_url---"+request_url )
        r = requests.get(request_url, headers=ClassImgur.request_header)
        
        if r.status_code==200:  #http status code 200 = success
            #log(r.text)
            j = r.json()   #json.loads(r.text)    
            
            #2 types of json received:
            #first, data is an array of objects 
            #second, data has 'images' which is the array of objects
            if 'images' in j['data']:
                imgs=j['data']['images']
            else:
                imgs=j['data']
            
            
            for idx, entry in enumerate(imgs):
                type       =entry['type']         #image/jpeg
                
                media_url  =str( entry['link'] )         #http://i.imgur.com/gpnMihj.jpg
                try: description=entry['description'].encode('utf-8')
                except: description=""
                #log("----description is "+description)
                filename,ext=parse_filename_and_ext_from_url(media_url)
                
                if description=='' or description==None:
                    #log("description is blank")
                    description=filename+"."+ext
                
                media_thumb_url=self.ret_thumb_url(media_url,thumbnail_size_code)
                #log("media_url----"+media_url) 
                #log("media_thumb_url----"+media_thumb_url)
                #log(str(idx)+type+" [" + str(description)+']'+media_url+" "  ) 
                list_item_name= entry['title'] if entry['title'] else str(idx).zfill(2)
                
                infoLabels={ "Title": list_item_name, "plot": description, "PictureDesc": description, "exif:exifcomment": description }
                e=[ description             #'li_label'           #  the text that will show for the list (we use description because most albumd does not have entry['type']
                   ,list_item_name          #'li_label2'          #  
                   ,""                      #'li_iconImage'       #
                   ,media_thumb_url         #'li_thumbnailImage'  #
                   ,media_url               #'DirectoryItem_url'  #  
                   ,False                   #'is_folder'          # 
                   ,'pictures'              #'type'               # video pictures  liz.setInfo(type='pictures',
                   ,True                    #'isPlayable'         # key:value       liz.setProperty('IsPlayable', 'true')  #there are other properties but we only use this 
                   ,infoLabels              #'infoLabels'         # {"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin
                   ,'none'                  #'context_menu'       # ...
                      ]

                """
                    keys = ['FirstName', 'LastName', 'SSID']
                     
                    name1 = ['Michael', 'Kirk', '224567']
                    name2 = ['Linda', 'Matthew', '123456']
                     
                    dictList = []
                    dictList.append(dict(zip(keys, name1)))
                    dictList.append(dict(zip(keys, name2)))
                     
                    print dictList
                    for item in dictList:
                        print ' '.join([item[key] for key in keys])
                """
                dictList.append(dict(zip(keys, e)))

        return dictList    
    
        
    def media_id(self, media_url):
        #return the media id from an imbur link
        log("aaa")
        
    def is_imgur_url(self,url_to_test):
        #returns true if url_to_test is from imgur (accdg. to make_addon_url_from function)
        match = re.compile( site07[3]  , re.DOTALL).findall(url_to_test)  #hoster, supportedPluginUrl, videoID, mode_type = make_addon_url_from(url_to_test)
        if match:                                                         #if hoster == 'Imgur':
            return True
        else:
            return False
    
    def prep_media_url(self, media_url, is_probably_a_video): #is_probably_a_video means put video extension on it if media_url has no ext
        #returns a tuple; the media url (with proper ext) and is_a_video true/false
        #returned media url will be 'album' if link is determined to be an album
        #returned media url will be '' if link is not imgur
        webm_or_mp4='.mp4'  #6/18/2016  using ".webm" has stopped working
        
        if not self.is_imgur_url(media_url):
            return "", False
            
        is_video=False
        media_url=media_url.split('?')[0] #get rid of the query string?

        is_album=self.is_an_album(media_url)
        #log('  imgur says is_an_album:'+str(is_album))
        if is_album:
            return "album", False                #  addDir(name=n+"[Album] "+post_title,   url=media_url,   mode="listImgurAlbum",  iconimage=iconimage,  type="",   listitem_infolabel=il)
        else:
            if '/gallery/' in media_url: 
                #media_url=media_url.replace("/gallery/","/")
                #is_an_album will ask imgur if a link has '/gallery/' in it and stores it in is_an_album_link
                media_url=self.is_an_album_link
                log('  media_link from /gallery/: '+str(media_url))

        filename,ext=parse_filename_and_ext_from_url(media_url) 

        #if is_probably_a_video=='yes': #is_a_video accdg. to the reddit json.
        if ext == "":
            #ask imgur for the media link
            media_url=self.ask_imgur_for_link(media_url)

            #below is a faster alternative but not as accurate.             
            #if is_probably_a_video:  #reddit thinks this is a video 
            #    media_url=media_url+ webm_or_mp4               
            #    is_video=True
            #else:
            #    media_url=media_url+".jpg"               
            #    is_video=False
                
        if ext in {'gif', 'gifv'} :
            media_url=media_url.replace(".gifv",webm_or_mp4) #can also use .mp4.  crass but this method uses no additional bandwidth.  see playImgurVideo
            media_url=media_url.replace(".gif",webm_or_mp4)  #xbmc won't play gif but replacing .webm works!
            is_video=True
            #lizb.setInfo(type='video', infoLabels=il)
        elif ext in image_exts:    #image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp']
            is_video=False
        else:
            is_video=False
            
        #log("    video media url return=["+media_url+']')
        return media_url, is_video

class ClassVidme:
    
    #request_header={ "Authorization": "Basic " + base64_encode($key . ':') }
    request_header={ "Authorization": "Basic aneKgeMUCpXv6FdJt8YGRznHk4VeY6Ps:" }
    media_status=""
    
    def __init__(self, media_url):
        return
    
    def prep_media_url(self,media_url, is_probably_a_video):
        #https://docs.vid.me/#api-Video-DetailByURL
        #request_url="https://api.vid.me/videoByUrl/"+videoID
        request_url="https://api.vid.me/videoByUrl?url="+ urllib.quote_plus( media_url )
        
        #log("vidme request_url---"+request_url )
        r = requests.get(request_url, headers=ClassImgur.request_header)
        log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j = r.json()    #j = json.loads(r.text)

            #for attribute, value in j.iteritems():
            #    log(  str(attribute) + '==' + str(value))
            status = j['video'].get( 'state' )
            
            log( "    vidme video state: " + status ) #success / suspended / deleted
            self.media_status=status
                
            return ( j['video']['complete_url'] )
            
        else: #status code not 200... what to do... 
            log("vidme request returned not ok status")
            return True  #i got a 404 on one item that turns out to be an album when checked in browser. i'll just return true

    def whats_wrong(self):
        return str( self.media_status )

class ClassVine:
    def __init__(self,media_url):
        return 
    
    def prep_media_url(self, media_url, is_probably_a_video=True):
        #asks vimeo about the url
        
        #media_url='"image": "https://v.cdn.vine.co/r/videos/38B4A9174D1177703702723739648_37968e655a0.1.5.1461921223578533188.mp4.jpg?versionId=hv6zBo4kGHPH8NdQeJVo_JRGSVXV73Cc"'
        #msp=re.compile('videos\/(.*?\.mp4)')
        msp=re.compile('(https?://.*/videos/.*?\.mp4)') 
        match=msp.findall(media_url)
        if match:
            #the media_url from reddit already leads to the actual stream, no need to ask vine
            #log('match [%s]' %match[0])
            return media_url   #return 'https://v.cdn.vine.co/r/videos/'+match[0]
    
        #request_url="https://vine.co/oembed.json?url="+media_url   won't work. some streams can't be easily "got" by removing the .jpg at the end 
        request_url=media_url
        #log("prep_media_url vine- request_url---"+request_url )
        r = requests.get(request_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            """
            #there are parsed characters(\u2122 etc.) in r.text that causes errors somewhere else in the code.  
            #matches the json script from the reply
            json_match=re.compile('<script type=\"application\/ld\+json\">\s*([\s\S]*?)<\/script>' , re.DOTALL).findall(r.text)
            if json_match:
                #log(json_match[0])
                #the text returned causes a json parsing error, we fix them below before decoding 
                #use this site to find out where the decoding failed https://jsonformatter.curiousconcept.com/
                jt = json_match[0].replace('"name" : ,','"name" : "",').encode('ascii', errors='ignore')   #('utf-8')
                j=json.loads(jt)
                contentUrl=j['sharedContent']['contentUrl']
                thumbnailUrl=j['sharedContent']['thumbnailUrl']

            """
            m_strm=re.compile('"contentUrl"\s:\s"(https?://.*?\.mp4.*?)"').findall(r.text)
            if m_strm:
                contentUrl=m_strm[0]
                #log('matched:'+ contentUrl )
            #m_thumb=re.compile('"thumbnailUrl"\s:\s"(https?://.*?\.jpg)\?').findall(r.text)
            #if m_thumb:
            #    thumbnailUrl=m_thumb[0]

            return contentUrl
            
            #log('vine type %s thumbnail_url[%s]' %(type, thumbnail_url) )
        return

class ClassStreamable:
    
    videoID=""
    re_videoID=re.compile('streamable\.com/(.*)')
    
    def __init__(self, media_url):
        m=self.re_videoID.findall(media_url)
        if m:
            self.videoID=m[0]
        return
    
    def prep_media_url(self, media_url, is_probably_a_video=True):
        #check if provided url links directly to the stream
        #https://streamable.com/dw9f 
        #   becomes --> https://streamable.com/video/mp4/dw9f.mp4  or  https://streamable.com/video/webm/dw9f.webm
        #   thumbnail -->     //cdn.streamable.com/image/dw9f.jpg 
        #this is the streamable api https://api.streamable.com/videos/dw9f
        
        msp=re.compile('(https?://.*?\.(mp4|webm))') 
        match=msp.findall(media_url)
        if match:
            log('media_url already streamable [%s]' % str(match[0]) )
            return media_url   

        url_mp4=""
        url_mp4m=""
        url_webm=""
        url_webmm=""
        
        api_url='https://api.streamable.com/videos/%s' %self.videoID
        r = requests.get(api_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            #log("success")
            j=json.loads(r.text.replace('\\"', '\''))
            
            if j.get('files'):  #we are not guaranteed that 'mp4-mobile' etc. exists.
                if j['files'].get('mp4'):
                    url_mp4=j['files']['mp4']['url']
                if j['files'].get('mp4-mobile'):
                    url_mp4m=j['files']['mp4-mobile']['url']
                if j['files'].get('webm'):
                    url_webm=j['files']['mp4']['url']
                if j['files'].get('webm-mobile'):
                    url_webmm=j['files']['mp4-mobile']['url']

                #use mp4 if mp4 is present else use mp4mobile then if it is still empty, use webm versions
                url_hq=url_mp4 if url_mp4 else url_mp4m
                if url_hq=="":
                    url_hq=url_webm if url_webm else url_webmm
                
                url_mq=url_mp4m if url_mp4m else url_mp4
                if url_mq=="":
                    url_mq=url_webmm if url_webmm else url_webm

                #finally if no hq available use mq
                if url_hq=="": url_hq=url_mq
                if url_mq=="": url_mq=url_hq
                
                if streamable_quality=='full' :
                    return "https:" + url_hq
                else:
                    return "https:" + url_mq

    def ret_thumb_url(self, image_url="", thumbnail_type='b'):
        return "https://cdn.streamable.com/image/%s.jpg" %self.videoID

class ClassTumblr:
    def __init__(self, media_url=""):
        return
    
    api_key='no0FySaKYuQHKl0EBQnAiHxX7W0HY4gKvlmUroLS2pCVSevIVy'
    thumb_url=""
    
    def ret_thumb_url(self, image_url="", thumbnail_type='b'):
        #call this after calling prep_media_url
        return self.thumb_url
    
    def prep_media_url(self, media_url, is_probably_a_video=True ):
        #log('class tumblr prep media url')

        #first, determine if the media_url leads to a media(.jpg .png .gif)
        filename,ext=parse_filename_and_ext_from_url(media_url)
        if ext in image_exts:
            return media_url,"photo"
        elif ext in {"mp4","gif"}:
            return media_url,"video"

        # don't check for media.tumblr.com because
        #there are instances where medis_url is "https://vt.tumblr.com/tumblr_o1jl6p5V5N1qjuffn_480.mp4#_=_"
#         if 'media.tumblr.com' in media_url:
#             if ext in image_exts:
#                 return media_url,"photo"
#             elif ext in {"mp4","gif"}:
#                 return media_url,"video"
        if "www.tumblr.com" in media_url:   #warning:nsfw!!  https://www.tumblr.com/video/johncena2014/144096330849/500/  
            match = re.findall('https?://www.tumblr.com/(?:post|image|video)/(.+?)/(.+?)(?:/|$)',media_url)
        else:
            match = re.findall('https?://(.*)\.tumblr.com/(?:post|image|video)/(.+?)(?:/|$)',media_url)

        blog_identifier = match[0][0]
        post_id         = match[0][1]

        api_url='http://api.tumblr.com/v2/blog/%s/posts?api_key=%s&id=%s' %(blog_identifier,self.api_key,post_id )
        #needs to look like this:   #see documentation  https://www.tumblr.com/docs/en/api/v2
        #url='http://api.tumblr.com/v2/blog/boo-rad13y/posts?api_key=no0FySaKYuQHKl0EBQnAiHxX7W0HY4gKvlmUroLS2pCVSevIVy&id=146015264096'
        #log('apiurl:'+api_url)
        
        r = requests.get(api_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j=json.loads(r.text.replace('\\"', '\''))
            
            #log("aaaaa "+ str( j['response']['blog']['url'])   )
            
            #this is only one post so no need to iterate through posts
            #for post in j['response']['posts']:
            post=j['response']['posts'][0]
            
            media_type=post['type']  #  text, photo, quote, link, chat, audio, video, answer 
            #log('  Tumblr media type: ' + post['type'])
            
            if media_type == 'photo':
                #log('len of photos ' + str(  len(post['photos']) )  )
                self.thumb_url=post['photos'][0]['alt_sizes'][1]['url']    #alt_sizes 0-5
                
                if len(post['photos'])==1: 
                    #log('media url: ' + post['photos'][0]['original_size']['url']  )
                    return post['photos'][0]['original_size']['url'], 'photo'  
                else:
                    dictList=[]
                    for i, photo in enumerate( post['photos'] ):
                        #log("%d %s" %(i, photo['original_size']['url'] ))
                        #p.append(photo['original_size']['url'])
    
                        infoLabels={ "Title": photo['caption'], "plot": photo['caption'], "PictureDesc": '', "exif:exifcomment": '' }
                        e=[ photo['caption'] if photo['caption'] else str(i+1) #'li_label'           #  the text that will show for the list  (list label will be the caption or number if caption is blank)
                           ,''                                                 #'li_label2'          #  
                           ,""                                                 #'li_iconImage'       #
                           ,photo['alt_sizes'][3]['url']                       #'li_thumbnailImage'  #
                           ,photo['original_size']['url']                      #'DirectoryItem_url'  #  
                           ,False                                              #'is_folder'          # 
                           ,'pictures'                                         #'type'               # video pictures  liz.setInfo(type='pictures',
                           ,True                                               #'isPlayable'         # key:value       liz.setProperty('IsPlayable', 'true')  #there are other properties but we only use this 
                           ,infoLabels                                         #'infoLabels'         # {"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin
                           ,'none'                                             #'context_menu'       # ...
                              ]
                    
                        dictList.append(dict(zip(keys, e)))
                        
                return dictList, 'album'
            elif media_type == 'video':
                self.thumb_url=post['thumbnail_url']
                return post['video_url'],media_type
            elif media_type == 'audio':
                return post['audio_url'],media_type
                    
        return "", media_type

class ClassBlogspot:
    media_is_an_image=False
    def __init__(self, media_url=""):
        return
    
    def prep_media_url(self, media_url, is_probably_a_video=True):
        #blogspot links point directly to the media we're interested. 
        #
        self.media_is_an_image=False
        contentUrl=""
        #https?://(?:.*)?\.blogspot\.com/(?:.*(jpg|gif|png))
        #we only grab the extension we support, likewise the regex is used(site14) to determine if the blogspot site(ext) is supported if match
        #the regex has 2 capture groups. the second one is the media extension  (https?://.*\.blogspot\.com/.*)(jpg|gif|png)
        m=re.compile(site14[3], re.IGNORECASE) 
        bs_ext=m.findall(media_url )
        
        if bs_ext:
            try:
                ext=bs_ext[0][1]
                if ext in image_exts:
                    self.media_is_an_image=True
                    contentUrl= bs_ext[0][0] + bs_ext[0][1]
                elif ext in {'gif','gifv'}:
                    self.media_is_an_image=False
                    contentUrl= bs_ext[0][0] + "webm"    #change gif extension to webm
                    
            except Exception as e:
                log(" EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )    
                  
        return contentUrl

class ClassInstagram:
    def __init__(self, media_url=""):
        return
    
    def prep_media_url(self, media_url, is_probably_a_video=True):
        #the instagram api has limits and that would not work for this purpose
        #  scrape the instagram post instead.

        r = requests.get(media_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            #grab the json-like object
            jo=re.compile('window._sharedData = ({.*});</script>').findall(r.text)
            if jo:
                try:
                    j=json.loads(jo[0].replace('\\"', '\''))
                    #log(str(j))
                    if j.get('entry_data'):
                        
                        #log(str(j['entry_data']['PostPage'][0]['media']['display_src']))
                        content_url=j['entry_data']['PostPage'][0]['media']['display_src']
                    else:
                        log("  Could not get 'entry_data' from scraping instagram [window._sharedData = ]")
                    
                except:
                    content_url=""
         
        
        
        return content_url

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
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    contentNew = ""

    keyboard = xbmc.Keyboard(subreddit, translation(30220))
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

def subreddit_alias( subreddit_entry_from_file ):
    #users can specify an alias for the subredit and it is stored in the file as a regular string  e.g. diy[do it yourself]  
    #this function returns the subreddit without the alias identifier and alias if any or alias=subreddit if none
    
    a=re.compile(r"(\[[^\]]*\])")
    alias=""
    subreddit = a.sub("",subreddit_entry_from_file).strip()
    #log( "  re:" +  subreddit )
    
    a= a.findall(subreddit_entry_from_file)
    if a:
        alias=a[0]
        #log( "      alias:" + alias )
    else:
        alias = subreddit
    
    return subreddit, alias

def index(url,name,type):
    ## this is where the __main screen is created
    content = ""
    if not os.path.exists(subredditsFile):
        #create a default file and sites
        fh = open(subredditsFile, 'a')
        fh.write('all\n')
        fh.write('music+listentothis+musicvideos\n')
        fh.write('site:youtu.be\n')
        fh.write('site:youtube.com\n')
        fh.write('site:vimeo.com/new\n')
        fh.write('aww+funny+Nickelodeons\n')
        fh.write('Documentaries+ArtisanVideos+lectures+LearnUselessTalents\n')
        fh.write('Stop_Motion+FrameByFrame+Brickfilms+Animation\n')
        fh.write('SlowMotion+timelapse+PerfectTiming\n')
        fh.write('videos\n')
        fh.write('videos/new\n')
        fh.write('/user/sallyyy19/m/video\n')  # user   http://forum.kodi.tv/member.php?action=profile&uid=134499
        fh.write('/user/gummywormsyum/m/videoswithsubstance\n')
        fh.close()
    #log(content)

    #log( sys.argv[0] ) #plugin://plugin.video.reddit_viewer/
    #log( addonID )     #plugin.video.reddit_viewer
    
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
    
    #log('cat_bypass='+str(cat_bypass))
    #go directly to the reddit content list instead of asking for what sort order they would be in
    if cat_bypass : 
        next_mode='listVideos'
        for subreddit in entries:
            #log(subreddit)
            
            #strip out the alias identifier from the subreddit string retrieved from the file so we can process it.
            subreddit_clean, alias = subreddit_alias(subreddit) 

            #url= urlMain+"/r/"+subreddit+"/.json?"+nsfw+allHosterQuery+"&limit="+itemsPerPage
            url= assemble_reddit_filter_string("",subreddit_clean, "yes")
            #log("assembled================="+url)
            if subreddit.lower() == "all":  
                #for listSorting, url is the subreddit
                #addDir(subreddit, subreddit.lower(), next_mode, "")
                #minor issue with the use of allHosterQuery here:
                #   we're asking reddit to return all supported sites by not sending allHosterQuery instead of assembling the a custom list of "site:"HosterQuery depending on the enabled sites setting. 
                #   we then filter the supported sites in get_hoster_and_PluginUrl_from_reddit to only add the supported sites on the list 
                addDir(subreddit_clean, url, next_mode, "", subreddit)
            else:                           
                #addDirR(subreddit, subreddit.lower(), next_mode, "")
                addDirR(subreddit, url, next_mode, "")
    
        #this portion removed. user can specify a domain shortcut    
#         if show_vimeo:
#             url = assemble_reddit_filter_string("","", "vimeo", "vimeo.com")  
#             addDir("[ Vimeo.com ]"      ,   url, next_mode, "", subreddit)
#         if show_youtube:   
#             url = assemble_reddit_filter_string("","", "yt","youtube.com")  
#             addDir("[ Youtube.com ]"    ,   url, next_mode, "", "")
#         if show_liveleak:    
#             url = assemble_reddit_filter_string("","", "ll","Liveleak.com")
#             addDir("[ Liveleak.com ]"   ,   url, next_mode, "", ""                )
#         if show_dailymotion: 
#             url = assemble_reddit_filter_string("","", "dm", "Dailymotion.com")
#             addDir("[ Dailymotion.com ]",   url, next_mode, "", ""             )
#         if show_gfycat:      
#             url = assemble_reddit_filter_string("","", "gc", "GfyCat.com")
#             addDir("[ GfyCat.com ]"     ,   url, next_mode, "", ""                  )
        
    else:  #this part is for if cat not bypass 
        next_mode='listSorting'
    
        for entry in entries:
            #log(entry)
            if entry.lower() == "all":
                addDir(entry, entry.lower(), next_mode, "")
            else:
                addDirR(entry, entry.lower(), next_mode, "")
    
        if show_vimeo:       addDir("[ Vimeo.com ]"      , "all", next_mode, "", "site:vimeo.com"                   )
        if show_youtube:     addDir("[ Youtube.com ]"    , "all", next_mode, "", "site:youtu.be OR site:youtube.com")
        if show_liveleak:    addDir("[ Liveleak.com ]"   , "all", next_mode, "", "site:liveleak.com"                )
        if show_dailymotion: addDir("[ Dailymotion.com ]", "all", next_mode, "", "site:dailymotion.com"             )
        if show_gfycat:      addDir("[ GfyCat.com ]"     , "all", next_mode, "", "site:gfycat.com"                  )

    addDir("[B]- "+translation(30001)+" or Multireddit[/B]", "", 'addSubreddit', "")
    addDir("[B]- "+translation(30019)+"[/B]", "", 'searchReddits', "")
    
    xbmcplugin.endOfDirectory(pluginhandle)


#MODE listVideos(url, name, type)    --name not used
def listVideos(url, name, subreddit):
    #url=r'https://www.reddit.com/r/videos/search.json?q=nsfw:yes+site%3Ayoutu.be+OR+site%3Ayoutube.com+OR+site%3Avimeo.com+OR+site%3Aliveleak.com+OR+site%3Adailymotion.com+OR+site%3Agfycat.com&sort=relevance&restrict_sr=on&limit=5&t=week'
    #url=r'https://www.reddit.com/r/videos/.json?site%3Ayoutu.be+OR+site%3Ayoutube.com+OR+site%3Avimeo.com+OR+site%3Aliveleak.com+OR+site%3Adailymotion.com+OR+site%3Agfycat.com&limit=50'
    #url=r'https://www.reddit.com/r/videos/search.json?q=nsfw:yes+site%3Adailymotion.com+OR+site%3Agfycat.com&sort=relevance&restrict_sr=on&limit=15&t=year'
    #url=r'https://www.reddit.com/r/aww/search.json?q=site%3Aimgur.com+OR+site%3Agfycat.com&sort=relevance&restrict_sr=on&limit=15&t=week'
    #url=r'http://www.reddit.com/r/all/.json?q=site%3Avimeo.com&limit=50'
    #url=r'http://www.reddit.com/r/all/search.json?q=site:vimeo.com&limit=50'
    #url='http://www.reddit.com/r/all/.json?limit=15'
    #url='https://www.reddit.com/r/all/search.json?q=site%3Avine&sort=relevance&restrict_sr=&t=week&limit=12'
    #url='https://www.reddit.com/search.json?q=site%3Areddituploads.com&sort=relevance&t=week'
    #url='https://www.reddit.com/search.json?q=site%3Astreamable.com&sort=relevance&restrict_sr=&t=week'
    #url='https://www.reddit.com/search.json?q=site%3Adailymotion&restrict_sr=&sort=relevance&t=week'
    #url='https://www.reddit.com/search.json?q=site%3A4tube&sort=relevance&t=all'
    #url='https://www.reddit.com/search.json?q=site%3Avid.me&sort=relevance&restrict_sr=&t=week'
    #url='https://www.reddit.com/search.json?q=site%3Ainstagram.com&sort=relevance&t=month'
    #url='https://www.reddit.com/search.json?q=site%3Ainstagram.com&sort=relevance&t=all'
    #url='https://www.reddit.com/search.json?q=site%3Ablogspot.com&sort=relevance&t=month'
    #url="https://www.reddit.com/r/bravo_vids/.json"
    #url="https://www.reddit.com/domain/tumblr.com.json"

    #show_listVideos_debug=False
    show_listVideos_debug=True
    credate = ""
    is_a_video=False
    title_line2=""
    log("listVideos url="+url)
    
    currentUrl = url
    xbmcplugin.setContent(pluginhandle, "movies") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos
    if showAllNewest:
        addDir("[B]- "+translation(30166)+"[/B]", url, 'autoPlay', "", "ALL_NEW")
    if showUnwatchedNewest:
        addDir("[B]- "+translation(30167)+"[/B]", url, 'autoPlay', "", "UNWATCHED_NEW")
    if showUnfinishedNewest:
        addDir("[B]- "+translation(30168)+"[/B]", url, 'autoPlay', "", "UNFINISHED_NEW")
    if showAll:
        addDir("[B]- "+translation(30012)+"[/B]", url, 'autoPlay', "", "ALL_RANDOM")
    if showUnwatched:
        addDir("[B]- "+translation(30014)+"[/B]", url, 'autoPlay', "", "UNWATCHED_RANDOM")
    if showUnfinished:
        addDir("[B]- "+translation(30015)+"[/B]", url, 'autoPlay', "", "UNFINISHED_RANDOM")
    content = opener.open(url).read()
    content = json.loads(content.replace('\\"', '\''))
    #log("query returned %d items " % len(content['data']['children']) )
    posts_count=len(content['data']['children'])
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

            #from urlparse import urlparse                
            #o=urlparse(media_url)    
            #log("P Media_url"+str(idx)+"="+o.path)
            #log("P Media_url"+str(idx)+"="+media_url.split('?')[0])

            try:
                thumb = entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8')
                #can't preview gif thumbnail on thumbnail view, use alternate provided by reddit
                if thumb.endswith('.gif'):
                    thumb = entry['data']['thumbnail'].encode('utf-8')
            except:
                thumb = entry['data']['thumbnail'].encode('utf-8')
                

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
            title_line2 = "[I][COLOR dimgrey]%s on [COLOR darkslategrey]r/%s[/COLOR] %d pts.[/COLOR][/I]" %(pretty_date,subreddit,ups)
            #title_line2 = "[I][COLOR dimgrey]"+pretty_date+" by "+author+" [COLOR darkslategrey]r/"+subreddit+"[/COLOR] "+str(ups)+" pts.[/COLOR][/I]"
                
            #title_line2 = "[I]"+str(idx)+". [COLOR dimgrey]"+ media_url[0:50]  +"[/COLOR][/I] "  # +"    "+" [COLOR darkslategrey]r/"+subreddit+"[/COLOR] "+str(ups)+" pts.[/COLOR][/I]"

            #if show_listVideos_debug : log( ("v" if is_a_video else " ") +"     TITLE"+str(idx)+"="+title)
            if show_listVideos_debug : log("POST%cTITLE%.2d=%s" %( ("v" if is_a_video else " "), idx, title ))
            #if show_listVideos_debug :log("    OVER_18"+str(idx)+"="+str(over_18))
            #if show_listVideos_debug :log(" IS_A_VIDEO"+str(idx)+"="+str(is_a_video))
            #if show_listVideos_debug :log("      THUMB"+str(idx)+"="+thumb)
            #if show_listVideos_debug :log("  MediaURL%.2d=%s" % (idx,media_url) )

            #if show_listVideos_debug :log("     HOSTER"+str(idx)+"="+hoster)
            #log("    VIDEOID"+str(idx)+"="+videoID)
            #log( "["+description+"]1["+ str(date)+"]2["+ str( count)+"]3["+ str( commentsUrl)+"]4["+ str( subreddit)+"]5["+ video_url +"]6["+ str( over_18))+"]"

            addLink(title=title, 
                    title_line2=title_line2,
                    iconimage=thumb, 
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
                    post_total=posts_count)
            
            
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
        addDir(translation(30016), nextUrl, 'listVideos', "", subreddit)
        #if show_listVideos_debug :log("NEXT PAGE="+nextUrl) 
    except:
        pass
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
        
        
    xbmcplugin.endOfDirectory(pluginhandle)



def addLink(title, title_line2, iconimage, description, credate, reddit_says_is_video, site, subreddit, media_url, over_18, posted_by="", num_comments=0,post_index=1,post_total=1 ):

    videoID=""
    post_title=title
    n=""  #will hold red nsfw asterisk string
    h=""  #will hold bold hoster:  string
    ok = False    
    #DirectoryItem_url=""
    hoster, DirectoryItem_url, videoID, mode_type, thumb_url, poster_url, isFolder,setInfo_type, IsPlayable=make_addon_url_from(media_url,reddit_says_is_video)
    name_param='' #extra parameter sent to this addon to put a 'title' on slideshows

    if iconimage in {"","nsfw", "default"}:
        #log( title+ ' iconimage blank['+iconimage+']['+thumb_url+ ']media_url:'+media_url ) 
        iconimage=thumb_url
    if poster_url=="":
        poster_url=iconimage
        
    #mode=mode_type #usually 'playVideo'
    if DirectoryItem_url:
        h="[B]" + hoster + "[/B]: "
        if over_18: 
            mpaa="R"
            n = "[COLOR red]*[/COLOR] "
            #description = "[B]" + hoster + "[/B]:[COLOR red][NSFW][/COLOR] "+title+"\n" + description
            description = "[COLOR red][NSFW][/COLOR] "+ h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"
        else:
            mpaa=""
            description = h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"

        if TitleAddtlInfo:     #put the additional info on the description if setting set to single line titles
            post_title=title+"[CR]"+title_line2
        else:
            post_title=title
            description=title_line2+"[CR]"+description
            
        il={"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin

        if setting_hide_images==True and mode_type in {'listImgurAlbum','playSlideshow','listLinksInComment' }:
            log('setting: hide non-video links') #and text links(reddit.com)
            return
        else:
            #name_param is additional text sent to modes that show a slideshow to 'title' the image
            if mode_type in {'listImgurAlbum','playSlideshow','listLinksInComment','playTumblr','playInstagram'  }:
                name_param="" #'&name=' + urllib.quote_plus(title)
        
        if mode_type in {'listImgurAlbum','listTumblrAlbum'}:post_title='[Album] '+post_title
        #if mode_type=='playSlideshow': post_title='[IMG] '+post_title   
        if setInfo_type=='pictures'  : post_title='[IMG] '+post_title   
        if mode_type=='listLinksInComment': post_title='[reddit] '+post_title  
        
        liz=xbmcgui.ListItem(label=n+post_title, 
                              label2="",
                              iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        
        #art_object
        liz.setArt({"thumb": iconimage, "poster":poster_url, "banner":iconimage, "fanart":iconimage, "landscape":iconimage   })

        #liz.setInfo(type=setInfo_type, infoLabels=il)
        liz.setInfo(type='video', infoLabels=il)
        
        liz.setProperty('IsPlayable', IsPlayable)
        
        entries = [] #entries for listbox for when you type 'c' or rt-click 

        #sys.argv[0] is plugin://plugin.video.reddit_viewer/
        #prl=zaza is just a dummy: during testing the first argument is ignored... possible bug?
        entries.append( ( translation(30219)+" r/%s" %subreddit , 
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listVideos&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit,True)  ) ) ) )            
        entries.append( ( translation(30203)+" (%d)" %num_comments, 
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(site) ) ) )            


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
          
        xbmcplugin.addDirectoryItem(pluginhandle, DirectoryItem_url+name_param, listitem=liz, isFolder=isFolder, totalItems=post_total)
        
    return ok

def make_addon_url_from(media_url, assume_is_video=True ):
    #returns tuple.  info ready for plugging into  addDirectoryItem
    #if url_for_DirectoryItem is blank, then assume media url is not supported.


    pluginUrl=None
    hoster=None
    videoID=""
    modecommand=""   #string used by this plugin to determine which functionality to call
    thumb_url=""     #reddit's thumbnail takes priority. this is for thumbs that can be easily gotten without requesting the hoster site.  
    poster_url=""    #a bigger thumbnail
    replace_url_for_DirectoryItem=None
    url_for_DirectoryItem = ""
    isFolder=False
    flag_media_not_supported=False
    
    
    setInfo_type='video'  #this used to be for the directoryItem but now we're abandoning the idea of using this addon as pictures addon.
                          #it is now used to determine if media is image and gets the [IMG] tag. we used to use 'playSlideShow' for this purpose but tumblr & instagram can have video, album or images that need to be processed later. 
                                        #liz.setInfo(type='pictures', infoLabels=il)  pictures or video 
                                        #if this addon is pictures addon, set to pictures so that image will show up
                                        #if this addon is video addon, set to video so that description will be shown (but image won't "play" in unix variants)
                                        #set this only to pictures for imgur images and only if    content_type='image'
    setProperty_IsPlayable='true'

#ask youtube-dl which sites it can process. (removed because this part takes too long!)
#     from youtube_dl.extractor import gen_extractors
#     for ie in gen_extractors():
# #        log("ie "+ str(ie.IE_NAME ) )
#         try:
#             site_pattern = ie._VALID_URL
#         except:
#             continue
# 
#         match = re.compile( site_pattern ).findall(media_url)
#         
#         if match :
#             log("matched: [%s] [%s]    [%s]" %( ie.IE_NAME, media_url, site_pattern ))
#             site_name =  ie.IE_NAME
#             try: media_type=  ie._ITEM_TYPE 
#             except: media_type=""
#             break



    log( "  Checking link %s" %media_url) 
    if media_url :

        #search our supported_sites[] to see if media_url can be handled by plugin
        for site in supported_sites :
            if site[0]:  #site[0]  is the show_youtube/show_vimeo/show_dailymotion/... global variables taken from settings file
                match = re.compile( site[3]  , re.DOTALL).findall(media_url)
                if match : break
    
        if match:
            #log("make_addon_url_from:match on hoster="+site[2])
            hoster = site[2]
            modecommand = site[1]  #
            #vimeo and liveleak sometimes have extra string after the video ID, we process
            if   hoster==site02[2] : videoID = match[0].replace("#", "").split("?")[0]  #'vimeo'
            elif hoster==site05[2] : videoID = match[0].split("#")[0]                   #'liveleak': 
            else                   : videoID = match[0]
    
            #figure out the thumbnail url. usually, reddit returns the thumbnail url but doesn't do so for nsfw
            #log("determine [%s] thumb from ID[%s] url[%s]" %(hoster,videoID,media_url))
            if hoster=="YouTube":   #**** this is case sensitive make sure it matches text defined in supported_sites[]
                thumb_url=ret_youtube_thumbnail(videoID,0)  #log("[%s] thumb_url from ID[%s] is[%s]" %(hoster,videoID,thumb_url))
                poster_url=thumb_url
                if use_ytdl_for_yt:
                    modecommand='playYTDLVideo'
                    #pluginUrl=media_url
                    
                    #a you tube link like the one below takes a very long time for youtube_dl to process 
                    #   https://www.youtube.com/watch?v=glXgSSOKlls&amp;list=RD0rtV5esQT6I&amp;index=9
                    #   since we already parsed the videoID, we will provide a faster url
                    pluginUrl="http://youtube.com/v/"+videoID  
                else:
                    pluginUrl= site[4].replace('##vidID##', videoID)
            elif hoster=="Giphy":
                #thumb_url="http://thumbs.gfycat.com/%s-poster.jpg"%videoID
                #poster_url=thumb_url
                
                #can change 'gif' to 'mp4' for https://media.giphy.com/media/l41YkuPROHQj0fjRS/giphy.gif 
                #but not http://i.giphy.com/xT8qBrECMlTTrn0iyI.gif  <--loads slow

                if 'media' in media_url:
                    media_url=media_url.replace('gif','mp4')
                replace_url_for_DirectoryItem=media_url
                modecommand='direct'  #no need to call plugin with a 'mode' just have xbmc handle the stream directly
                                 

            elif hoster=="Vimeo":
                #get thumbnail here then parse reply ['thumbnail_medium'] 
                #http://vimeo.com/api/v2/video/<video-id>.php
                thumb_url=""
                pluginUrl= site[4].replace('##vidID##', videoID)
            elif hoster=="DailyMotion":
                thumb_url=""
                pluginUrl= site[4].replace('##vidID##', videoID)
            elif hoster=="LiveLeak":
                thumb_url=""
                pluginUrl= site[4].replace('##vidID##', videoID)
            elif hoster=="Gfycat":
                thumb_url="http://thumbs.gfycat.com/%s-poster.jpg"%videoID
                poster_url=thumb_url
                pluginUrl= site[4].replace('##vidID##', videoID)

            elif hoster=="Imgur":
                c=ClassImgur()
                thumb_url=c.ret_thumb_url( media_url )
                #log('thumb_url '+thumb_url)
                prepped_media_url, is_video = c.prep_media_url(media_url, assume_is_video)
                #log('thumb_url'+thumb_url)
                thumb_url=c.ret_thumb_url( prepped_media_url )
                if prepped_media_url=='':     #not imgur
                    flag_media_not_supported=True
                    log('  not imgur') #very unlikely to happen. 
                elif prepped_media_url=='album':
                    pluginUrl=media_url
                    modecommand='listImgurAlbum'
                    isFolder=True
                else:
                    poster_url=c.ret_thumb_url( prepped_media_url,'l' )
                    if prepped_media_url.endswith(tuple(image_exts)):
                        pluginUrl=prepped_media_url
                        modecommand='playSlideshow'
                        #isFolder=True
                        setProperty_IsPlayable='false'
                        setInfo_type='pictures'
                    else:
                        replace_url_for_DirectoryItem=prepped_media_url
                        modecommand='direct'  #no need to call plugin with a 'mode' just have xbmc handle the stream directly

            elif hoster == 'Tumblr':
                pluginUrl=media_url
                t=ClassTumblr(media_url)
                ret_url, media_type =t.prep_media_url(media_url, assume_is_video)
                log( "   tumblr media type is [" + media_type +"]" )
                if media_type=='album':
                    modecommand='listTumblrAlbum'
                    poster_url=t.ret_thumb_url() #if poster+url =="" is taken care of by calling function
                    pluginUrl=media_url  #we don't use the ret_url here. ret_url is a dictlist of images
                    isFolder=True
                elif media_type=='photo':
                    modecommand='playSlideshow'
                    #provide thumbnail
                    poster_url=t.ret_thumb_url() #if poster+url =="" is taken care of by calling function

                    if thumb_url=="": 
                        filename,ext=parse_filename_and_ext_from_url(ret_url)
                        if ext in image_exts :             #=='gif':  #*** we can't handle gif. 
                            thumb_url=media_url                        
                        
                    pluginUrl=ret_url
                    setProperty_IsPlayable='false'
                    setInfo_type='pictures'
                elif media_type in {'audio','answer','text'}:
                    log("  tumblr media (%s) not supported" %(media_type) )
                    flag_media_not_supported=True   
                elif media_type=='video':
                    thumb_url=t.ret_thumb_url()
                    poster_url=thumb_url
                    replace_url_for_DirectoryItem=ret_url
                    modecommand='direct'  #no need to call plugin with a 'mode' just have xbmc handle the stream directly
                else:
                    log("  unknown tumblr media" )
                    flag_media_not_supported=True
                
            elif hoster in {"Redd.it", "RedditUploads", "RedditMedia"}:
                media_url=media_url.replace('&amp;','&')
                pluginUrl=media_url  #this replace is only for  RedditUploads but seems harmless for the others...
                modecommand='playSlideshow'
                #replace_url_for_DirectoryItem=media_url      #this is for direct link on the directory item  xbmc prefers this mode but this only works on image addon since this media most likely is an image
                #try to provide thumbnail:
                filename,ext=parse_filename_and_ext_from_url(media_url)
                #log( "  parsed filename" + filename + " ext---" + ext)
                if ext=='gif':  #
                    replace_url_for_DirectoryItem=pluginUrl
                    #pluginUrl=media_url
                    modecommand='direct'
                    setProperty_IsPlayable='true'
                    #thumb_url=media_url  can't use gifs as thumb
                else:
                    thumb_url=media_url
                    setInfo_type='pictures'
                    setProperty_IsPlayable='false'
                     
            elif hoster=="Reddit.com":
                pluginUrl=media_url 
                modecommand='listLinksInComment'    #
                #setProperty_IsPlayable='false'
                isFolder=True                                 #<-- this is important. tells kodi that this will open another listing. fixes WARNING: Attempt to use invalid handle -1

            elif hoster in {"Vine","Vidme"}:
                #v=ClassVine(media_url)
                #replace_url_for_DirectoryItem='https://v.cdn.vine.co/r/videos/38B4A9174D1177703702723739648_37968e655a0.1.5.1461921223578533188.mp4'
                #replace_url_for_DirectoryItem=v.prep_media_url(media_url, True)    #this is for direct link on the directory item  xbmc prefers this mode but we don't use it.
                #   because it involves querying vine(for the .mp4 link) for each item. 
                #   this adds a short delay on the directory listing(that will add up).
                #log('m:'+ media_url)
                #log('p:'+pluginUrl)
                pluginUrl=media_url
                thumb_url=""
            elif hoster=="Streamable":
                pluginUrl=media_url
                s=ClassStreamable(media_url)
                #replace_url_for_DirectoryItem=s.prep_media_url(media_url,True )  6/18/2016  direct linking doesn't work anymore
                #replace_url_for_DirectoryItem="https://cdn.streamable.com/video/mp4/dw9f.mp4"
                thumb_url=s.ret_thumb_url()
            elif hoster=="Blogspot":
                b=ClassBlogspot(media_url)
                pluginUrl=b.prep_media_url(media_url,assume_is_video )
                if b.media_is_an_image:
                    modecommand='playSlideshow'
                    setProperty_IsPlayable='false'
                    thumb_url=pluginUrl
                    setInfo_type='pictures'   #to get the [IMG] tag
                else:
                    replace_url_for_DirectoryItem=pluginUrl
    
            elif hoster in {'Instagram','porn','misc'}:   #everything here is handled by the Youtube_dl plugin by ruuk
                #log('YTDL:'+hoster)
                pluginUrl=media_url 
                modecommand='playYTDLVideo'
                if hoster == 'Instagram':  #instagram is a little special coz it has a siteXX definition
                    thumb_url=ret_Instagram_thumbnail(media_url)
                    #poster_url=thumb_url  #ret_Instagram_thumbnail(media_url,'l')  #doesn't display
                    #log("  thumb: "+poster_url)
                    if assume_is_video==False:  #we determined that this is not a video accdg. to reddit json
                        modecommand='playInstagram'
                        #pluginUrl=ret_Instagram_thumbnail(media_url,'l')
                        setInfo_type='pictures'
                        setProperty_IsPlayable='false' 
                elif hoster in {'porn','misc'}: #hoster will show in description. we replace it with the match to inform user where video is hosted
                    #log('pr0n')
                    for n in match[0]:
                        if n:
                            hoster=str( n )
                                
                
    #             ytdl_blacklist=["Youtube","24video", "XXXYMovies", "4tube"]
    #             YDStreamExtractor.generateBlacklist(ytdl_blacklist)
    #              
    #             if YDStreamExtractor.mightHaveVideo(media_url,resolve_redirects=True):
    #                 log('might have video=true ' + media_url)
    #                 vid = YDStreamExtractor.getVideoInfo(media_url)  #quality is 0=SD, 1=720p, 2=1080p and is a maximum
    #                  
    #                 if vid:
    #                     log("vid is true")
    #                 else:
    #                     log("can't get getVideoInfo")
    #             else:
    #                 log('might have video=false ' + media_url)
            #log ("  replace direct: "+replace_url_for_DirectoryItem)
            if replace_url_for_DirectoryItem:
                url_for_DirectoryItem = replace_url_for_DirectoryItem
                #log ("  direct link: "+url_for_DirectoryItem)
            else:
                url_for_DirectoryItem = sys.argv[0]+"?url="+ urllib.quote_plus(pluginUrl) +"&mode="+str(modecommand)  #sys.argv[0] is "plugin://plugin.video.reddit_viewer/"
    
        else:  # if match:
            flag_media_not_supported=True
            
        
    
    if flag_media_not_supported:  #caller checks for the returned DirectoryItem_url. if it is blank, it is unsupported.
        log("  unsupported link[%s]" %media_url)
        url_for_DirectoryItem = "" 
     
    #log( hoster + "==" + videoID  )
    return hoster, url_for_DirectoryItem, videoID, modecommand, thumb_url, poster_url, isFolder, setInfo_type,setProperty_IsPlayable


def url_is_supported(url_to_check):
    #search our supported_sites[] to see if media_url can be handled by plugin
    #returns the regex match
    for site in supported_sites :
        if site[0]:  #site[0]  is the show_youtube/show_vimeo/show_dailymotion/... global variables taken from settings file
            match = re.compile( site[3]  , re.DOTALL).findall(url_to_check)
            if match : 
                return True

    return False

#MODE listFavourites -  name, type not used
def listFavourites(subreddit, name, type):
    xbmcplugin.setContent(pluginhandle, "episodes")
    file = os.path.join(addonUserDataFolder, subreddit+".fav")
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if os.path.exists(file):
        fh = open(file, 'r')
        content = fh.read()
        fh.close()
        match = re.compile('<favourite name="(.+?)" url="(.+?)" description="(.+?)" thumb="(.+?)" date="(.+?)" site="(.+?)" />', re.DOTALL).findall(content)
        for name, url, desc, thumb, date, site in match:
            addFavLink(name, url, "playVideo", thumb, desc.replace("<br>","\n"), date, site, subreddit)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
    xbmcplugin.endOfDirectory(pluginhandle)

#MODE autoPlay        - name not used
def autoPlay(url, name, type):
    #collect a list of title and urls as entries[] from the j_entries obtained from reddit
    #then create a playlist from those entries
    #then play the playlist

    entries = []
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    #log("**********autoPlay*************")
    content = opener.open(url).read()
    content = json.loads(content.replace('\\"', '\''))
    #ava=  int(len(content['data']['children'])) 
    #log("autoplay "+str(ava) +" items")
    
    for j_entry in content['data']['children']:
        try:
            #title = cleanTitle(entry['data']['media']['oembed']['title'].encode('utf-8'))
            title = cleanTitle(j_entry['data']['title'].encode('utf-8'))

            #log("**********title:"+title)                
            try:
                media_url = j_entry['data']['media']['oembed']['url']
            except:
                media_url = j_entry['data']['url']

            is_a_video = determine_if_video_media_from_reddit_json(j_entry) 

            hoster, DirectoryItem_url, videoID, mode_type, thumb_url,isFolder,setInfo_type, IsPlayable=make_addon_url_from(media_url,is_a_video)
        
            if DirectoryItem_url:
                if isFolder:  #imgur albums are 'isFolder'
                    continue
                if setInfo_type=='pictures': #we also skip images in autoplay
                    continue
                
                if setting_hide_images==True and mode_type in {'listImgurAlbum','playSlideshow','listLinksInComment' }:
                    #log('img links not shown')
                    continue                
                
                if type.startswith("ALL_"):
                    entries.append([title, DirectoryItem_url])
                elif type.startswith("UNWATCHED_") and getPlayCount(url) < 0:
                    entries.append([title, DirectoryItem_url])
                elif type.startswith("UNFINISHED_") and getPlayCount(url) == 0:
                    entries.append([title, DirectoryItem_url])
        except:
            pass
    
    if type.endswith("_RANDOM"):
        random.shuffle(entries)

    for title, url in entries:
        listitem = xbmcgui.ListItem(title)
        playlist.add(url, listitem)
        #log("added to playlist:"+ title + "  " + urllib.unquote_plus(url) )
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
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    else:
        log("playVideo(url) url is blank")
        
def playYTDLVideo(url, name, type):
    #url = "http://www.youtube.com/watch?v=_yVv9dx88x0"   #a youtube ID will work as well and of course you could pass the url of another site
    
    #url='https://www.youtube.com/shared?ci=W8n3GMW5RCY'
    #url='https://www.youtube.com/watch?v=nsTuFn2IcHQ'
    #url='http://www.3sat.de/mediathek/?mode=play&obj=51264'
    #url='http://www.4tube.com/videos/209271/hurry-fuck-i-bored'
    #url='http://sex3.com/23951/'
    choices = []


#does not work:  yourlust 4tube porntube xpornvid.com porndig.com  thumbzilla.com eporner.com beeg.com yuvutu.com porn.com pornerbros.com fux.com flyflv.com xstigma.com sexu.com 5min.com alphaporno.com
# stickyxtube.com xxxbunker.com bdsmstreak.com  jizzxman.com pornwebms.com pornurl.pw porness.tv openload.online pornworms.com fapgod.com porness.tv hvdporn.com pornmax.xyz xfig.net yobt.com
# eroshare.com kalporn.com hdvideos.porn dailygirlscute.com desianalporn.com indianxxxhd.com onlypron.com sherloxxx.com hdvideos.porn x1xporn.com pornhvd.com lxxlx.com xrhub.com shooshtime.com
# pornvil.com lxxlx.com redclip.xyz younow.com aniboom.com  gotporn.com  virtualtaboo.com 18porn.xyz vidshort.net fapxl.com vidmega.net

# also does not work (non porn)
# rutube.ru  mail.ru  afreeca.com nicovideo.jp  videos.sapo.pt(many but not all) sciencestage.com vidoosh.tv metacafe.com vzaar.com videojug.com trilulilu.ro tudou.com video.yahoo.com blinkx.com blip.tv
# blogtv.com  brainpop.com crackle.com engagemedia.org expotv.com flickr.com fotki.com godtube.com hulu.com lafango.com  mefeedia.com motionpictur.com izlesene.com sevenload.com patas.in myvideo.de
# vbox7.com

# 
# ytdl also supports these sites: 
# - funnyordie.com
# - videos.sapo.pt
# - schooltube.com
# 
# - viddler.com
# - veoh.com
# - break.com
# - videosift.com
# - engagemedia.org
# myvideo.co.za  ?
# - funnyclips.me 
#bluegartr.com  (gif)



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
            log('YDStreamExtractor.mightHaveVideo[true]' + url)
            vid = YDStreamExtractor.getVideoInfo(url,0,True)  #quality is 0=SD, 1=720p, 2=1080p and is a maximum
            if vid:
                log("getVideoInfo success")
                if vid.hasMultipleStreams():
                    log("vid hasMultipleStreams")
                    for s in vid.streams():
                        title = s['title']
                        log('choices' + title  )
                        choices.append(title)
                    #index = some_function_asking_the_user_to_choose(choices)
                    vid.selectStream(0) #You can also pass in the the dict for the chosen stream
        
                stream_url = vid.streamURL()                         #This is what Kodi (XBMC) will play        
                log("stream_url="+stream_url)
                listitem = xbmcgui.ListItem(path=stream_url)
                xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
            else:
                #log("getVideoInfo failed==" )
                xbmc.executebuiltin('XBMC.Notification("error","getVideoInfo Failed")' )  
    except Exception as e:
        #log( "zz   " + str(e) )
        xbmc.executebuiltin('XBMC.Notification("error","%s")' %str(e)  )
        

#MODE playGfycatVideo       - name, type not used
def playGfycatVideo(id, name, type):
    content = opener.open("http://gfycat.com/cajax/get/"+id).read()
    content = json.loads(content.replace('\\"', '\''))
    
    if "gfyItem" in content and "mp4Url" in content["gfyItem"]:
        GfycatStreamUrl=content["gfyItem"]["mp4Url"]
    
    playVideo(GfycatStreamUrl, name, type)

def ret_youtube_thumbnail(videoID, quality0123=1):
    """
    Each YouTube video has 4 generated images. They are predictably formatted as follows:

    http://img.youtube.com/vi/<insert-youtube-video-id-here>/0.jpg
    http://img.youtube.com/vi/<insert-youtube-video-id-here>/1.jpg
    http://img.youtube.com/vi/<insert-youtube-video-id-here>/2.jpg
    http://img.youtube.com/vi/<insert-youtube-video-id-here>/3.jpg
    
    The first one in the list is a full size image and others are thumbnail images. The default thumbnail image (ie. one of 1.jpg, 2.jpg, 3.jpg) is:
    http://img.youtube.com/vi/<insert-youtube-video-id-here>/default.jpg
    
    For the high quality version of the thumbnail use a url similar to this:    http://img.youtube.com/vi/<insert-youtube-video-id-here>/hqdefault.jpg
    There is also a medium quality version of the thumbnail, similar to the HQ: http://img.youtube.com/vi/<insert-youtube-video-id-here>/mqdefault.jpg
    For the standard definition version of the thumbnail, use similar to this:  http://img.youtube.com/vi/<insert-youtube-video-id-here>/sddefault.jpg
    For the maximum resolution version of the thumbnail use similar to this:    http://img.youtube.com/vi/<insert-youtube-video-id-here>/maxresdefault.jpg
    All of the above urls are available over https too. Just change http to https in any of the above urls. Additionally, the slightly shorter hostname i3.ytimg.com works in place of img.youtube.com in the example urls above.

    #http://stackoverflow.com/questions/2068344/how-do-i-get-a-youtube-video-thumbnail-from-the-youtube-api
    """

    #getting the videoID from url   
    #match = re.compile('youtube\.com/watch\?v=([^?&#]+)|youtu\.be/([^?&#]+)', re.DOTALL).findall(url)
    #if match:
    #    log('match were looking for!')
    
    return ('http://img.youtube.com/vi/%s/%d.jpg' %(videoID,quality0123))

def ret_Instagram_thumbnail( media_url, thumbnail_type='m'):
    #return the instagram thumbnail url 

    #possible thumbnail_types(6/1/2016)
    #    t = 150 x 150 px
    #    m = 306 x 306 px
    #    l = 640 x 640 px

    #just add "/media/?size=m" OR "/media/"  default size is m
    #https://www.instagram.com/p/BF3x5kajBja/media/?size=m
    from urlparse import urlparse
    o=urlparse(media_url)    #from urlparse import urlparse
    #scheme, netloc, path, params, query, fragment
    
    #log("thumb from: "+media_url )
    #path starts with / use [1:] to skip 1st character
    #log ("thumb     : %s://%s/%s%s%c" % ( o.scheme, o.netloc, o.path[1:], 'media/?size=', thumbnail_type ) )
    #return ("%s://%s/%s%s%c" % ( o.scheme, o.netloc, o.path[1:], 'media/?size=', thumbnail_type ) )
    return ("http://%s/%s%s%c" % ( o.netloc, o.path[1:], 'media/?size=', thumbnail_type ) )


def listLinksInComment(url, name, type):
    #MODE list supported links in reddit comment 
    #log('listLinksInComment:'+url)

    xbmcplugin.setContent(pluginhandle, "movies")    #files, songs, artists, albums, movies, tvshows, episodes, musicvideos 

    #sometimes the url has a query string. we discard it coz we add .json at the end
    #url=url.split('?', 1)[0]+'.json'

    #url='https://www.reddit.com/r/Music/comments/4k02t1/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/' + '.json'
    #only get up to "https://www.reddit.com/r/Music/comments/4k02t1". 
    #   do not include                                            "/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/"
    #   because we'll have problem when it looks like this: "https://www.reddit.com/r/Overwatch/comments/4nx91h/ever_get_that_feeling_dÃ©jÃ _vu/"
    
    url=re.findall(r'(.*/comments/[A-Za-z0-9]+)',url)[0] 
    url+='.json'
    log("listLinksInComment:"+url)
    content = opener.open(url).read()
    #log(content)
    #content = json.loads(content.replace('\\"', '\''))  #some error here ?      TypeError: 'NoneType' object is not callable
    content = json.loads(content)
    
    del harvest[:]
    #harvest links in the post text (just 1) 
    r_linkHunter(content[0]['data']['children'])
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
        kind=h[6] #reddit used t1 for comments and t3 for post text
        d=h[5]   #depth of the comment
        tab=" "*d
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
            
            #log(h[3])
            
            fl= re.compile('\[(.*?)\]\(.*?\)',re.IGNORECASE) #match '[...](...)' with a capture group inside the []'s as capturegroup1
            result = fl.sub(r"[B]\1[/B]", h[3])              #replace the match with [B] [/B] with capturegroup1 in the middle of the [B]'s
            #log(result)

            liz=xbmcgui.ListItem(label=     "[COLOR greenyellow]"+     list_title+"[%s] %s"%(hoster, result.replace('\n',' ')[0:100])  + "[/COLOR]", 
                                 label2="",
                                 iconImage="DefaultVideo.png", 
                                 thumbnailImage=thumb_url)

            
            liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": result, "studio": hoster } )
            liz.setArt({"thumb": thumb_url, "poster":thumb_url, "banner":thumb_url, "fanart":thumb_url, "landscape":thumb_url   })

            liz.setProperty('IsPlayable', setProperty_IsPlayable)

            xbmcplugin.addDirectoryItem(handle=pluginhandle
                                        ,url=DirectoryItem_url
                                        ,listitem=liz
                                        ,isFolder=isFolder)
        else:
            #this section are for comments that have no links or unsupported links
            if not ShowOnlyCommentsWithlink:
                
                liz=xbmcgui.ListItem(label=list_title + desc100 , 
                                     label2="",
                                     iconImage="", 
                                     thumbnailImage="")
                liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": h[3], "studio": hoster } )
                liz.setProperty('IsPlayable', 'false')
                xbmcplugin.addDirectoryItem(handle=pluginhandle
                                            ,url=""
                                            ,listitem=liz
                                            ,isFolder=False)
            
            #END section are for comments that have no links or unsupported links
            
            
    #xbmc.executebuiltin('Container.SetViewMode(%d)' %(515) )
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
    
    xbmcplugin.endOfDirectory(pluginhandle)


harvest=[]
def r_linkHunter(json_node,d=0):
    #recursive function to harvest stuff from the reddit comments json reply
    prog = re.compile('<a href=[\'"]?([^\'" >]+)[\'"]>(.*?)</a>')   

    for e in json_node:
        link_desc=""
        link_http=""
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
                harvested=False  
                for link_http,link_desc in result:
                    if url_is_supported(link_http) or not harvested:   #store at least one instance of the post but not for every link
                        #store an entry for every supported link. if a post has a lot of links, it will repeat and look ugly
                        if not harvested:
                            harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",)   )
                        else:
                            harvest.append((score, link_desc, link_http, link_desc, post_html, d, "t1",)   )    
                        harvested=True
            else:
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",)   )    
    
            d+=1 #d tells us how deep is the comment in
            r_linkHunter(replies,d)            

        if e['kind']=='t3':     #'t3' for post text(?)
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
                harvested=False  
                for link_http,link_desc in result:
                    if url_is_supported(link_http) or not harvested:   #store at least one instance of the post but not for every link
                        #store an entry for every supported link. if a post has a lot of links, it will repeat and look ugly
                        if not harvested:
                            harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3", )   )
                        else:
                            harvest.append((score, link_desc, link_http, link_desc, self_text_html, d, "t3", )   )
                        harvested=True
            else:
                if len(self_text) > 0: #don't post an empty titles
                    harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",)   )    
            

#MODE listImgurAlbum
def listImgurAlbum(album_url, name, type):
    #log("listImgurAlbum")
    
    #album_url="http://imgur.com/a/fsjam"
    ci=ClassImgur()
        
    dictlist=ci.ret_album_list(album_url)
    display_album_from(dictlist, name)

def display_album_from(dictlist, album_name):
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

    xbmcplugin.setContent(pluginhandle, "episodes")
    
    for d in dictlist:
        #log('li_label:'+d['li_label'] + "  pluginhandle:"+ str(pluginhandle))
        ti=d['li_thumbnailImage']
        liz=xbmcgui.ListItem(label=d['li_label2'], 
                             label2=d['li_label2'],
                             iconImage=d['li_iconImage'],
                             thumbnailImage=ti)
        
        content_type='video'  #<-- this addon used to be run as video or pictures. now that we've found a workaround to showing images as a video addon, it is now set permanently to 'video' 
        

        #classImgur puts the media_url into  d['DirectoryItem_url']  no modification.
        #we modify it here...
        #url_for_DirectoryItem = sys.argv[0]+"?url="+ urllib.quote_plus(d['DirectoryItem_url']) +"&mode=playSlideshow"
        hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, IsPlayable=make_addon_url_from(d['DirectoryItem_url'],False)
        if poster_url=="": poster_url=ti
        if content_type=='video':
            liz.setInfo( type='video', infoLabels= d['infoLabels'] ) #this tricks the skin to show the plot. where we stored the picture descriptions
            liz.setArt({"thumb": ti, "poster":poster_url, "banner":ti, "fanart":poster_url, "landscape":poster_url   })             
        else:
            liz.setInfo( type=d['type'], infoLabels= d['infoLabels'] )


        xbmcplugin.addDirectoryItem(handle=pluginhandle
                                    ,url=DirectoryItem_url
                                    ,listitem=liz)

    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

    xbmcplugin.endOfDirectory(pluginhandle)

def parse_filename_and_ext_from_url(url=""):
    filename=""
    ext=""
    try:
        filename, ext = (url.split('/')[-1].split('.'))
        #log( "  ext=[%s]" %ext )
        if not ext=="":
            
            #ext=ext.split('?')[0]
            ext=re.split("\?|#",ext)[0]
            
        return filename, ext
    except:
        return "", ""
 
def listTumblrAlbum(t_url, name, type):    
    log("listTumblrAlbum:"+t_url)
    t=ClassTumblr(t_url)
    
    media_url, media_type =t.prep_media_url(t_url, True)
    #log('  ' + str(media_url))
    
    if media_type=='album':
        display_album_from( media_url, name )
    else:
        log("  listTumblrAlbum can't process " + media_type)    


def playVineVideo(vine_url, name, type):
    #log('playVineVideo')
    
    v=ClassVine(vine_url)
    #vine_stream_url='https://v.cdn.vine.co/r/videos/38B4A9174D1177703702723739648_37968e655a0.1.5.1461921223578533188.mp4'
    vine_stream_url=v.prep_media_url(vine_url, True)    #instead of querying vine(for the .mp4 link) for each item when listing the directory item(addLink()). we do that query here. better have the delay here than for each item when listing the directory item 
    
    if vine_stream_url:
        playVideo(vine_stream_url, name, type)
    else:
        #media_status=v.whats_wrong()
        xbmc.executebuiltin('XBMC.Notification("Vine","%s")' % 'media_status'  )

    
    #xbmc.executebuiltin("PlayerControl('repeatOne')")  #how do i make this video play again? 

def playVidmeVideo(vidme_url, name, type):
    log('playVidmeVideo')
    v=ClassVidme(vidme_url)
    vidme_stream_url=v.prep_media_url(vidme_url, True)
    if vidme_stream_url:
        playVideo(vidme_stream_url, name, type)
    else:
        media_status=v.whats_wrong()
        xbmc.executebuiltin('XBMC.Notification("Vidme","%s")' % media_status  )
        

def playStreamable(media_url, name, type):
    log('playStreamable '+ media_url)
    
    s=ClassStreamable(media_url)
    playable_url=s.prep_media_url(media_url, True)

    if playable_url:
        playVideo(playable_url, name, type)
    else:
        #media_status=s.whats_wrong()  #streamable does not tell us if access to video is denied beforehand
        xbmc.executebuiltin('XBMC.Notification("Streamable","%s")' % "Access Denied"  )
    

def playInstagram(media_url, name, type):
    log('playInstagram '+ media_url)
    #instagram video handled by ytdl. links that reddit says is image are handled here.
    i=ClassInstagram( media_url )
    image_url=i.prep_media_url(media_url, False)
    
    playSlideshow(image_url,"Instagram","")

#MODE playLiveLeakVideo       - name, type not used
def playLiveLeakVideo(id, name, type):
    playVideo(getLiveLeakStreamUrl(id), name, type)

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
    keyboard = xbmc.Keyboard('', translation(30017))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():  
        
        search_string = urllib.quote_plus(keyboard.getText().replace(" ", "+"))
        
        sites_filter = site_filter_for_reddit_search()
        url = urlMain +"/search.json?q=" +search_string + '+' + nsfw  + sites_filter

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

def addFavLink(name, url, mode, iconimage, description, date, site, subreddit):
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description, "Aired": date})
    liz.setProperty('IsPlayable', 'true')
    entries = []
    entries.append((translation(30018), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(url)+'&name='+urllib.quote_plus(name)+')',))
    favEntry = '<favourite name="'+name+'" url="'+url+'" description="'+description+'" thumb="'+iconimage+'" date="'+date+'" site="'+site+'" />'
    entries.append((translation(30024), 'RunPlugin(plugin://'+addonID+'/?mode=removeFromFavs&url='+urllib.quote_plus(favEntry)+'&type='+urllib.quote_plus(subreddit)+')',))
    if showBrowser and (osWin or osOsx or osLinux):
        if osWin and browser_win==0:
            entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.webbrowser/?url='+urllib.quote_plus(site)+'&mode=showSite&zoom='+browser_wb_zoom+'&stopPlayback=no&showPopups=no&showScrollbar=no)',))
        else:
            entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.chrome.launcher/?url='+urllib.quote_plus(site)+'&mode=showSite)',))
    liz.addContextMenuItems(entries)
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=liz)
    return ok

#addDir(subreddit, subreddit.lower(), next_mode, "")
def addDir(name, url, mode, iconimage, type="", listitem_infolabel=None):
    #adds a list entry
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type)
    #log('addDir='+u)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    
    if listitem_infolabel==None:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    else:
        liz.setInfo(type="Video", infoLabels=listitem_infolabel)
        
    
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def addDirA(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    #log('addDirA='+u)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.addContextMenuItems([(translation(30001), 'RunPlugin(plugin://'+addonID+'/?mode=addSubreddit&url='+urllib.quote_plus(url)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def addDirR(name, url, mode, iconimage):
    #addDir with a remove subreddit context menu
    #alias is the text for the listitem that is presented to the user
    
    subreddit, alias = subreddit_alias(name)

    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    #log('addDirR='+u)
    ok = True
    liz = xbmcgui.ListItem(alias, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": alias})
    
    #liz.addContextMenuItems([(translation(30013), 'RunPlugin(plugin://'+addonID+'/?mode=removeSubreddit&url='+urllib.quote_plus(url)+')',)])
    liz.addContextMenuItems([(translation(30220), 'RunPlugin(plugin://'+addonID+'/?mode=editSubreddit&url='+urllib.quote_plus(name)+')',)     ,
                             (translation(30013), 'RunPlugin(plugin://'+addonID+'/?mode=removeSubreddit&url='+urllib.quote_plus(name)+')',)  
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
                return "just now"
            if sec_diff < 60:
                return str(sec_diff) + " secs ago"
            if sec_diff < 120:
                return "a min ago"
            if sec_diff < 3600:
                return str(sec_diff / 60) + " mins ago"
            if sec_diff < 7200:
                return "an hour ago"
            if sec_diff < 86400:
                return str(sec_diff / 3600) + " hrs ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff / 7) + " wks ago"
        if day_diff < 365:
            return str(day_diff / 30) + " months ago"
        return str(day_diff / 365) + " years ago"
    except:
        pass

class ssGUI(xbmcgui.WindowXMLDialog):
    #credit to The big Picture addon.
    CONTROL_MAIN_IMAGE = 100
    CONTROL_VISIBLE = 102
    CONTROL_ASPECT_KEEP = 103
    CONTROL_ARROWS = 104
    CONTROL_BG = 105
    ACTION_CONTEXT_MENU = [117]
    ACTION_PREVIOUS_MENU = [9, 92, 10]
    ACTION_SHOW_INFO = [11]
    ACTION_EXIT_SCRIPT = [13]
    ACTION_DOWN = [4]
    ACTION_UP = [3]
    ACTION_0 = [58, 18]
    ACTION_PLAY = [79]
    items=[]
    album_name=''
    
    def __init__(self, *args, **kwargs):
        #log("starting ssgui")
        #xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        pass

    def onInit(self):
        self.show_info = True
        self.aspect_keep = True

        self.getControls()
        self.addItems(self.items)

        self.setFocus(self.image_list)
        log('onInit finished')

    def onAction(self, action):
        action_id = action   #action.getId()
        if action_id in self.ACTION_SHOW_INFO:
            log('ACTION_SHOW_INFO: category:' + self.getWindowProperty('Category') )
            self.toggleInfo()  #show/hide description
        elif action_id in self.ACTION_CONTEXT_MENU:
            log('ACTION_CONTEXT_MENU category:' + self.getWindowProperty('Category') )
            self.close()
            #self.download_album()
        elif action_id in self.ACTION_PREVIOUS_MENU:
            log('ACTION_PREVIOUS_MENU: category:' + self.getWindowProperty('Category') )
            self.close()

    def onClick(self, controlId):
        if controlId == self.CONTROL_MAIN_IMAGE:
            self.toggleInfo()

    def getControls(self):
        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        self.image_list = self.getControl(self.CONTROL_MAIN_IMAGE)
        self.arrows_controller = self.getControl(self.CONTROL_ARROWS)
        self.aspect_controller = self.getControl(self.CONTROL_ASPECT_KEEP)
        self.info_controller = self.getControl(self.CONTROL_VISIBLE)
        try:
            self.bg_controller = self.getControl(self.CONTROL_BG)
        except RuntimeError:
            # catch exception with skins which override the xml
            # but are not up2date like Aeon Nox
            self.bg_controller = None

    def addItems(self, items):
        #self.log('addItems:' + str(items ))
        self.image_list.reset()
        for item in items:
            #log('aaaaaa : '+str(item))
            li = xbmcgui.ListItem(
                label=item['title'],
                label2=item['description'],
                iconImage=item['pic']
            )
            li.setProperty(
                'album_title',
                self.album_name   #top left-hand side
            )
            #li.setProperty('album_url', "item.get('album_url')")
            li.setProperty('album_id', "0")
            self.image_list.addItem(li)

    def toggleInfo(self):
        self.show_info = not self.show_info
        self.info_controller.setVisible(self.show_info)

    def toggleAspect(self):
        self.aspect_keep = not self.aspect_keep
        self.aspect_controller.setVisible(self.aspect_keep)

    def getWindowProperty(self, key):
        return self.window.getProperty(key)

    def setWindowProperty(self, key, value):
        return self.window.setProperty(key, value)


class qGUI(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        
    image_path=""
    s=0

    def onInit(self):
        self.getControl(3000).setImage(self.image_path)
        self.getControl(3100).setImage(self.image_path)
        self.getControl(3200).setImage(self.image_path)
        self.getControl(3300).setImage(self.image_path)

        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(False)

    def onAction(self, action):
        #ACTION_PREVIOUS_MENU=10    #ACTION_STOP=13    #AACTION_MOUSE_RIGHT_CLICK = 101   #ACTION_BACKSPACE = 110   ACTION_NAV_BACK = 92
        #ACTION_PAUSE = 12     #ACTION_PREV_ITEM = 15    # ACTION_STOP = 13   #KEY_BUTTON_B = 257   #KEY_BUTTON_BACK = 275 ACTION_PARENT_DIR = 9
        #
        #ACTION_PLAY = 68  KEY_BUTTON_A = 256 ACTION_ENTER = 135 ACTION_MOUSE_LEFT_CLICK = 100 ACTION_CONTEXT_MENU = 117
        if action in [68,256, 135,100]:
            self.cycle_zoom()
            #log("aaaaa go")
        
        if action == 31:  #ACTION_ZOOM_IN = 31
            log("zoom in")
        
        if action == 30:  #ACTION_ZOOM_OUT = 30
            log("zoom out")

        if action in [9, 10,13,92, 101,110,12,15,13,257,275,117]:
            self.close()        
        pass

    def onFocus(self, controlId):
        pass
    
    def cycle_zoom(self):
        if self.s==1:
            self.zoom_top()
        elif self.s==2:
            self.zoom_mid()
        elif self.s==3:
            self.zoom_btm()
        else:
            self.zoom_out()

    def zoom_out(self):
        self.s=1
        self.getControl(3000).setVisible(True)
        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(False)
    def zoom_top(self):
        self.s=2
        self.getControl(3000).setVisible(False)
        self.getControl(3100).setVisible(True)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(False)
    def zoom_mid(self):
        self.s=3
        self.getControl(3000).setVisible(False)
        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(True)
        self.getControl(3300).setVisible(False)
    def zoom_btm(self):
        self.s=4
        self.getControl(3000).setVisible(False)
        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(True)
        

    def onClick(self, controlId):
        #if controlId == 3001:
        self.cycle_zoom()
            
    def closeDialog(self):
        self.close()



def playSlideshow(url, name, type):

    #url='d:\\aa\\lego_fusion_beach1.jpg'

    #xbmc.executebuiltin('ActivateWindow(busydialog)')  #wouldn't work
    ui = qGUI('view_image.xml' , addon_path)   
    #no need to download the image. kodi does it automatically!!!
    ui.image_path=url
    ui.doModal()
    del ui
    return


    #this is a workaround to not being able to show images on video addon
    log('playSlideshow:'+url +'  ' + name )

    ui = ssGUI('tbp_main.xml' , addon_path)
    items=[]
    
    items.append({'pic': url ,'description': "", 'title' : name })
    
    ui.items=items
    ui.album_name=""
    ui.doModal()
    del ui
    return


    #this will also work:
    #download the image, then view it with view_image.xml.
#     url=url.split('?')[0]
#     
#     filename,ext=parse_filename_and_ext_from_url(url)
#     #empty_slideshow_folder()  # we're showing only 1 file
#     xbmc.executebuiltin('ActivateWindow(busydialog)')
# 
#     os.chdir(SlideshowCacheFolder)
#     download_file= filename+"."+ext
#     if os.path.exists(download_file):
#         log("  file exists")
#     else:
#         log('  downloading %s' %(download_file))
#         downloadurl(url, download_file)
#         log('  downloaded %s' %(download_file))
#     xbmc.executebuiltin('Dialog.Close(busydialog)')
# 
#     ui = qGUI('view_image.xml' , addon_path, 'default')
#     
#     ui.image_path=SlideshowCacheFolder + fd + download_file  #fd = // or \ depending on os
#     ui.doModal()
#     return
    

    #download_file=download_file.replace(r"\\",r"\\\\")

    #addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
    #i cannot get this to work reliably...
    #xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":"1","method":"Player.Open","params":{"item":{"directory":"%s"}}}' %(addonUserDataFolder) )
    #xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":"1","method":"Player.Open","params":{"item":{"directory":"%s"}}}' %(r"d:\\aa\\") )
    #xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":"1","method":"Player.Open","params":{"item":{"file":"%s"}}}' %(download_file) )
    #return

    #whis won't work if addon is a video add-on
    #xbmc.executebuiltin("XBMC.SlideShow(" + SlideshowCacheFolder + ")")
'''
def empty_slideshow_folder():
    for the_file in os.listdir(SlideshowCacheFolder):
        file_path = os.path.join(SlideshowCacheFolder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                #log("deleting:"+file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            log("empty_slideshow_folder error:"+e)    
'''    
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
# log("----------------------")
# log("params="+ str(params))
# log("mode="+ mode)
# log("type="+ typez) 
# log("name="+ name)
# log("url="+  url)
# log("pluginhandle:" + str(pluginhandle) )
# log("-----------------------")

if mode=='':mode='index'  #default mode is to list start page (index)
#plugin_modes holds the mode string and the function that will be called given the mode
plugin_modes = {'index'                 : index
                ,'listVideos'           : listVideos
                ,'listFavourites'       : listFavourites     
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
                }
#whenever a list item is clicked, this part handles it.
plugin_modes[mode](url,name,typez)

#    usually this plugin is called by a list item constructed like the one below
#         u = sys.argv[0]+"?url=&mode=addSubreddit&type="   #these are the arguments that is sent to our plugin and processed by plugin_modes
#         liz = xbmcgui.ListItem("Add Subreddit",label2="aaa", iconImage="DefaultFolder.png", thumbnailImage="")
#         liz.setInfo(type="Video", infoLabels={"Title": "aaaaaaa", "Plot": "description", "Aired": "daate", "mpaa": "aa"})
#         xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)



#the above dictionary(plugin_modes) replaces the if statements below
#all the functions need to accept 3 parameters
# if mode ==   'listVideos':            listVideos(url, type)
# elif mode == 'listSorting':           listSorting(url, type)
# elif mode == 'listFavourites':        listFavourites(url)
# elif mode == 'playVideo':             playVideo(url)
# elif mode == 'playLiveLeakVideo':     playLiveLeakVideo(url)
# elif mode == 'playGfycatVideo':       playGfycatVideo(url)
# elif mode == 'downloadLiveLeakVideo': downloadLiveLeakVideo(url)
# elif mode == 'downloadGfycatVideo':   downloadGfycatVideo(url)
# elif mode == 'addSubreddit':          addSubreddit(url)
# elif mode == 'removeSubreddit':       removeSubreddit(url)
# elif mode == 'autoPlay':              autoPlay(url, type)
# elif mode == 'queueVideo':            queueVideo(url, name)
# elif mode == 'addToFavs':             addToFavs(url, type)
# elif mode == 'removeFromFavs':        removeFromFavs(url, type)
# elif mode == 'searchAskOne':          searchAskOne(url, type)
# elif mode == 'searchAskTwo':          searchAskTwo(url, type)
# elif mode == 'searchVideos':          searchVideos(url, type)
# elif mode == 'searchReddits':         searchReddits()
# elif mode == 'openSettings':          openSettings(url)
# elif mode == 'toggleNSFW':            toggleNSFW()
# else:
#     index()


'''
#special credit to https://www.reddit.com/r/learnpython/comments/4pl11h/dynamically_instantiate_class_from_class_method/
# 6/24/2016 - this portion abandoned because it takes a long time to process. 
# dynamically instantiate a classes based on url. similar to how youtube_dl parses media content 
class hosterBase(object):
    
    def __init__(self, url):
        self.url = url

    @classmethod
    def from_url(cls, url):
        for subclass in cls.__subclasses__():
            if subclass.recc.match(url):
                return subclass(url)
            #if re.match(subclass.regex, url):   #            if sub.regex in url:
            #    return subclass(url)
        #raise ValueError('wtf is {}'.format(url))

#     @staticmethod
#     def from_url(url):
#         for cls in hosterBase.__subclasses__():
#             if re.match(cls.regex, url):
#                 return cls(url)
#         raise ValueError("URL %r does not match any image hosts" % url)


class cVidme(hosterBase):
    regex = 'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]*)'
    recc=re.compile(regex)

class b(hosterBase):
    regex = 'bbb'
    recc=re.compile(regex)    
    
    
#you call this class like:

    m = hosterBase.from_url(media_url)
    log("  "+str(m))
    if m:
        a = m.prep_media_url(media_url, assume_is_video)
        log("  " + a)
        #return
     
    
'''

