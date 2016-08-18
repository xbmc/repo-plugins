#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import urllib
import urllib2
import sys
import re
import requests 
import json

#sys.setdefaultencoding("utf-8")

from default import addon, comments_viewMode, streamable_quality   #,addon_path,pluginhandle,addonID
from default import log



show_youtube     = addon.getSetting("show_youtube") == "true"
use_ytdl_for_yt  = addon.getSetting("use_ytdl_for_yt") == "true"    #let youtube_dl addon handle youtube videos. this bypasses the age restriction prompt
show_vimeo       = addon.getSetting("show_vimeo") == "true"
show_liveleak    = addon.getSetting("show_liveleak") == "true"
show_dailymotion = addon.getSetting("show_dailymotion") == "true"
show_gfycat      = addon.getSetting("show_gfycat") == "true"
show_imgur       = addon.getSetting("show_imgur") == "true"
#show_i_redd_it   = addon.getSetting("show_i_redd_it") == "true"
#show_reddituploads=addon.getSetting("show_reddituploads") == "true"
show_vine        = addon.getSetting("show_vine") == "true"
show_streamable  = addon.getSetting("show_streamable") == "true"
show_vidme       = addon.getSetting("show_vidme") == "true"
show_instagram   = addon.getSetting("show_instagram") == "true"
show_blogspot    = addon.getSetting("show_blogspot") == "true"
show_pornsites   = addon.getSetting("show_pornsites") == "true"
show_reddit_com  = addon.getSetting("show_reddit_com") == "true"
show_ytdl_misc   = addon.getSetting("show_ytdl_misc") == "true"
show_tumblr      = addon.getSetting("show_tumblr") == "true"
show_gyazo       = addon.getSetting("show_gyazo") == "true" 
show_giphy       = addon.getSetting("show_giphy") == "true"
show_videoLink   = addon.getSetting("show_videoLink") == "true"
show_imageLink   = addon.getSetting("show_imageLink") == "true"
show_flickr      = addon.getSetting("show_flickr") == "true"


site00 = [show_youtube      , "playVideo"          ,'YouTube'      ,'(?:youtube(?:-nocookie)?\.com/(?:\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&;]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'    ,"plugin://plugin.video.youtube/play/?video_id=##vidID##"                , "site:youtu.be OR site:youtube.com" ]
#ite01 = [show_youtube      , "playVideo"          ,'YouTube'      ,'https?://www.youtube.com/attribution_link\?a=(.*)&'                                                          ,"plugin://plugin.video.youtube/play/?video_id=##vidID##"                , ""                      ] #leave the second site filter blank
site01 = [show_giphy        , "direct"             ,'Giphy'        ,'https?://(?:.+).giphy.com/'     ,"(not used)##vidID##"                                                   , "site:giphy.com"        ] 
site02 = [show_vimeo        , "playVideo"          ,'Vimeo'        ,'vimeo.com/(.*)'                 ,"plugin://plugin.video.vimeo/play/?video_id=##vidID##"                  , "site:vimeo.com"        ]
site03 = [show_dailymotion  , "playVideo"          ,'DailyMotion'  ,'dailymotion.com/video/(.*)_?'   ,"plugin://plugin.video.dailymotion_com/?mode=playVideo&url=##vidID##"   , "site:dailymotion.com"  ]
site04 = [show_dailymotion  , "playVideo"          ,'DailyMotion'  ,'dailymotion.com/.+?video=(.*)'  ,"plugin://plugin.video.dailymotion_com/?mode=playVideo&url=##vidID##"   , ""                      ]
site05 = [show_liveleak     , "playLiveLeakVideo"  ,'LiveLeak'     ,'liveleak.com/view\\?i=(.*)'     ,"##vidID##"                                                             , "site:liveleak.com"     ]
site06 = [show_gfycat       , "playGfycatVideo"    ,'Gfycat'       ,'gfycat.com/(.*)'                ,"##vidID##"                                                             , "site:gfycat.com"       ]
site07 = [show_imgur        , "playImgurVideo"     ,'Imgur'        ,'imgur\.com\/(.*)'               ,"##vidID##"                                                             , "site:imgur.com"        ]
site08 = [show_imageLink    , "playSlideshow"      ,'Redd.it'      ,'i.redd.it\/(.*)'                ,"##vidID##"                                                             , "site:redd.it"        ]
site09 = [show_imageLink    , "playSlideshow"      ,'RedditMedia'  ,'\.(?:reddituploads|redditmedia).com/(.+)'       ,"##vidID##"                                             , "site:redditmedia.com"        ]
site10 = [show_vine         , "playVineVideo"      ,'Vine'         ,'vine\.co\/(.*)'                 ,"(not used) ##vidID##"                                                  , "site:vine.co"        ]
site11 = [show_streamable   , "playStreamable"     ,'Streamable'   ,'streamable\.com/(.*)'           ,"(not used) ##vidID##"                                                  , "site:streamable.com"        ]
site12 = [show_vidme        , "playVidmeVideo"     ,'Vidme'        ,'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]*)' ,"(not used) ##vidID##"                                     , "site:vid.me"        ]
site13 = [show_instagram    , "playYTDLVideo"      ,'Instagram'    ,'(?P<url>https?://(?:www\.)?instagram\.com/p/(?P<id>[^/?#&]+))' ,"(not used) ##vidID##"                   , "site:Instagram.com"        ]
site14 = [show_blogspot     , "playSlideshow"      ,'Blogspot'     ,'(https?://.*\.blogspot\.com/.*)(jpg|gif|png)'       ,"(not used) ##vidID##"                              , "site:blogspot.com"        ]
site15 = [show_reddit_com   , "playReddit"         ,'Reddit.com'   ,'reddit.com'                     ,"(not used)##vidID##"                                                   , "site:reddit.com"        ]
site16 = [show_tumblr       , "done in code"       ,'Tumblr'       ,'tumblr.com'                     ,"(not used)##vidID##"                                                   , "site:tumblr.com"        ]
site17 = [show_gyazo        , "done in code"       ,'Gyazo'        ,'gyazo.com'                      ,"(not used)##vidID##"                                                   , "site:gyazo.com"        ]
site18 = [show_flickr       , "playFlickr"         ,'Flickr'       ,'flickr.com'                     ,"(not used)##vidID##"                                                   , "site:flickr.com"        ]
site28 = [show_videoLink    , "direct"             ,'video link'   ,"\.(mp4|webm|gifv)(?:\?|$)"      ,"(not used) ##vidID##"                                                   , ""        ]
site29 = [show_imageLink    , "playSlideshow"      ,'image link'   ,"\.(jpg|jpeg|png|gif)(?:\?|$)"   ,"(not used) ##vidID##"                                                   , ""        ]
site30 = [show_ytdl_misc    , "playYTDLVideo"      ,'misc1'        ,"(nbcsports.com)|(nbcnews.com)|(nbc\.com\/.+\/video\/)|(mlb.com/video)|(localnews8.com)|(ellentv.com/videos)|(video.cnbc.com)|(canalplus.fr)|(allocine.fr)|(spiegel.tv)","(not used) ##vidID##", ""        ]
site31 = [show_ytdl_misc    , "playYTDLVideo"      ,'misc2'        ,"(pandora.tv)|(ora.tv)|(on.aol.com/video)|(ok.ru/video)|(npo.nl)|(nowvideo.sx/video)|(nick.com/videos)|(nerdcubed.co.uk/videos)|(tvcast.naver.com/v)|(MySpass.de)|(mva.microsoft.com)|(musicplayon.com)|(mtv.com/videos)|(mpora.com/videos)|(moviezine.se)|(allmyvideos.net)|(mojvideo.com)|(miomio.tv)|(mgtv.com)|(mgoon.com)|(maker.tv/video)|(makerschannel.com)|(lynda.com)|(alfa.lt/visi-video)|(life.ru/video)|(ku6.com)|(kontrtube.ru)|(konserthusetplay.se)|(khanacademy.org)|(keek.com)|(kaltura.com)|(jwplatform.com)|(jpopsuki.tv)|(jove.com/video)|(jeuxvideo.com/videos)|(izlesene.com)|(iqiyi.com/v_)|(iprima.cz)|(indavideo.hu)|(ina.fr/video)|(ign.com/videos)|(historicfilms.com)|(godtube.com)|(gdcvault.com)|(gamekings.tv/videos)|(freespeech.org/video)|(footyroom.com)|(fernsehkritik.tv)|(myaidol.net)|(c48.org)|(show48.com)|(dai.ly)|(features.aol.com)|(video.esri.com)|(escapistmagazine.com/videos)|(ebaumsworld.com/videos)|(video.aktualne.cz)|(dotsub.com)|(discovery.com)|(dbtv.no)|(csnne.com/video)|(collegerama.tudelft.nl)|(cnn.com)|(clubic.com/video)|(closertotruth.com)|(clipsyndicate.com)|(clipfish.de)|(chilloutzone.net/video)|(channel9.msdn.com)|(carambatv.ru)|(canvas.net)|(brightcove.com)|(bilibili.com)|(bambuser.com)|(arte.tv)|(ardmediathek.de)|(aparat.com)|(air.mozilla.org)|(tv.adobe.com)|(vevo.com)|(cc.com)|(comediansincarsgettingcoffee.com)|(trailers.apple.com)|(devour.com)|(funnyclips.me)|(engagemedia.org)|(videosift.com)|(break.com)|(veoh.com)|(viddler.com)|(schooltube.com)|(videos.sapo.pt)|(funnyordie.com)","(not used) ##vidID##", ""        ]
site32 = [show_pornsites    , "playYTDLVideo"      ,'porn'         ,"(3movs.com)|(4tube.com)|(91porn.com)|(alphaporno.com)|(animestigma.com)|(anysex.com)|(beeg.com)|(burningcamel.com)|(cliphunter.com)|(crocotube.com)|(cutegirlsgifs.info)|(daporn.com)|(deviantclip.com)|(drtuber.com)|(efukt.com)|(empflix.com)|(eroprofile.com)|(eroshare.com)|(eroxia.com)|(extremetube.com)|(faapy.com)|(fapality.com)|(fapdu.com)|(faptube.xyz)|(femdom-tube.com)|(fuckuh.com)|(hclips.com)|(hdporn.net)|(hellporno.com)|(hornbunny.com)|(hotgoo.com)|(japan-whores.com)|(keezmovies.com)|(lovehomeporn.com)|(madthumbs.com)|(motherless.com)|(mofosex.com)|(www.moviefap.com)|(my18tube.com)|(mylust.com)|(myvidster.com)|(nuvid.com)|(onlypron.com)|(panapin.com)|(porndoe.com)|(porneq.com)|(pornfun.com)|(pornhd.com)|(pornhost.com)|(pornhub.com)|(pornoxo.com)|(pornrabbit.com)|(porntrex.com)|(pussy.com)|(redclip.xyz)|(redtube.com)|(secret.sex)|(sendvid.com)|(sex24open.com)|(sex3.com)|(sexfactor.com)|(shameless.com)|(slutload.com)|(smotri.com)|(spankbang.com)|(spankingtube.com)|(spankwire.com)|(stickyxxx.com)|(stileproject.com)|(sunporno.com)|(submityourflicks.com)|(teenfucktory.com)|(thisav.com)|(thisvid.com)|(tnaflix.com)|(tube8.com)|(txxx.com)|(videolovesyou.com)|(vporn.com)|(worldsex.com)|(xbabe.com)|(xbabe.com)|(xcafe.com)|(xcum.com)|(xhamster.com)|(xnxx.com)|(xogogo.com)|(xtube.com)|(xvideos.com)|(xvids.us)|(xxxaporn.com)|(xxxymovies.com)|(xxxyours.com)|(youjizz.com)|(youporn.com)|(zedporn.com)","(not used) ##vidID##", ""        ]
site99 = [0,''              , "video" ,''          ,''             ,""                                                                      , ""                      ]
#to add: vidmero.com/gifs.com  playlink.xyz  facebook.com  vrchive.com   
supported_sites = [site00,site01,site02,site03,site04,site05,site06,site07,site08,site09,site10,site11,site12,site13,site14,site15,site16,site17,site18,site28,site29,site30,site31,site32]

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
    #request_header={ "Authorization": "Client-Id a594f39e5d61396" }
    request_header={ "Authorization": "Client-Id 7b82c479230b85f" }
    
    
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
        #log("    imgur:check if album- request_url---"+request_url )
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
        #log("  ask_imgur_for_link: "+media_url )
        
        media_url=media_url.split('?')[0] #get rid of the query string
        img_id =media_url.split("com/",1)[1]  #.... just get whatever is after "imgur.com/"   hope nothing is beyond the id
        
        #log("  ask_imgur_for_link: "+img_id )
        
        #6/30/2016: noticed a link like this: http://imgur.com/topic/Aww/FErKmLG
        if '/' in img_id:
            #log("  split_ask_imgur_for_link: "+ str( img_id.split('/')) )
            img_id = img_id.split('/')[-1]     #the -1 gets the last item on the list returned by split

        if img_id:
            request_url="https://api.imgur.com/3/image/"+img_id
            #log("  imgur check link- request_url---"+request_url )
            r = requests.get(request_url, headers=ClassImgur.request_header)
            #log(r.text)
            if r.status_code == 200:   #http status code 200 is success
                j = r.json()    #j = json.loads(r.text)
            
                #log('link is ' + j['data'].get('link') )
                return j['data'].get('link')
            else:
                log("    ask_imgur_for_link ERROR:" + r.text)
        
        return ''

    def ret_thumb_url(self, image_url, thumbnail_type='b'):
        #return the thumbnail url given the image url
        #accomplished by appending a 'b' at the end of the filename       
        #this won't work if there is a '/gallery/' in the url

        #possible thumbnail_types
        #    s = Small Square (90�90) 
        #    b = Big Square (160�160)
        #    t = Small Thumbnail (160�160)
        #    m = Medium Thumbnail (320�320)
        #    l = Large Thumbnail (640�640) 
        #    h = Huge Thumbnail (1024�1024)
        
        from urlparse import urlparse
        o=urlparse(image_url)    #from urlparse import urlparse
        filename,ext=parse_filename_and_ext_from_url(image_url) 
        #log("file&ext------"+filename+"--"+ext+"--"+o.netloc )
        
        #imgur url's sometimes do not have an extension and we don't know if it is an image or video
        if ext=="":
            #log("ret_thumb_url["+ o.path[1:] ) #starts with / use [1:] to skip 1st character
            filename = o.path[1:]
            ext = 'jpg'
        elif ext in ['gif', 'gifv', 'webm', 'mp4']:
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
                
                #filename,ext=parse_filename_and_ext_from_url(media_url)
                #if description=='' or description==None: description=filename+"."+ext
                
                media_thumb_url=self.ret_thumb_url(media_url,thumbnail_size_code)
                #log("media_url----"+media_url) 
                #log("media_thumb_url----"+media_thumb_url)
                #log(str(idx)+type+" [" + str(description)+']'+media_url+" "  ) 
                list_item_name = entry['title'] #if entry['title'] else str(idx).zfill(2)
                
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
    
    def get_playable_url(self, media_url, is_probably_a_video): #is_probably_a_video means put video extension on it if media_url has no ext
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
                log('      media_link from /gallery/: '+str(media_url))

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
                
        if ext in ['gif', 'gifv'] :
            media_url=media_url.replace(".gifv",webm_or_mp4) #can also use .mp4.  crass but this method uses no additional bandwidth.  see playImgurVideo
            media_url=media_url.replace(".gif",webm_or_mp4)  #xbmc won't play gif but replacing .webm works!
            is_video=True
            #lizb.setInfo(type='video', infoLabels=il)
        elif ext in image_exts:    #image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp']
            is_video=False
        else:
            is_video=False
            
        #log("    media url return=["+media_url+'] vid:' + str(is_video ))
        return media_url, is_video

class ClassVidme:
    
    #request_header={ "Authorization": "Basic " + base64_encode($key . ':') }
    request_header={ "Authorization": "Basic aneKgeMUCpXv6FdJt8YGRznHk4VeY6Ps:" }
    media_status=""
    
    def __init__(self, media_url):
        return
    
    def get_playable_url(self,media_url, is_probably_a_video):
        #https://docs.vid.me/#api-Video-DetailByURL
        #request_url="https://api.vid.me/videoByUrl/"+videoID
        request_url="https://api.vid.me/videoByUrl?url="+ urllib.quote_plus( media_url )
        
        #log("vidme request_url---"+request_url )
        r = requests.get(request_url, headers=ClassVidme.request_header)
        #log(r.text)

        if r.status_code != 200:   #http status code 200 is success
            #log("  vidme request returned: "+ str(r.text))
            
            #try to get media id from link.
            #media_url='https://vid.me/Wo3S/skeletrump-greatest-insults'
            #media_url='https://vid.me/Wo3S'
            id=re.findall( 'vid\.me/(.+?)(?:/|$)', media_url )   #***** regex capture to end-of-string or delimiter. didn't work while testing on https://regex101.com/#python but will capture fine 
            
            request_url="https://api.vid.me/videoByUrl/" + id[0]

            r = requests.get(request_url, headers=ClassVidme.request_header)
            #log(r.text)
            if r.status_code != 200:
                log("  vidme request still returned "+ str(r.text) )
                #t= r.json()
                #self.media_status=t['error']
                #xbmc.executebuiltin('XBMC.Notification("Vidme",%s)' %(r.text) )
                return True  #i got a 404 on one item that turns out to be an album when checked in browser. i'll just return true



        j = r.json()    #j = json.loads(r.text)

        #for attribute, value in j.iteritems():
        #    log(  str(attribute) + '==' + str(value))
        status = j['video'].get( 'state' )
        
        log( "    vidme video state: " + status ) #success / suspended / deleted
        self.media_status=status
        return ( j['video']['complete_url'] )

    def whats_wrong(self):
        return str( self.media_status )

class ClassVine:
    def __init__(self,media_url):
        return 
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
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
        #log("get_playable_url vine- request_url---"+request_url )
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
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
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
        #call this after calling get_playable_url
        return self.thumb_url
    
    def get_playable_url(self, media_url, is_probably_a_video=True ):
        #log('class tumblr prep media url')

        #first, determine if the media_url leads to a media(.jpg .png .gif)
        filename,ext=parse_filename_and_ext_from_url(media_url)
        if ext in image_exts:
            return media_url,"photo"
        elif ext in ["mp4","gif"]:
            return media_url,"video"

        # don't check for media.tumblr.com because
        #there are instances where medis_url is "https://vt.tumblr.com/tumblr_o1jl6p5V5N1qjuffn_480.mp4#_=_"
#         if 'media.tumblr.com' in media_url:
#             if ext in image_exts:
#                 return media_url,"photo"
#             elif ext in ["mp4","gif"]:
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
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
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
                elif ext in ['gif','gifv']:
                    self.media_is_an_image=False
                    contentUrl= bs_ext[0][0] + "webm"    #change gif extension to webm
                    
            except Exception as e:
                log("  EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )    
                  
        return contentUrl

class ClassInstagram:
    def __init__(self, media_url=""):
        return
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
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

class ClassGyazo:
    def __init__(self, media_url=""):
        return
    
    def get_playable_url(self, media_url, is_probably_a_video=True):

        #first, determine if the media_url leads to a media(.jpg .png .gif)
        filename,ext=parse_filename_and_ext_from_url(media_url)
        if ext in image_exts:
            return media_url,"photo"
        elif ext in ["mp4","gif"]:
            return media_url,"video"

        #media_url='http://gyazo.com/b8c993ab1435171eafefb882d8e2d17a'
        api_url='https://api.gyazo.com/api/oembed?url=%s' %(media_url )
        
        r = requests.get(api_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j=json.loads(r.text.replace('\\"', '\''))
        
            media_type=j['type']    
            media_url=j['url']
                  
        return media_url,media_type
    
class ClassFlickr:
    def __init__(self, media_url=""):
        return
    
    api_key='a3662f98e08266dca430404d37d8dc95'
    thumb_url=""
    poster_url=""
    
    def ret_thumb_url(self, image_url="", thumbnail_type='b'):
        #call this after calling get_playable_url
        return self.thumb_url
    
    def get_playable_url(self, media_url, is_probably_a_video=True ):
        media_type="photo"
        ret_url=""
        
        #first, determine if the media_url leads to a media(.jpg .png .gif)
        #this is not likely coz flickr does not like it and i've not seen posts that do it
        filename,ext=parse_filename_and_ext_from_url(media_url)
        if ext in image_exts:
            return media_url,"photo"
        elif ext in ["mp4","gif"]:
            return media_url,"video"


        #get the photoID
        match = re.findall('flickr\.com\/photos\/(?:.+\/)?(\d+)',media_url)

        photo_id=match[0]
        #log( " *****" + str(match) )

        if '/sets/' in media_url:
            media_type="album"
            api_method='flickr.photosets.getPhotos'
            api_arg='photoset_id=%s' %photo_id
        else:
            media_type="photo"
            api_method='flickr.photos.getSizes'
            api_arg='photo_id=%s' %photo_id
            
        api_url='https://api.flickr.com/services/rest/?format=json&nojsoncallback=1&api_key=%s&method=%s&%s' %(self.api_key,api_method,api_arg )

        #log('  flickr apiurl:'+api_url)
        r = requests.get(api_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j=json.loads(r.text.replace('\\"', '\''))
            
            
            if media_type=='album':   #for  #photosets, galleries, pools? panda?
                photos=j['photoset']['photo']
                '''
                You can construct the source URL to a photo once you know its ID, server ID, farm ID and secret, as returned by many API methods.
                The URL takes the following format:
                https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}.jpg
                https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}_[mstzb].jpg
                https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{o-secret}_o.(jpg|gif|png)
                    The letter suffixes are as follows:
                    s    small square 75x75
                    q    large square 150x150
                    t    thumbnail, 100 on longest side
                    m    small, 240 on longest side
                    n    small, 320 on longest side
                    -    medium, 500 on longest side
                    z    medium 640, 640 on longest side
                    c    medium 800, 800 on longest side†
                    b    large, 1024 on longest side*
                    h    large 1600, 1600 on longest side†
                    k    large 2048, 2048 on longest side†
                    o    original image, either a jpg, gif or png, depending on source format                
                '''
                dictList=[]
                for i, p in enumerate( photos ):
                    photo_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'b' )
                    thumb_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'n' )
                    #log(" %d  %s" %(i,photo_url ))

                    infoLabels={ "Title": p['title'], "plot": p['title'], "PictureDesc": '', "exif:exifcomment": '' }
                    e=[ p['title'] if p['title'] else str(i+1)             #'li_label'           #  the text that will show for the list  (list label will be the caption or number if caption is blank)
                       ,p['title']                                         #'li_label2'          #  
                       ,""                                                 #'li_iconImage'       #
                       ,thumb_url                                          #'li_thumbnailImage'  #
                       ,photo_url                                          #'DirectoryItem_url'  #  
                       ,False                                              #'is_folder'          # 
                       ,'pictures'                                         #'type'               # video pictures  liz.setInfo(type='pictures',
                       ,True                                               #'isPlayable'         # key:value       liz.setProperty('IsPlayable', 'true')  #there are other properties but we only use this 
                       ,infoLabels                                         #'infoLabels'         # {"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin
                       ,'none'                                             #'context_menu'       # ...
                          ]
                 
                    dictList.append(dict(zip(keys, e)))
                    
                return dictList, 'album'
                
            elif media_type=='photo':
            
                sizes=j['sizes']
                #log('    sizes' + str(sizes))
                #Square, Large Square, Thumbnail, Small, Small 320, Medium, Medium 640, Medium 800, Large, Large 1600, Large 2048, Original
                for s in sizes['size']:
                    #log('    images size %s url=%s' %( s['label'], s['source']  ) )
                    if s['label'] == 'Medium 800':    
                        poster_url=s['source']
                    if s['label'] == 'Large':    #case sensitive
                        ret_url=s['source']
                        media_type=s['media']
                
                    
        return ret_url, media_type

class ClassGifsCom:
    #also vidmero.com
    def __init__(self, media_url=""):
        return
    
    api_key='gifs577da09e94ee1'   #gifs577da0485bf2a'
    headers = { 'Gifs-API-Key': api_key, 'Content-Type': "application/json" }
    
    thumb_url=""
    poster_url=""
    
    def ret_thumb_url(self, image_url="", thumbnail_type='b'):
        #call this after calling get_playable_url
        return self.thumb_url
    
    def get_playable_url(self, media_url, is_probably_a_video=True ):
        media_type="photo"
        ret_url=""
        
        #first, determine if the media_url leads to a media(.jpg .png .gif)
        #this is not likely coz flickr does not like it and i've not seen posts that do it
        filename,ext=parse_filename_and_ext_from_url(media_url)
        if ext in image_exts:
            return media_url,"photo"
        elif ext in ["mp4","gif"]:
            return media_url,"video"


        #get the photoID
        #match = re.findall('flickr\.com\/photos\/(?:.+\/)?(\d+)',media_url)
        #photo_id=match[0]
        #log( " *****" + str(match) )

        request_url="https://api.gifs.com"
        #log("listImgurAlbum-request_url---"+request_url )
        r = requests.get(request_url, headers=ClassVidme.request_header)
        
        if r.status_code==200:  #http status code 200 = success
            j=json.loads(r.text.replace('\\"', '\''))
            

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



def make_addon_url_from(media_url, assume_is_video=True ):
    #returns tuple.  info ready for plugging into  addDirectoryItem
    #if url_for_DirectoryItem is blank, then assume media url is not supported.
    #  the returned videoID/pluginUrl is the resolved media url. (depends on hoster) 

    pluginUrl=""     #resolved media url
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



    log( "    Checking link %s" %media_url) 
    if media_url :

        #search our supported_sites[] to see if media_url can be handled by plugin
        for site in supported_sites :
            if site[0]:  #site[0]  is the show_youtube/show_vimeo/show_dailymotion/... global variables taken from settings file
                match = re.compile( site[3]  , re.DOTALL).findall( media_url )
                if match : break
    
        if match:
            #log("  make_addon_url_from:match on hoster="+site[2])
            hoster = site[2]
            modecommand = site[1]  #
            #vimeo and liveleak sometimes have extra string after the video ID, we process
            if   hoster==site02[2] : videoID = match[0].replace("#", "").split("?")[0]  #'vimeo'
            elif hoster==site05[2] : videoID = match[0].split("#")[0]                   #'liveleak': 
            else                   : videoID = match[0]
    
            try:
                #figure out the thumbnail url. usually, reddit returns the thumbnail url but doesn't do so for nsfw
                #log("determine [%s] thumb from ID[%s] url[%s]" %(hoster,videoID,media_url))
                if hoster=="YouTube":   #**** this is case sensitive make sure it matches text defined in supported_sites[]
                    thumb_url=ret_youtube_thumbnail(videoID,0)  
                    #log("[%s] thumb_url from ID[%s] is[%s]" %(hoster,videoID,thumb_url))
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
                    from resources.domains import ClassImgur
                    c=ClassImgur()
                    #thumb_url=c.ret_thumb_url( media_url )
                    #log('thumb_url '+thumb_url)
                    prepped_media_url, is_video = c.get_playable_url(media_url, assume_is_video)
                    #log( "  Imgur prepped_media_url="+prepped_media_url)
                    if prepped_media_url=='':     #not imgur
                        flag_media_not_supported=True
                        log('  not imgur') # sometimes imgur post is deleted
                    else:
                        thumb_url=c.ret_thumb_url( prepped_media_url )
                        #log('  thumb_url:'+thumb_url)
                        
                        if prepped_media_url=='album':
                            pluginUrl=media_url
                            modecommand='listImgurAlbum'
                            setProperty_IsPlayable='false'
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
                    ret_url, media_type =t.get_playable_url(media_url, assume_is_video)
                    log( "   tumblr media type is [" + media_type +"]" )
                    if media_type=='album':
                        modecommand='listTumblrAlbum'
                        poster_url=t.ret_thumb_url() #if poster+url =="" is taken care of by calling function
                        pluginUrl=media_url  #we don't use the ret_url here. ret_url is a dictlist of images
                        setProperty_IsPlayable='false'
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
                    elif media_type in ['audio','answer','text']:
                        log("  tumblr media (%s) not supported" %(media_type) )
                        flag_media_not_supported=True   
                    elif media_type=='video':
                        thumb_url=t.ret_thumb_url()
                        poster_url=thumb_url
                        pluginUrl=ret_url
                        replace_url_for_DirectoryItem=ret_url
                        modecommand='direct'  #no need to call plugin with a 'mode' just have xbmc handle the stream directly
                    else:
                        log("  unknown tumblr media" )
                        flag_media_not_supported=True
    
                elif hoster == 'Gyazo':
                    pluginUrl=media_url
                    g=ClassGyazo(media_url)
                    ret_url, media_type =g.get_playable_url(media_url, assume_is_video)
                    #log( "   gyazo media type is [" + media_type +"] " + ret_url)
                    filename,ext=parse_filename_and_ext_from_url(ret_url)
                    if ext == 'gif':            
                        media_type='video'      #force media type to video
                        #ret_url=ret_url.replace('gif','mp4')   #replacing 'gif' to 'mp4' plays on browser but not on kodi 
                    
                    if media_type=='photo':
                        modecommand='playSlideshow'
                        thumb_url=ret_url
                        pluginUrl=ret_url
                        setProperty_IsPlayable='false'
                        setInfo_type='pictures'
                    elif media_type=='video':
                        #thumb_url=t.ret_thumb_url()
                        #poster_url=thumb_url
                        pluginUrl=ret_url
                        replace_url_for_DirectoryItem=ret_url
                        modecommand='direct'  #no need to call plugin with a 'mode' just have xbmc handle the stream directly
                    else:
                        log("  unknown gyazo media" )
                        flag_media_not_supported=True
                    
                elif hoster in ["Redd.it", "RedditUploads", "RedditMedia", "image link"]:
                    media_url=media_url.replace('&amp;','&')  #this replace is only for  RedditUploads but seems harmless for the others...
                    pluginUrl=media_url  
                    
                    from urlparse import urlparse
                    hoster=urlparse(media_url).netloc
    
                    modecommand='playSlideshow'
                    #replace_url_for_DirectoryItem=media_url      #this is for direct linking the media in the directory item  xbmc prefers this mode but this only works on image addon since this media most likely is an image
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
    
                elif hoster=="Flickr":
                    pluginUrl=media_url 
                    setProperty_IsPlayable='false'
    
                    if '/sets/' in media_url:   #indicates that this is an album
                        modecommand='listFlickrAlbum'
                        setProperty_IsPlayable='false'
                        isFolder=True
                    else:
                        setInfo_type='pictures'
                        
    
                    
                    #modecommand='listLinksInComment'    #
                    #setProperty_IsPlayable='false'
                    #isFolder=True                                 #<-- this is important. tells kodi that this will open another listing. fixes WARNING: Attempt to use invalid handle -1
    
                elif hoster in ["Vine","Vidme"]:
                    #v=ClassVine(media_url)
                    #replace_url_for_DirectoryItem='https://v.cdn.vine.co/r/videos/38B4A9174D1177703702723739648_37968e655a0.1.5.1461921223578533188.mp4'
                    #replace_url_for_DirectoryItem=v.get_playable_url(media_url, True)    #this is for direct link on the directory item  xbmc prefers this mode but we don't use it.
                    #   because it involves querying vine(for the .mp4 link) for each item. 
                    #   this adds a short delay on the directory listing(that will add up).
                    #log('m:'+ media_url)
                    #log('p:'+pluginUrl)
                    pluginUrl=media_url
                    thumb_url=""
                elif hoster=="Streamable":
                    pluginUrl=media_url
                    s=ClassStreamable(media_url)
                    #replace_url_for_DirectoryItem=s.get_playable_url(media_url,True )  6/18/2016  direct linking doesn't work anymore
                    #replace_url_for_DirectoryItem="https://cdn.streamable.com/video/mp4/dw9f.mp4"
                    thumb_url=s.ret_thumb_url()
                elif hoster=="Blogspot":
                    b=ClassBlogspot(media_url)
                    pluginUrl=b.get_playable_url(media_url,assume_is_video )
                    if b.media_is_an_image:
                        modecommand='playSlideshow'
                        setProperty_IsPlayable='false'
                        thumb_url=pluginUrl
                        setInfo_type='pictures'   #to get the [IMG] tag
                    else:
                        replace_url_for_DirectoryItem=pluginUrl
    
                elif hoster=="video link":     #a direct link to the video media
                    pluginUrl=media_url
                    replace_url_for_DirectoryItem=media_url
                    modecommand='direct'
                    from urlparse import urlparse
                    hoster=urlparse(media_url).netloc
                    setProperty_IsPlayable='true'
                elif hoster in ['Instagram','porn','misc1','misc2']:   #everything here is handled by the Youtube_dl plugin by ruuk
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
                    elif hoster in ['porn','misc1','misc2']: #hoster will show in description. we replace it with the match to inform user where video is hosted
                        #log('pr0n')
                        for n in match[0]:
                            if n:
                                hoster=str( n )
            except Exception as e:
                log("    EXCEPTION:"+ str( sys.exc_info()[0]) + "  " + str(e) )    
                
                flag_media_not_supported=True
                                
            #log ("  replace direct: "+replace_url_for_DirectoryItem)
            if replace_url_for_DirectoryItem:
                url_for_DirectoryItem = replace_url_for_DirectoryItem
                #log ("  direct link: "+url_for_DirectoryItem)
            else:
                url_for_DirectoryItem = sys.argv[0]+"?url="+ urllib.quote_plus(pluginUrl) +"&mode="+str(modecommand)  #sys.argv[0] is "plugin://plugin.video.reddit_viewer/"
    
        else:  # if match:
            flag_media_not_supported=True
            
        
    if flag_media_not_supported:  #caller checks for the returned DirectoryItem_url. if it is blank, it is unsupported.
        log("    unsupported [%s]" %media_url)
        url_for_DirectoryItem = "" 
     
    #log( "    %s vid=%s playable=%s di_url=%s" %( hoster ,videoID, setProperty_IsPlayable, url_for_DirectoryItem)  )
    return hoster, url_for_DirectoryItem, pluginUrl, modecommand, thumb_url, poster_url, isFolder, setInfo_type,setProperty_IsPlayable


def url_is_supported(url_to_check):
    #search our supported_sites[] to see if media_url can be handled by plugin
    #returns the regex match
    for site in supported_sites :
        if site[0]:  #site[0]  is the show_youtube/show_vimeo/show_dailymotion/... global variables taken from settings file
            match = re.compile( site[3]  , re.DOTALL).findall(url_to_check)
            if match : 
                return True

    return False

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
        a = m.get_playable_url(media_url, assume_is_video)
        log("  " + a)
        #return
     
    
'''
