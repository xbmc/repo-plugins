#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import urllib
import urllib2
import sys
import re
import requests 
import json
import xbmc
import xbmcgui
#sys.setdefaultencoding("utf-8")

from default import addon, addonID, streamable_quality   #,addon_path,pluginhandle,addonID
from default import log, dump, translation

from default import default_ytdl_psites_file, default_ytdl_sites_file, playVideo, addon_path, use_ytdl_for_unknown_in_comments, reddit_userAgent
from utils import build_script, parse_filename_and_ext_from_url, image_exts, link_url_is_playable, remove_duplicates, safe_cast

use_ytdl_for_yt  = addon.getSetting("use_ytdl_for_yt") == "true"    #let youtube_dl addon handle youtube videos. this bypasses the age restriction prompt


from CommonFunctions import parseDOM
import pprint

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
      ,'width'
      ,'height'
      ,'description'
      ]

ytdl_sites=[]

#deviantart mixtape.moe sli.mg 

class sitesBase(object):
    regex=''
    thumb_url=''
    poster_url=''
    media_type=''
    link_action=''   #'playable' for direct video links or one of the "modes" used by this script
    dictList = []   #used by assemble_images_dict ret_album_list and 
    media_url=''
    original_url=''
    media_w=0
    media_h=0
    
    include_gif_in_get_playable=False   #it is best to parse the link and get the mp4/webm version of a gif media. we can't do this with some sites so we just return the gif media instead of looking for mp4/webm

    TYPE_IMAGE='image'
    TYPE_ALBUM='album'
    TYPE_VIDEO='video'
    TYPE_VIDS ='vids'
    TYPE_MIXED='mixed'
    TYPE_REDDIT='reddit'
    DI_ACTION_PLAYABLE='playable'
    DI_ACTION_YTDL='playYTDLVideo'
    
    def __init__(self, link_url):
        self.media_url=link_url
        self.original_url=link_url

    def get_html(self,link_url=''):
        if not link_url:
            link_url=self.original_url
        
        content = requests.get( link_url )
        
        if content.status_code==200:
            return content.text
        else:
            log('    error: %s get_html: %s %s' %(self.__class__.__name__, repr( content.status_code ), link_url ) )
            return None
    
    def get_playable(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url
            
        filename,ext=parse_filename_and_ext_from_url(media_url)
        if self.include_gif_in_get_playable:
            if ext in ["mp4","webm","gif"]:
                if ext=='gif':
                    self.link_action=sitesBase.DI_ACTION_PLAYABLE
                    self.thumb_url=media_url
                    self.poster_url=self.thumb_url
                return media_url,self.TYPE_VIDEO
        else:
            if ext in ["mp4","webm"]:
                self.link_action=self.DI_ACTION_PLAYABLE
                return self.media_url,self.TYPE_VIDEO

        if ext in image_exts:  #excludes .gif
            self.thumb_url=media_url
            self.poster_url=self.thumb_url
            return self.media_url,self.TYPE_IMAGE

        return self.get_playable_url(self.media_url, is_probably_a_video=False )
    
    def get_playable_url(self, media_url, is_probably_a_video ):
        raise NotImplementedError
        
    def get_thumb_url(self):
        raise NotImplementedError

    def request_meta_ogimage_content(self,link_url=''):
        if not link_url: link_url=self.media_url

        m_type=link_url_is_playable(link_url)
        if m_type:
            #if m_type=='image': return link_url
            return link_url #will a video link resolve to a preview image?
        else:  
            #content = requests.get( link_url, timeout=(0.5, 1) )
            content = requests.get( link_url )
            if content.status_code==200:
                i=parseDOM(content.text, "meta", attrs = { "property": "og:image" }, ret="content" )
                if i[0]:
                    return i[0]
                else:
                    log('      %s: cant find <meta property="og:image" '  %(self.__class__.__name__ ) )
            else:
                log('    %s :get_thumb_url: %s ' %(self.__class__.__name__, repr(content.status_code) ) )
    
    def all_same(self, items ):
        #returns True if all items the same
        return all(x == items[0] for x in items)
    #def combine_title_and_description(self, title, description):
    #    return ( '[B]'+title+'[/B]\n' if title else '' ) + ( description if description else '' )
    
    def clog(self, error_code, request_url):
        log("    %s error:%s %s" %( self.__class__.__name__, error_code ,request_url) )
    
    def assemble_images_dictList(self,images_list):
        title=''
        desc=''
        image_url=''
        thumbnail=''
        width=0
        height=0
        for item in images_list:
            #log('      type: %s' %( type(item)  ) )
            if type(item) in [str,unicode]:  #if isinstance(item, basestring):
                #log( 'assemble_images_dictList STRING')
                image_url=item
                thumbnail=image_url
            elif type(item) is list:
                if len(item)==1:
                    #log( 'assemble_images_dictList LEN1')
                    image_url=item[0]
                elif len(item)==2:
                    #log( 'assemble_images_dictList LEN2')
                    title=item[0]
                    image_url=item[1]
                    thumbnail=image_url
                elif len(item)==3:
                    #log( 'assemble_images_dictList LEN3')
                    title=item[0]
                    image_url=item[1]
                    thumbnail=item[2]
            elif type(item) is dict:
                title    =item.get('title') if item.get('title') else ''
                desc     =item.get('description') if item.get('description') else ''
                image_url=item.get('url')
                thumbnail=item.get('thumb')
                width    =item.get('width') if item.get('width') else 0
                height   =item.get('height') if item.get('height') else 0
                
            
                    
            infoLabels={ "Title": title, "plot": desc, "PictureDesc": desc }
            e=[ title                   #'li_label'           #  the text that will show for the list (we use description because most albumd does not have entry['type']
               ,''                      #'li_label2'          #  
               ,""                      #'li_iconImage'       #
               ,thumbnail               #'li_thumbnailImage'  #
               ,image_url               #'DirectoryItem_url'  #  
               ,False                   #'is_folder'          # 
               ,'pictures'              #'type'               # video pictures  liz.setInfo(type='pictures',
               ,True                    #'isPlayable'         # key:value       liz.setProperty('IsPlayable', 'true')  #there are other properties but we only use this 
               ,infoLabels              #'infoLabels'         # {"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin
               ,'none'                  #'context_menu'       # ...
               ,width
               ,height 
               ,desc   
                ]
            self.dictList.append(dict(zip(keys, e)))
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

class ClassYoutube(sitesBase):      
    regex='(youtube.com/)|(youtu.be/)'      
    video_id=''
    
    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url
            
        self.get_video_id()
        log('      youtube video id:' + self.video_id )
        
        if self.video_id:
            if use_ytdl_for_yt:
                self.link_action='playYTDLVideo'
                return "http://youtube.com/v/" + self.video_id, self.TYPE_VIDEO
            else:
                self.link_action=self.DI_ACTION_PLAYABLE
                return "plugin://plugin.video.youtube/play/?video_id=" + self.video_id, self.TYPE_VIDEO
        else:
            log("    %s cannot get videoID %s" %( self.__class__.__name__, media_url) )
            self.link_action='playYTDLVideo'
            return media_url, self.TYPE_VIDEO

        
    def get_video_id(self):
        match = re.compile('(?:youtube(?:-nocookie)?\.com/(?:\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&;]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})', re.DOTALL).findall(self.media_url)
        if match:
            self.video_id=match[0]

    def get_thumb_url(self, quality0123=1):
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

        if not self.video_id:
            self.get_video_id()

        if self.video_id:            
            self.thumb_url='http://img.youtube.com/vi/%s/%d.jpg' %(self.video_id,quality0123)
            self.poster_url='http://img.youtube.com/vi/%s/%d.jpg' %(self.video_id,0)
   
        return self.thumb_url
    
class ClassImgur(sitesBase):
    regex='(imgur.com)' 

    #use this header for interacting with the imgur api
    #get client id by registering at https://api.imgur.com/oauth2/addclient
    #request_header={ "Authorization": "Client-Id a594f39e5d61396" }
    request_header={ "Authorization": "Client-Id 7b82c479230b85f" }
    
    #when is_an_album() is called to check a /gallery/ link, we ask imgur; it returns more info than needed, we store some of it here   
    is_an_album_type=""
    is_an_album_link=""
    
    def get_album_thumb(self, media_url):

        album_id=self.get_album_or_gallery_id(media_url)
        
        request_url="https://api.imgur.com/3/album/"+album_id 
        #log("    get_album_thumb---"+request_url )
        r = requests.get(request_url, headers=ClassImgur.request_header)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j = r.json()    #j = json.loads(r.text)

            thumb_image_id=j['data'].get('cover')
            
            images_count=j['data'].get('images_count')

            if thumb_image_id:
                #we're not guaranteed that it is jpg but it seems to work with png files as well...
                return 'http://i.imgur.com/'+thumb_image_id+'m.jpg', 'http://i.imgur.com/'+thumb_image_id+'l.jpg'
            
                #for i in j['data']['images']:
                #    if thumb_image_id == i.get('id'):
                #        thumb_image=i.get('link')
                #        thumb_w=i.get('width')
                #        thumb_h=i.get('height')
                
        return "",""

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
        
        log("    ask_imgur_for_link: "+img_id )
        
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

    def get_thumb_url(self, link_url='', thumbnail_type='b'):
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
        if not link_url:
            link_url=self.original_url

        if self.thumb_url:
            return self.thumb_url

        is_album=self.is_an_album(link_url)
        #log('  imgur says is_an_album:%s %s' %( str(is_album), link_url) )
        if is_album:
            #log('      getting album thumb for ' + link_url)
            self.thumb_url, self.poster_url= self.get_album_thumb(link_url)
            return self.thumb_url
        
        from urlparse import urlparse
        o=urlparse(link_url)    #from urlparse import urlparse
        filename,ext=parse_filename_and_ext_from_url(link_url) 
        #log("file&ext------"+filename+"--"+ext+"--"+o.netloc )
        
        #imgur url's sometimes do not have an extension and we don't know if it is an image or video
        if ext=="":
            #log("ret_thumb_url["+ o.path[1:] ) #starts with / use [1:] to skip 1st character
            filename = o.path[1:]
            ext = 'jpg'
        elif ext in ['gif', 'gifv', 'webm', 'mp4']:
            ext = 'jpg'
        
        #return o.scheme+"://"+o.netloc+"/"+filename+ thumbnail_type +"."+ext
        thumb= ("%s://%s/%s%c.%s" % ( o.scheme, o.netloc, filename, thumbnail_type, ext ) ) 
        log('      imgur thumb:' + thumb)

        return thumb

    def get_album_or_gallery_id(self,album_url):
        #you need to have determined that the url is album
        match = re.compile(r'imgur\.com/(?:a|gallery)/(.*)/?', re.DOTALL).findall(album_url)
        if match:
            album_name = match[0]  #album_url.split("/a/",1)[1]
        else:
            log(r"ret_album_list: Can't determine album name from["+album_url+"]" )
            album_name=""
        return album_name        

    def ret_album_list(self, album_url, thumbnail_size_code='b'):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem
        # see ret_thumb_url for thumbnail_size_code values

        #album_url="http://imgur.com/a/fsjam"
        #sometimes album name has "/new" at the end
        
        album_name = self.get_album_or_gallery_id(album_url)

        if album_name=="": 
            log(r"ret_album_list: Can't determine album name from["+album_url+"]" )
            return self.dictList
        
        #log('album name:'+album_name+' from ['+album_url+']')
        request_url="https://api.imgur.com/3/album/"+album_name+"/images"
        #log("listImgurAlbum-request_url---"+request_url )
        r = requests.get(request_url, headers=ClassImgur.request_header)

        images=[]
                
        if r.status_code==200:  #http status code 200 = success
            #log(r.text)
            j = r.json()   #json.loads(r.text)    
            
            #2 types of json received:
            #first, data is an array of objects 
            #second, data has 'images' which is the array of objects
            if 'images' in j['data']:
                imgs=j.get('data').get('images')
            else:
                imgs=j.get('data')
            
            
            for idx, entry in enumerate(imgs):
                type       =entry.get('type')         #image/jpeg
                
                media_url=entry.get('link')          #http://i.imgur.com/gpnMihj.jpg
                width    =entry.get('width')
                height   =entry.get('height')
                title    =entry.get('title')
                descrip  =entry.get('description')
                #combined = self.combine_title_and_description(title, descrip)
                #log("----description is "+description)
                
                #filename,ext=parse_filename_and_ext_from_url(media_url)
                #if description=='' or description==None: description=filename+"."+ext
                
                media_thumb_url=self.get_thumb_url(media_url,thumbnail_size_code)
                
                #log("media_url----"+media_url) 
                #log("media_thumb_url----"+media_thumb_url)
                #log(str(idx)+type+" [" + str(description)+']'+media_url+" "  ) 
                #list_item_name = entry['title'] #if entry['title'] else str(idx).zfill(2)
                
                images.append( {'title': title,
                                'description': descrip, 
                                'url': media_url,
                                'thumb': media_thumb_url,
                                'width': width,
                                'height': height,
                                }  )
            
            #for i in images: log( '##' + repr(i))
            
            self.assemble_images_dictList(images)
        else:
            self.clog(r.status_code ,request_url)

        return self.dictList    
    
        
    def media_id(self, media_url):
        #return the media id from an imbur link
        log("aaa")
        
    def get_playable_url(self, media_url, is_probably_a_video): #is_probably_a_video means put video extension on it if media_url has no ext

        webm_or_mp4='.mp4'  #6/18/2016  using ".webm" has stopped working
        media_url=media_url.split('?')[0] #get rid of the query string?

        is_album=self.is_an_album(media_url)
        #log('  imgur says is_an_album:'+str(is_album))
        if is_album:
            log('    imgur link is an album '+ media_url)
            return media_url, sitesBase.TYPE_ALBUM   
        else:
            if '/gallery/' in media_url: 
                #media_url=media_url.replace("/gallery/","/")
                #is_an_album will ask imgur if a link has '/gallery/' in it and stores it in is_an_album_link
                media_url=self.is_an_album_link
                log('      media_link from /gallery/: '+  media_url )

        filename,ext=parse_filename_and_ext_from_url(media_url) 

        #if is_probably_a_video=='yes': #is_a_video accdg. to the reddit json.
        #log('    ext[%s]' %ext)
        if ext == "":
            #ask imgur for the media link
            media_url=self.ask_imgur_for_link(media_url)
            filename,ext=parse_filename_and_ext_from_url(media_url) 
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
            self.media_type=sitesBase.TYPE_VIDEO
            self.link_action=self.DI_ACTION_PLAYABLE
            
            self.thumb_url=media_url.replace(webm_or_mp4,'.jpg')
            self.poster_url=self.thumb_url            
        elif ext in image_exts:    #image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp']
            self.thumb_url=media_url
            self.poster_url=self.thumb_url
            
            self.media_type=sitesBase.TYPE_IMAGE
            #self.link_action=viewImagew'
        else:
            self.media_type=sitesBase.TYPE_VIDEO
            self.link_action=self.DI_ACTION_PLAYABLE
            
        #log("    media url return=["+media_url+'] vid:' + str(is_video ))
        self.media_url=media_url
        return self.media_url, self.media_type

class ClassVidme(sitesBase):
    regex='(vid.me)' 
    #request_header={ "Authorization": "Basic " + base64_encode($key . ':') }
    request_header={ "Authorization": "Basic aneKgeMUCpXv6FdJt8YGRznHk4VeY6Ps:" }
    media_status=""
    
    def get_playable_url(self,media_url, is_probably_a_video=True):
        #https://docs.vid.me/#api-Video-DetailByURL
        #request_url="https://api.vid.me/videoByUrl/"+videoID
        request_url="https://api.vid.me/videoByUrl?url="+ urllib.quote_plus( media_url )
        #log("vidme request_url---"+request_url )
        r = requests.get(request_url, headers=ClassVidme.request_header)
        #log(r.text)

        if r.status_code != 200:   #http status code 200 is success
            log("    vidme request failed, trying alternate method: "+ str(r.text))
            
            #try to get media id from link.
            #media_url='https://vid.me/Wo3S/skeletrump-greatest-insults'
            #media_url='https://vid.me/Wo3S'
            id=re.findall( 'vid\.me/(.+?)(?:/|$)', media_url )   #***** regex capture to end-of-string or delimiter. didn't work while testing on https://regex101.com/#python but will capture fine 
            
            request_url="https://api.vid.me/videoByUrl/" + id[0]
            r = requests.get(request_url, headers=ClassVidme.request_header)
            #log(r.text)
            if r.status_code != 200:
                log("    vidme request still failed:"+ str(r.text) )
                #t= r.json()
                #self.media_status=t['error']
                return '', '' #sitesBase.TYPE_ALBUM  #i got a 404 on one item that turns out to be an album when checked in browser. i'll just return true

        j = r.json()    #j = json.loads(r.text)

        #for attribute, value in j.iteritems():
        #    log(  str(attribute) + '==' + str(value))
        status = j['video'].get( 'state' )
        
        log( "    vidme video state: " + status ) #success / suspended / deleted
        self.media_status=status
        self.link_action=self.DI_ACTION_PLAYABLE
        return ( j['video']['complete_url'] ), sitesBase.TYPE_VIDEO

    def whats_wrong(self):
        return str( self.media_status )

class ClassVine(sitesBase):
    regex='(vine.co)' 
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
        
        #media_url='"image": "https://v.cdn.vine.co/r/videos/38B4A9174D1177703702723739648_37968e655a0.1.5.1461921223578533188.mp4.jpg?versionId=hv6zBo4kGHPH8NdQeJVo_JRGSVXV73Cc"'
        #msp=re.compile('videos\/(.*?\.mp4)')
        msp=re.compile('(https?://.*/videos/.*?\.mp4)') 
        match=msp.findall(media_url)
        if match:
            #the media_url from reddit already leads to the actual stream, no need to ask vine
            log('    the media_url from reddit already leads to the actual stream [%s]' %match[0])
            return media_url, sitesBase.TYPE_VIDEO   #return 'https://v.cdn.vine.co/r/videos/'+match[0]
    
        #request_url="https://vine.co/oembed.json?url="+media_url   won't work. some streams can't be easily "got" by removing the .jpg at the end 
        request_url=media_url
        #log("    %s get_playable_url request_url--%s" %( self.__class__.__name__, request_url) )
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

            self.link_action=self.DI_ACTION_PLAYABLE
            return contentUrl, sitesBase.TYPE_VIDEO
            
            #log('vine type %s thumbnail_url[%s]' %(type, thumbnail_url) )
        return '',''

class ClassVimeo(sitesBase):      
    regex='(vimeo.com/)'      
    video_id=''
    
    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url
            
        self.get_video_id()
        
        if self.video_id:
            #if use_ytdl_for_yt:  #ytdl can also handle vimeo
            #    self.link_action=sitesBase.DI_ACTION_YTDL
            #    return media_url, self.TYPE_VIDEO
            #else:
            self.link_action=self.DI_ACTION_PLAYABLE
            return "plugin://plugin.video.vimeo/play/?video_id=" + self.video_id, self.TYPE_VIDEO
        else:
            log("    %s cannot get videoID %s" %( self.__class__.__name__, media_url) )
            #feed it to ytdl. sometimes link points to multiple streams: https://vimeo.com/mrmichaelrobinson/videos/ 
            self.link_action=sitesBase.DI_ACTION_YTDL
            return media_url, self.TYPE_VIDEO
        
        
    def get_video_id(self):
#         match = re.compile('vimeo.com/(.*)', re.DOTALL).findall(self.media_url)
#         if match:
#             log('      simple regex got:' + repr(match) )
#             self.video_id=match[0]
        match = re.compile('vimeo.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|album\/(?:\d+)\/video\/|)(\d+)(?:$|\/|\?)', re.DOTALL).findall(self.media_url)
        if match:
            #log('      long regex got:' + repr(match) )
            self.video_id=match[0]
        

    def get_thumb_url(self, quality0123=1):
        #http://stackoverflow.com/questions/1361149/get-img-thumbnails-from-vimeo
        if not self.video_id:
            self.get_video_id(self)
        
        request_url='http://vimeo.com/api/v2/video/%s.json' % self.video_id
        #log(request_url)
        r = requests.get(request_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j=r.json()
            self.poster_url=j[0].get('thumbnail_large')
            self.thumb_url=self.poster_url
            #log( "   ***** thumbnail " + self.poster_url)
   
        return self.thumb_url

class ClassGiphy(sitesBase):
    regex='(giphy.com)'
    #If your app is a form of a bot (ie. hubot), for internal purposes, open source, or for a class project, 
    #  we highly recommend you institute the beta key for your app. 
    #  Unless you're making thousands of requests per IP, you shouldn't have any issues.    
    #The public beta key is "dc6zaTOxFJmzC”
    key='dc6zaTOxFJmzC'
    video_url=''
    video_id=''
    
    def get_playable_url(self, media_url, is_probably_a_video=True ):
        
        if 'media' in media_url:
            if 'giphy.gif' in media_url:
                self.media_url=media_url.replace('giphy.gif','giphy-loop.mp4')
            
                self.link_action=sitesBase.DI_ACTION_PLAYABLE
                log('    simple replace ' + self.media_url )
                return self.media_url, sitesBase.TYPE_VIDEO   
        
        if self.get_media_info():
            self.link_action=sitesBase.DI_ACTION_PLAYABLE
            return self.video_url, sitesBase.TYPE_VIDEO
        
        return '',''

    def get_media_info(self):
        if not self.video_id:
            self.get_video_id()
            log("      giphy id:" + self.video_id)
        
        if self.video_id:
            request_url="http://api.giphy.com/v1/gifs/%s?api_key=%s" %( self.video_id, self.key )
            #log('    Giphy request:'+ request_url)
            content = requests.get(request_url )
            if content.status_code==200:
                j = content.json()
                #d=j.get('data')
                images=j.get('data').get('images')
                #log( pprint.pformat(images, indent=1) )

                #log('      vid=%s' %  images.get('original').get('mp4')  )
                #log('     loop=%s' %  images.get('looping').get('mp4')  )
                
                original=images.get('original')
                self.media_w=original.get('width')
                self.media_h=original.get('height')
                original_video=original.get('mp4')
                looping_video=images.get('looping').get('mp4')
                
                self.thumb_url=images.get('fixed_height_still').get('url')
                self.poster_url=images.get('original_still').get('url')
                
                if looping_video:
                    self.video_url=looping_video
                else:
                    self.video_url=original_video

                return True
            else:
                log("  giphy query failed:" + str(content.status_code) )
        else:
            log("cannot get giphy id")
            
        return False

    def get_video_id(self):
        self.video_id=''
        match = re.compile('giphy\.com/media/([^ /]+)/|i\.giphy\.com/([^ /]+)\.gif|giphy\.com/gifs/(?:.*-)?([^ /?]+)').findall(self.media_url)
        #log('    matches' + repr(match) )
        for m in match[0]:
            if m: 
                self.video_id=m
                return

    def get_thumb_url(self, quality0123=1):
        #calling get_playable_url sometimes results in querying giphy.com. if we do, we also save the thumbnail info.
        if self.thumb_url:
            return self.thumb_url
        else:
            self.get_media_info()            
   
        return self.thumb_url
                
class ClassDailymotion(sitesBase):
    regex='(dailymotion.com)'
    
    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url
        
        # *** needs access token to get playable url. we'll just have ytdl handle dailymotion
        self.link_action=sitesBase.DI_ACTION_YTDL
        return media_url, self.TYPE_VIDEO
    
#         self.get_video_id()
#         #log('    videoID:' + self.video_id)
#         if self.video_id:
#             request_url= 'https://api.dailymotion.com/video/' + self.video_id
#             
#             #https://api.dailymotion.com/video/x4qviso?fields=aspect_ratio,stream_h264_hd_url,poster_url,thumbnail_url,sprite_320x_url
#             
#             content = requests.get(request_url )
#             log('    ' + str(content.text))
#             if content.status_code==200:
#                 j = content.json()
#                 log( pprint.pformat(j, indent=1) )
#             else:
#                 log("  dailymotion query failed:" + str(content.status_code) )
#         else:
#             log("    %s cannot get videoID %s" %( self.__class__.__name__, media_url) )
    
    
    def get_video_id(self):
        match = re.compile('.+dailymotion.com\/(?:video\/([^_]+))?[^#]*(?:#video=([^_&]+))?', re.DOTALL).findall(self.media_url)
        #log('    match:'+ repr(match) )
        for m in match[0]:
            if m: 
                self.video_id=m
                return

    def get_thumb_url(self, quality0123=1):
        #http://stackoverflow.com/questions/13173641/how-to-get-the-video-thumbnail-from-dailymotion-video-from-the-video-id-of-that
        #Video URL: http://www.dailymotion.com/video/`video_id`
        #Thumb URL: http://www.dailymotion.com/thumbnail/video/video_id
        #
        #OR
        #https://api.dailymotion.com/video/VIDEO_ID?fields=field1,field2,...
        #Replace field1,field2 with
        #thumbnail_large_url (320px by 240px)
        #thumbnail_medium_url (160px by 120px)
        #thumbnail_small_url (80px by 60px)
        return self.media_url.replace('/video/','/thumbnail/video/')

class ClassLiveleak(sitesBase):
    regex='(liveleak.com)'
    # *** liveleak handled by ytdl
    
    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        self.link_action=sitesBase.DI_ACTION_YTDL
        return self.media_url, self.TYPE_VIDEO
    
    def get_thumb_url(self, quality0123=1):
        log('    getting liveleak thumbnail ')
        if not self.thumb_url:
            img=self.request_meta_ogimage_content()
            self.thumb_url=img
            self.poster_url=self.thumb_url

        log('      ll thumb:' + self.thumb_url )                        
        return self.thumb_url
    
class ClassStreamable(sitesBase):
    regex='(streamable.com)' 
    video_id=''
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
        #check if provided url links directly to the stream
        #https://streamable.com/dw9f 
        #   becomes --> https://streamable.com/video/mp4/dw9f.mp4  or  https://streamable.com/video/webm/dw9f.webm
        #   thumbnail -->     //cdn.streamable.com/image/dw9f.jpg 
        #this is the streamable api https://api.streamable.com/videos/dw9f

        self.get_video_id()
        #log('    ' + self.video_id)
        url_mp4=""
        url_mp4m=""
        url_webm=""
        url_webmm=""
        
        if self.video_id:
            api_url='https://api.streamable.com/videos/%s' %self.video_id
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
                    
                    self.link_action=sitesBase.DI_ACTION_PLAYABLE
                    if streamable_quality=='full' :
                        return "https:" + url_hq, sitesBase.TYPE_VIDEO
                    else:
                        return "https:" + url_mq, sitesBase.TYPE_VIDEO
        else:
            log('      %s: cant get video id '  %(self.__class__.__name__ ) )

    def get_video_id(self):
        self.video_id=''
        match = re.compile('streamable\.com\/video/(?:.+)/([^_]+)\.(?:mp4|webm)|streamable\.com\/(.*)(?:\?|$)').findall(self.media_url)
        #log('    matches' + repr(match) )
        for m in match[0]:
            if m: 
                self.video_id=m
                return
        #if match: self.video_id=match[0]

    def get_thumb_url(self, image_url="", thumbnail_type='b'):
        log('    getting thumbnail [%s] %s' %(self.video_id, self.media_url ) )
        if not self.video_id:
            self.get_video_id()

        self.thumb_url="https://cdn.streamable.com/image/%s.jpg" %self.video_id
        self.poster_url=self.thumb_url
                    
        return self.thumb_url

class ClassTumblr(sitesBase):
    regex='(tumblr.com)'
    
    api_key='no0FySaKYuQHKl0EBQnAiHxX7W0HY4gKvlmUroLS2pCVSevIVy'
    include_gif_in_get_playable=True
    
    def get_thumb_url(self, image_url="", thumbnail_type='b'):
        #call this after calling get_playable_url
        return self.thumb_url

    def get_playable_url(self, media_url, is_probably_a_video=True ):
        #log('class tumblr prep media url')

        # don't check for media.tumblr.com because
        #there are instances where media_url is "https://vt.tumblr.com/tumblr_o1jl6p5V5N1qjuffn_480.mp4#_=_"
#         filename,ext=parse_filename_and_ext_from_url(media_url)
# 
#         if 'media.tumblr.com' in media_url:
#             if ext in image_exts:
#                 return media_url, sitesBase.TYPE_IMAGE
#             elif ext in ["mp4","gif"]:
#                 return media_url,sitesBase.TYPE_VIDEO
            
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
        #log(api_url)
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
                    image=post['photos'][0]['original_size']['url'] 
                    #log('media url: ' + post['photos'][0]['original_size']['url']  )
                    
                    self.poster_url=image
                    return image, sitesBase.TYPE_IMAGE
                
                else:
#                     dictList=[]
#                     for i, photo in enumerate( post['photos'] ):
#                         #log("%d %s" %(i, photo['original_size']['url'] ))
#                         #p.append(photo['original_size']['url'])
#     
#                         infoLabels={ "Title": photo['caption'], "plot": photo['caption'], "PictureDesc": '', "exif:exifcomment": '' }
#                         e=[ photo['caption'] if photo['caption'] else str(i+1) #'li_label'           #  the text that will show for the list  (list label will be the caption or number if caption is blank)
#                            ,''                                                 #'li_label2'          #  
#                            ,""                                                 #'li_iconImage'       #
#                            ,photo['alt_sizes'][3]['url']                       #'li_thumbnailImage'  #
#                            ,photo['original_size']['url']                      #'DirectoryItem_url'  #  
#                            ,False                                              #'is_folder'          # 
#                            ,'pictures'                                         #'type'               # video pictures  liz.setInfo(type='pictures',
#                            ,True                                               #'isPlayable'         # key:value       liz.setProperty('IsPlayable', 'true')  #there are other properties but we only use this 
#                            ,infoLabels                                         #'infoLabels'         # {"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin
#                            ,'none'                                             #'context_menu'       # ...
#                               ]
#                     
#                         dictList.append(dict(zip(keys, e)))
                    return self.media_url, sitesBase.TYPE_ALBUM
                
            elif media_type == 'video':
                self.thumb_url=post['thumbnail_url']
                return post['video_url'], sitesBase.TYPE_VIDEO
            elif media_type == 'audio':
                return post['audio_url'], media_type
                    
        return "", media_type

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem

        if "www.tumblr.com" in album_url:   #warning:nsfw!!  https://www.tumblr.com/video/johncena2014/144096330849/500/  
            match = re.findall('https?://www.tumblr.com/(?:post|image|video)/(.+?)/(.+?)(?:/|$)',album_url)
        else:
            match = re.findall('https?://(.*)\.tumblr.com/(?:post|image|video)/(.+?)(?:/|$)',album_url)

        blog_identifier = match[0][0]
        post_id         = match[0][1]

        api_url='http://api.tumblr.com/v2/blog/%s/posts?api_key=%s&id=%s' %(blog_identifier,self.api_key,post_id )
        #needs to look like this:   #see documentation  https://www.tumblr.com/docs/en/api/v2
        #url='http://api.tumblr.com/v2/blog/boo-rad13y/posts?api_key=no0FySaKYuQHKl0EBQnAiHxX7W0HY4gKvlmUroLS2pCVSevIVy&id=146015264096'
        #log('apiurl:'+api_url)
        #log(api_url)
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
                
                list=(        [ photo.get('caption'), photo.get('original_size').get('url'), photo['alt_sizes'][3]['url'] ]  for photo in post['photos']   )
                
                self.assemble_images_dictList( list )

            else:
                log('      %s wrong media type: %s '  %(self.__class__.__name__ ), media_type )
        else:
            log('    %s :ret_album_list: %s ' %(self.__class__.__name__, repr(r.status_code) ) )


        #log( pprint.pformat(self.dictList, indent=1) )            
        return self.dictList    

class ClassBlogspot(sitesBase):
    regex='(blogspot.com)'
    include_gif_in_get_playable=True
    
    #go here:  https://console.developers.google.com/apis/credentials?project=_
    #  Create Credentials -> API Key -> Browser Key
    #  test: https://www.googleapis.com/blogger/v3/blogs/2399953?key=YOUR-API-KEY
    #     FAIL. go to. https://console.developers.google.com/apis/api/blogger/overview?project=script-reddit-reader
    #       click on "Enable" on top center area
    #  test: https://www.googleapis.com/blogger/v2/blogs/2399953&key=AIzaSyCcKuHRAYT1qreLx_Z3zwks9ODuEauJmUU
    #     will work
    
    key_string='key=AIzaSyCcKuHRAYT1qreLx_Z3zwks9ODuEauJmUU'
    
    #first retrieve the blog id by url
    #https://www.googleapis.com/blogger/v3/blogs/byurl
    #    ?key=AIzaSyCcKuHRAYT1qreLx_Z3zwks9ODuEauJmUU
    #    &url=http://zishygallery.blogspot.fr/2016/08/heaven-starr-bearded-ladies-49-images.html?zx=4b8a257abc62bfe7
    
    #then get the blog post by the url path 
    #https://www.googleapis.com/blogger/v3/blogs/4969494452935498564/posts/bypath?key=AIzaSyCcKuHRAYT1qreLx_Z3zwks9ODuEauJmUU&path=/2016/08/heaven-starr-bearded-ladies-49-images.html
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
        #match = re.compile('^https?://.*\.blog(?:spot|ger)\..*?/(.*)?$', re.DOTALL).findall(media_url)

        #content = requests.get( blog_post_request )
        content = self.ret_blog_post_request()
        if content:
            j = content.json()
            #log( pprint.pformat(j, indent=1) )
            #author_image=j.get('author').get('image').get('url')
            #log('    author image:' + author_image)
                        
            html=j.get('content')  
            #could have just ran parseDOM the original media_url...
            
#            all_images=[]
#             fns=[parseDOM(html, 'img', ret="src"),parseDOM(html, 'a', ret="href") ]
#             
#             log( 'zzzzzz' + repr( [ f() for f in fns])  )
#             all_images.append(  f() for f in fns )
# 
#             for i in all_images:
#                 log('      all i:' + i )
            
#             for images=f() in fns:

#                 if images:
#                     for i in images:
#                         log('      images:'+ repr(i))
            #https://www.reddit.com/r/learnpython/comments/50ciod/calling_functions_in_a_list/
                                
                
                
             
            images=parseDOM(html, name='img', ret="src")
            #log('      1st parse dom: %d %s' %(len(images), repr(images))  )
            if images:
                #for i in images:
                #    log('      images:'+ repr(i))
                self.thumb_url=images[0]
                self.poster_url=self.thumb_url
                      
                if len(images) == 1:
                    return images[0], self.TYPE_IMAGE
                else:
                    return media_url, self.TYPE_ALBUM
                    
              
              
            images=parseDOM(html, name='a', ret="href")
            #log('      2nd parse dom: %d %s' %(len(images), repr(images))  )
            if images:
                #for i in images:
                #    log('      images:'+ repr(i))
                log('        check[0] if playable:' + images[0])
                if link_url_is_playable(images[0]) == 'image':
                    log('        [0] is playable')
                    self.thumb_url=images[0]
                    self.poster_url=self.thumb_url
                          
                    if len(images) == 1:
                        return images[0], self.TYPE_IMAGE
                    else:
                        return media_url, self.TYPE_ALBUM
            
        else:
            log('    error: %s ret_blog_post_request failed' %(self.__class__.__name__  ) )
        
        return '',''

    def ret_blog_post_request(self):
        
        from urlparse import urlparse
        o=urlparse(self.media_url)   #scheme, netloc, path, params, query, fragment
        #log( '  blogpath=' + o.path )
        blog_path= o.path
        
        if not blog_path:
            log('    could not determine blog path in:' + self.media_url)
            return None
            
        
        blog_info_request='https://www.googleapis.com/blogger/v3/blogs/byurl?' + self.key_string + '&url=' + self.media_url
        content = requests.get( blog_info_request )
        
        if content.status_code==200:
            j = content.json()
            #log( pprint.pformat(j, indent=1) )
            blog_id=j.get('id')  
        else:
            log('    error: %s getting blog id : %s %s' %(self.__class__.__name__, repr( content.status_code ), blog_info_request ) )
            return None

        blog_post_request='https://www.googleapis.com/blogger/v3/blogs/%s/posts/bypath?%s&path=%s' %( blog_id, self.key_string, blog_path)
        #log( '    api request:'+blog_post_request )
        content = requests.get( blog_post_request )
        if content.status_code==200:
            return content
        else:
            log('    error: %s blogs/posts/bypath: %s ' %(self.__class__.__name__, repr( content.status_code ) ) )
            return None


    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        content = self.ret_blog_post_request()
        if content:
            j = content.json()    #log( pprint.pformat(j, indent=1) )
            html=j.get('content')  

            all_images=[]
            
#             images=parseDOM(html, name='img', ret="src")
#             if images:
#                 for i in images:
#                     all_images.append(i)
#                     #log('      images:'+ repr(i))
#                       
#             images=parseDOM(html, name='a', ret="href")
#             if images:
#                 for i in images:
#                     all_images.append(i)
#                     #log('      images:'+ repr(i))

            #https://www.reddit.com/r/learnpython/comments/50ciod/calling_functions_in_a_list/

            #doesn't work
            #params=[('img','src'),('a', 'href')]
            #all_images = [parseDOM(html, name, ret=ret) for name,ret in params]
            
            names = ['img', 'a']
            rets = ['src','href']
            all_images = []
            
            for name, ret in zip(names, rets):
                images = parseDOM(html, name = name, ret = ret)
                #log here if you'd like
                if images:
                    all_images.extend(images)            

            #for i in all_images: log('  all_images:' + i  )
            
            list1=remove_duplicates(all_images)
            list2 =[]
            #for i in list1: log('  checking links in list1:' + i)
            for i in list1:
                #if 'blogspot' in i: continue
                if link_url_is_playable(i) == 'image':
                    list2.append(i)
            #for i in list2: log('  checking links in list2:' + i)
            
            #if len(all_images) > 1:
            self.assemble_images_dictList(  list2    )

            return self.dictList
        else:
            log('    content blank ')

class ClassInstagram(sitesBase):
    regex='(instagram.com)'
    
    def get_playable_url(self, media_url, is_probably_a_video=True):
        #the instagram api has limits and that would not work for this purpose
        #  scrape the instagram post instead.

        r = requests.get(media_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            #grab the json-like object
            jo=re.compile('window._sharedData = ({.*});</script>').findall(r.text)
            if jo:
                
                #log( pprint.pformat(jo[0], indent=1) )
                try:
                    j=json.loads(jo[0] )
                    #log(str(j))
                    if j.get('entry_data'):
                        post_pages=j.get('entry_data').get('PostPage')
                        #log('    post_pages %d' %len(post_pages) )
                        
                        post_page=post_pages[0]
                        media=post_page.get('media')
                        #log(str(j['entry_data']['PostPage'][0]['media']['display_src']))
                        display_src=media.get('display_src')
                        is_video=media.get('is_video')
                        self.media_w=media.get('dimensions').get('width')
                        self.media_h=media.get('dimensions').get('height')
                        
                        self.thumb_url=display_src
                        self.poster_url=self.thumb_url
                        
                        #log('      vid=%s %dx%d %s' %(is_video,self.media_w,self.media_h,display_src)  )
                        if is_video:
                            self.media_url=media.get('video_url')
                            self.link_action=sitesBase.DI_ACTION_PLAYABLE
                            return self.media_url, sitesBase.TYPE_VIDEO
                        else:
                            return display_src, sitesBase.TYPE_IMAGE
                    else:
                        log("  Could not get 'entry_data' from scraping instagram [window._sharedData = ]")
                    
                except:
                    log('    exception while parsing json')
                    return '',''
        else:
            log('    error: %s :%s' %(self.__class__.__name__, repr( r.status_code ) ) ) 
        
        return '', ''

    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url
        pass

class ClassGyazo(sitesBase):
    regex='(gyazo.com)'
    
    def get_playable_url(self, media_url, is_probably_a_video=True):

        #media_url='http://gyazo.com/b8c993ab1435171eafefb882d8e2d17a'
        api_url='https://api.gyazo.com/api/oembed?url=%s' %(media_url )
        
        r = requests.get(api_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j=json.loads(r.text.replace('\\"', '\''))
            
            media_type=j.get('type')
            self.media_w=j.get('width')
            self.media_h=j.get('height')
            media_url=j.get('url')
            
            log('      gyazo=%s %dx%d %s' %(media_type, self.media_w,self.media_h, j.get('url'))  )
            
            if link_url_is_playable(media_url)=='video': #catch .gif
                media_type='video'

            if media_type=='photo':
                self.thumb_url=media_url
                self.poster_url=self.thumb_url
                
                self.media_type=sitesBase.TYPE_IMAGE
                self.media_url=media_url
            elif media_type=='video':
                self.link_action=sitesBase.DI_ACTION_PLAYABLE
                self.media_type=sitesBase.TYPE_VIDEO
                self.media_url=media_url
                
            return self.media_url,self.media_type    
        else:
            log('    error: %s :%s' %(self.__class__.__name__, repr( r.status_code ) ) )
                                
        return '',''
    
    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url
        pass
 
class ClassFlickr(sitesBase):
    regex='(flickr\.com|flic\.kr)'
    
    api_key='a3662f98e08266dca430404d37d8dc95'
    thumb_url=""
    poster_url=""
    
    fTYPE_ALBUM='album'
    fTYPE_PHOTO='photo'
    fTYPE_GROUP='group'
    fTYPE_VIDEO='video'
    fTYPE_GALLERY='gallery'
    fmedia_type=''
    
    def get_thumb_url(self, image_url="", thumbnail_type='b'):
        #call this after calling get_playable_url
        return self.thumb_url
    
    def get_photo_id_flic_kr(self, url):
        #Flickr provides a URL shortening service for uploaded photos (and videos). Short URLs can be useful in a variety of contexts including: email, on business cards, IM, text messages, or short status updates.
        #Every photo on Flickr has a mathematically calculated short URL of the form:
        #   https://flic.kr/p/{base58-photo-id}
        #Base58 is used to compress the photo-ids using a mix of letters and numbers. You can find more info on base58, and code samples in the Flickr API Group.
        
        #after some testing, found that the flickr api accepts the undecoded photo id.
        #after some more testing, undecoded photo id for photos only. for photosets(album), it has to be decoded
        
        #flic\.kr\/(?:.+\/)?(.+)|flickr\.com\/photos\/|flic\.kr\/(?:.+\/)?(\d+)
        #match = re.findall('flic\.kr\/(?:.+\/)?(.+)',url)
        #photo_id=match[0]
        
        from base58 import decode        
        b58e_id=url.split('/')[-1] #https://flic.kr/p/KSt6Hh   https://flic.kr/s/aHskGjN56V

        a = decode(b58e_id)
        sa= str(a)
        #this site is helpful to test decoding:
        #  https://www.darklaunch.com/tools/base58-encoder-decoder
        
        if self.media_type==self.fTYPE_GROUP:
            # https://flic.kr/g/stemc  ==>  https://www.flickr.com/groups/2995418@N23/
            #log( " group id was %s" %a )
            #log( " group id now %s" %( a[0:-2] + '@N' + a[-2:] ) )  #[ begin : end : step ]
            sa =( sa[0:-2] + '@N' + sa[-2:] )

        if self.media_type==self.fTYPE_GALLERY:
            #note: this was done through trial and error. the short code did not decode to the correct galleryID. 
            # https://flic.kr/y/2sfUimC  ==>  https://www.flickr.com/photos/flickr/galleries/72157671483451751/
            a = a + 72157616180848087
            sa=str(a)
        
        log( '    decoding flickrID:' + b58e_id + ' => ' + sa )      
        return sa

    def get_video_id(self):
        #this method cannot determine ID from flikr group like  https://www.flickr.com/groups/flickrfriday/   (https://flic.kr/g/ju9j6)
        #  flickrfriday is the friendly name for the group. you need to use the flickr api to get groupID
        #  https://www.flickr.com/services/api/flickr.urls.lookupGroup.html
        #  
        #  not doing that right now. 
        #use shortened url. it worked for groups

        self.video_id=''
        if 'flic.kr' in self.media_url:
            photo_id=self.get_photo_id_flic_kr(self.media_url)
        else:
            #get the photoID 
            #match = re.findall('flickr\.com\/photos\/(?:.+\/)?(\d+)',media_url)
            if self.is_an_album(self.media_url):
                match = re.findall('flickr\.com/photos/(?:.+)?(?:/sets/|/albums/|/s/|/groups/|/g/|galleries|/y/)(\d+)|flickr\.com/photo\.gne\?short=(.+)',self.media_url)  
            else:
                match = re.findall('flickr\.com\/photos\/(?:.+\/)?(\d+)|flickr\.com/photo\.gne\?short=(.+)',self.media_url)  #sometimes url comes like this: https://www.flickr.com/photo.gne?short=LHmhpR
            
            for m in match[0]:
                if m: 
                    photo_id=m
            
        self.video_id=photo_id
    
    def get_playable_url(self, media_url, is_probably_a_video=True ):
        
        if self.is_an_album(media_url):
            return media_url, sitesBase.TYPE_ALBUM
        
        self.fmedia_type="photo"
        ret_url=""
        photo_id=0
        
        #figure out the media type; this determines how we extract the ID and api call to use
        self.fmedia_type=self.flickr_link_type(media_url)
        log( '    media_type='+ self.fmedia_type + "  from:" + media_url)

        self.get_video_id()
        photo_id=self.video_id

        if self.fmedia_type==self.fTYPE_ALBUM:  
            #log('  is a flickr album (photoset)')
            api_method='flickr.photosets.getPhotos'
            api_arg='photoset_id=%s' %photo_id
        elif self.fmedia_type==self.fTYPE_PHOTO:
            api_method='flickr.photos.getSizes'
            api_arg='photo_id=%s' %photo_id
        elif self.fmedia_type==self.fTYPE_GROUP:
            api_method='flickr.groups.pools.getPhotos'
            api_arg='group_id=%s' %photo_id
        elif self.fmedia_type==self.fTYPE_GALLERY:
            api_method='flickr.galleries.getPhotos'
            api_arg='gallery_id=%s' %photo_id
            
            
        api_url='https://api.flickr.com/services/rest/?format=json&nojsoncallback=1&api_key=%s&method=%s&%s' %(self.api_key,api_method,api_arg )

        #log('  flickr apiurl:'+api_url)
        r = requests.get(api_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j=json.loads(r.text.replace('\\"', '\''))
            
            status=j.get('stat')
            if status=='fail':
                message=j.get('message')
                raise Exception(message)
            
            if self.fmedia_type in [self.fTYPE_ALBUM, self.fTYPE_GROUP, self.fTYPE_GALLERY ]:   #for  #photosets, galleries, pools? panda?
                self.media_type=sitesBase.TYPE_ALBUM
                
                if self.fmedia_type==self.fTYPE_ALBUM:
                    photos=j['photoset']['photo']
                    owner=j.get('photoset').get('ownername')
                else:
                    #elif self.media_type in [self.fTYPE_GROUP, self.fTYPE_GALLERY]:
                    photos=j['photos']['photo']
                    
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
                    ownerstring=''
                    if self.fmedia_type in [self.fTYPE_GROUP, self.fTYPE_GALLERY]:
                        owner=p.get('ownername')
                        if owner:
                            ownerstring ='by %s'%(owner)
                    
                    photo_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'b' )
                    thumb_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'n' )
                    poster_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'z' )
                    #log(" %d  %s" %(i,photo_url ))
                    #log(" %d  %s" %(i,thumb_url ))

                    infoLabels={ "Title": p['title'], "plot": ownerstring , "director": p.get('ownername'), "exif:exifcomment": '',  }
                    
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
                    
                    #use first image as thumbnail and poster
                    if i==0:
                        self.thumb_url=thumb_url
                        self.poster_url=poster_url
                
                return dictList
                
            elif self.fmedia_type==self.fTYPE_PHOTO:
            
                sizes=j['sizes']
                #log('    sizes' + str(sizes))
                #Square, Large Square, Thumbnail, Small, Small 320, Medium, Medium 640, Medium 800, Large, Large 1600, Large 2048, Original
                for s in sizes['size']:
                    #log('    images size %s url=%s' %( s['label'], s['source']  ) )
                    if s['label'] == 'Medium 640':    
                        self.poster_url=s['source']

                    #if s['label'] == 'Medium 800': 
                    #    self.poster_url=s['source']

                    if s['label'] == 'Thumbnail':    
                        self.thumb_url=s['source']

                    if s['label'] == 'Small':    
                        self.thumb_url=s['source']

                    #sometimes large is not available we just brute force the list starting from lowest that we'll take
                    if s['label'] == 'Medium':    
                        ret_url=s['source']
                        #media_type=s['media']   #'photo'

                    if s['label'] == 'Medium 640':    
                        ret_url=s['source']
                        #media_type=s['media']   #'photo'

                    if s['label'] == 'Medium 800':    
                        ret_url=s['source']
                        #media_type=s['media']   #'photo'

                    if s['label'] == 'Large':    
                        ret_url=s['source']
                        #media_type=s['media']

                    if s['label'] == 'Large 1600':    
                        ret_url=s['source']
                        #media_type=s['media']
                    
            return ret_url, self.TYPE_IMAGE
        else:
            log('    error: %s :%s' %(self.__class__.__name__, repr( r.status_code ) ) )
        
        return '',''

    def is_an_album(self,media_url):
        #returns true if link is a bunch of images
        a=['/sets/','/albums/','/s/','/groups/','/g/','/galleries/','/y/']
        if any(x in media_url for x in a): 
            return True
        return False

    def flickr_link_type(self,media_url):
        a=['/sets/','/albums/','/s/']
        g=['/groups/','/g/']
        y=['/galleries/','/y/']
        if any(x in media_url for x in a): 
            return self.fTYPE_ALBUM

        if any(x in media_url for x in g): 
            return self.fTYPE_GROUP
        
        if any(x in media_url for x in y): 
            return self.fTYPE_GALLERY

        #p=['/photo/','/p/']
        return self.fTYPE_PHOTO

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        
        if not self.is_an_album(album_url):
            log('  flickr link is not an album' + album_url)
            return ''
        
        self.fmedia_type="photo"
        ret_url=""
        photo_id=0
        
        #figure out the media type; this determines how we extract the ID and api call to use
        self.fmedia_type=self.flickr_link_type(album_url)
        log( '    media_type='+ self.fmedia_type + "  from:" + album_url)

        self.get_video_id()
        photo_id=self.video_id

        if self.fmedia_type==self.fTYPE_ALBUM:  
            #log('  is a flickr album (photoset)')
            api_method='flickr.photosets.getPhotos'
            api_arg='photoset_id=%s' %photo_id
        elif self.fmedia_type==self.fTYPE_PHOTO:
            api_method='flickr.photos.getSizes'
            api_arg='photo_id=%s' %photo_id
        elif self.fmedia_type==self.fTYPE_GROUP:
            api_method='flickr.groups.pools.getPhotos'
            api_arg='group_id=%s' %photo_id
        elif self.fmedia_type==self.fTYPE_GALLERY:
            api_method='flickr.galleries.getPhotos'
            api_arg='gallery_id=%s' %photo_id
            
        api_url='https://api.flickr.com/services/rest/?format=json&nojsoncallback=1&api_key=%s&method=%s&%s' %(self.api_key,api_method,api_arg )

        #log('  flickr apiurl:'+api_url)
        r = requests.get(api_url)
        #log(r.text)
        if r.status_code == 200:   #http status code 200 is success
            j=json.loads(r.text.replace('\\"', '\''))
            
            status=j.get('stat')
            if status=='fail':
                message=j.get('message')
                raise Exception(message)
            
            if self.fmedia_type in [self.fTYPE_ALBUM, self.fTYPE_GROUP, self.fTYPE_GALLERY ]:   #for  #photosets, galleries, pools? panda?
                self.media_type=sitesBase.TYPE_ALBUM
                
                if self.fmedia_type==self.fTYPE_ALBUM:
                    photos=j['photoset']['photo']
                    owner=j.get('photoset').get('ownername')
                else:
                    #elif self.media_type in [self.fTYPE_GROUP, self.fTYPE_GALLERY]:
                    photos=j['photos']['photo']
                    
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
                    ownerstring=''
                    if self.fmedia_type in [self.fTYPE_GROUP, self.fTYPE_GALLERY]:
                        owner=p.get('ownername')
                        if owner:
                            ownerstring ='by %s'%(owner)
                    
                    photo_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'b' )
                    thumb_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'n' )
                    poster_url='https://farm%s.staticflickr.com/%s/%s_%s_%c.jpg' %(p['farm'],p['server'],p['id'],p['secret'],'z' )
                    #log(" %d  %s" %(i,photo_url ))
                    #log(" %d  %s" %(i,thumb_url ))

                    infoLabels={ "Title": p['title'], "plot": ownerstring , "director": p.get('ownername'), "exif:exifcomment": '',  }
                    
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
                    
                return dictList
                
            else:
                log('    NOT AN ALBUM: unexpected flickr media type ' + self.fmedia_type )
        else:
            log('    error: %s :%s' %(self.__class__.__name__, repr( r.status_code ) ) )
        
        return ''

class ClassGifsCom(sitesBase):
    regex='(gifs.com)'
    #also vidmero.com
    
    api_key='gifs577da09e94ee1'   #gifs577da0485bf2a'
    headers = { 'Gifs-API-Key': api_key, 'Content-Type': "application/json" }
    #request_url="https://api.gifs.com"   r=requests.get(request_url, headers=ClassGifsCom.headers)

    def get_playable(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url
            
        filename,ext=parse_filename_and_ext_from_url(media_url)
        #log('    file:%s.%s' %(filename,ext)  )
        if ext in ["mp4","webm","gif"]:
            if ext=='gif':
                self.link_action=sitesBase.DI_ACTION_PLAYABLE
                self.thumb_url=media_url.replace( '%s.%s'%(filename,ext) , '%s.jpg' %(filename))
                self.poster_url=self.thumb_url
                self.media_url=media_url.replace( '%s.%s'%(filename,ext) , '%s.mp4' %(filename))   #just replacing gif to mp4 works
            return self.media_url, self.TYPE_VIDEO

        if ext in image_exts:  #excludes .gif
            self.link_action='viewImage'
            self.thumb_url=media_url
            self.poster_url=self.thumb_url
            return media_url,self.TYPE_IMAGE

        return self.get_playable_url(self.media_url, is_probably_a_video=False )

    
    def get_thumb_url(self, image_url="", thumbnail_type='b'):
        #call this after calling get_playable_url
        return self.thumb_url
    
    def get_video_id(self):
        #looks like the filename is also the video id and some links have it at the "-"end od url
        self.video_id=''
        
        #https://j.gifs.com/zpOmn5.gif       <-- this is handled in get_playable -> .gif replaced with .mp4 
        #http://gifs.com/gif/qxBQMp                   <-- parsed here.
        #https://gifs.com/gif/yes-nooo-whaaa-5yZ8rK   <-- parsed here.
        
        match = re.compile('gifs\.com/(?:gif/)?(.+)(?:.gif|$)').findall(self.media_url)
        #log('    matches' + repr(match) )
        
        if match: 
            vid=match[0]
            if '-' in vid:
                vid= vid.split('-')[-1]

            self.video_id=vid
        
    
    def get_playable_url(self, media_url, is_probably_a_video=True ):
        #api method abandoned. doesn't seem to be any way to get media info. just upload and convert

        #can also parse the link...
#               <div class="gif-display">
#                   <video id="video" muted class="gifyt-player gifyt-embed" preload="auto"
#                          poster="https://j.gifs.com/gJoYy9.jpg" loop="" autoplay="">
#                       <source src="https://j.gifs.com/gJoYy9.mp4" type="video/mp4">
#                   </video>
#               </div>        

        
        self.get_video_id()
        log('    gifs.com videoID:' + self.video_id )
        
        self.link_action=sitesBase.DI_ACTION_PLAYABLE
        return 'http://j.gifs.com/%s.mp4' %self.video_id , sitesBase.TYPE_VIDEO

class ClassGfycat(sitesBase):
    regex='(gfycat.com)'

    def get_playable_url(self, media_url, is_probably_a_video=True ):

        self.get_video_id()

        if self.video_id:
            #log('    video id:' + repr(self.video_id) )
            request_url="https://gfycat.com/cajax/get/" + self.video_id
            
            content = requests.get(request_url )
            #content = opener.open("http://gfycat.com/cajax/get/"+id).read()
            #log('gfycat response:'+ content)
            if content.status_code==200:
                content = content.json()
            
                gfyItem=content.get('gfyItem')
                if gfyItem:
                    self.media_w=safe_cast(gfyItem.get('width'),int,0)
                    self.media_h=safe_cast(gfyItem.get('height'),int,0)
                    webmSize=safe_cast(gfyItem.get('webmSize'),int,0)
                    mp4Size =safe_cast(gfyItem.get('mp4Size'),int,0)
                    
                    self.thumb_url =gfyItem.get('posterUrl')  #thumb100PosterUrl
                    self.poster_url=gfyItem.get('posterUrl')

                    #pick the smaller of the streams
                    if mp4Size > webmSize:
                        log('      using webm  wm(%d) m4(%d)' %(webmSize,mp4Size) )
                        stream_url=gfyItem.get('webmUrl') if gfyItem.get('webmUrl') else gfyItem.get('mp4Url')
                    else:
                        log('      using mp4   wm(%d) m4(%d)' %(webmSize,mp4Size) )
                        stream_url=gfyItem.get('mp4Url') if gfyItem.get('mp4Url') else gfyItem.get('webmUrl')
                    
                    log('      %dx%d %s' %(self.media_w,self.media_h,stream_url)  )
                    
                    self.link_action=sitesBase.DI_ACTION_PLAYABLE
                    return stream_url, sitesBase.TYPE_VIDEO
            else:
                log('    error: %s :%s' %(self.__class__.__name__, repr( content.status_code ) ) )         
        else:
            log("cannot get gfycat id")
        
        return '', ''

    def get_video_id(self):
        self.video_id=''
        match = re.findall('gfycat.com/(.*)', self.media_url)
        if match:
            self.video_id=match[0]

    
    def get_thumb_url(self, image_url="", thumbnail_type='b'):
        #call this after calling get_playable_url
        return self.thumb_url
   
class ClassEroshare(sitesBase):
    SITE='eroshare'
    regex='(eroshare.com)'
    
    def get_playable_url(self, link_url, is_probably_a_video=True ):
        
        content = requests.get( link_url )
        #if 'pnnh' in media_url:
        #    log('      retrieved:'+ str(content) )
        
        if content.status_code==200:
            match = re.compile('var album\s=\s(\{.*\});', re.DOTALL).findall(content.text)
            #log('********* ' + match[0])    
            if match:
                j = json.loads(match[0])
                items = j.get('items')
                #log( '      %d item(s)' % len(items) )
                
                self.media_type, playable_url, self.poster_url, self.thumb_url=self.get_media(items[0])
                if len(items) == 1:
                    #item=items[0]
                    #log('      single %s %s' %( self.media_type, playable_url ))
                    #self.media_type=item.get('type')
                    #self.media_type, playable_url, self.poster_url, self.thumb_url=self.get_media(item)
                    if self.media_type==sitesBase.TYPE_VIDEO:
                        self.link_action=sitesBase.DI_ACTION_PLAYABLE
                        
                    return playable_url, self.media_type
                    
                else:
                    #check if all items are video or image
                    media_types = []
                    for item in items:
                        #log('    multiple: %s orig=%s ' %( item.get('type').lower(), item.get('url_orig') ))
                        media_types.append( item.get('type').lower() )
                    
                    if self.all_same(media_types):
                        if media_types[0]==self.TYPE_IMAGE: 
                            self.media_type=self.TYPE_ALBUM
                            
                        elif media_types[0]==self.TYPE_VIDEO:
                            #multiple video stream
                            self.link_action=sitesBase.DI_ACTION_YTDL
                            self.media_type=self.TYPE_VIDS
                        
                        return link_url, self.media_type
                        
                    else: #video and images
                        log('    eroshare link has mixed video and images %d' %len(items) )
                        #self.link_action=sitesBase.DI_ACTION_YTDL
                        self.media_type=self.TYPE_ALBUM
                        return link_url, self.media_type
            else:
                #try an alternate method
                log('      var album string not found. trying alternate method ')

                div_item_list = parseDOM(content.text, "div", attrs = { "class": "item-list" })
                #log('div_item_list=' + repr(div_item_list))
                poster = parseDOM(div_item_list, "video", ret = "poster")
                #log('    poster=' + repr(poster))
                if poster:
                    #assume video if there is poster
                    self.poster_url='http:' + poster[0]
                
                    playable_url = parseDOM(div_item_list, "source", ret = "src")
                    #log('playable_url=' + repr(playable_url))
                    if playable_url:
                        self.link_action=sitesBase.DI_ACTION_PLAYABLE
                        return playable_url[0], self.TYPE_VIDEO
                else:
                    #assume image if can't get poster
                    image=parseDOM(div_item_list, "img", ret = "src")
                    if image:
                        self.poster_url='http:' + image[0]
                        return self.poster_url, self.TYPE_IMAGE
        else:
            log('    error: eroshare get_playable_url:' + str( content.status_code ) )
            
        return '', ''

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem
        images=[]
        content = requests.get( album_url )
        
        if content.status_code==200:
            match = re.compile('var album\s=\s(\{.*\});', re.DOTALL).findall(content.text)
            #log('********* ' + match[0])    
            if match:
                j = json.loads(match[0])
                items = j.get('items')
                log( '      %d item(s)' % len(items) )

                prefix='https:'
                
                for s in items:
                    description = s.get('description') 
                    #media_url=prefix+s.get('url_orig')   #this size too big... 
                    media_url=prefix+s.get('url_full')
                    width=s.get('width')
                    height=s.get('height')
                
                    images.append( {'description': description, 
                                    'url': media_url,
                                    'width': width,
                                    'height': height,
                                    }  )
                self.assemble_images_dictList(images)
                #self.assemble_images_dictList(   ( [ s.get('description'), prefix+s.get('url_full')] for s in items)    )
    
            else:
                log('      eroshare:ret_album_list: var album string not found. ')
        else:
            log('    eroshare:ret_album_list: ' + str( content.status_code ) )
            
        return self.dictList    
    
    def get_media(self, j_item):
        h='https:'
        media_type=j_item.get('type').lower()
        if media_type==sitesBase.TYPE_VIDEO:
            media_url =  j_item.get('url_mp4')
            poster_url=h+j_item.get('url_full')
            thumb_url =h+j_item.get('url_thumb')
        elif media_type==sitesBase.TYPE_IMAGE:
            poster_url=h+j_item.get('url_full')
            media_url =poster_url    #h+j_item.get('url_orig')  #url_orig is very slow
            thumb_url =h+j_item.get('url_thumb')
        else:
            log('   returned media type(%s) does not match defined media types ' %media_type )
        return media_type, media_url, poster_url, thumb_url   

    def get_thumb_url(self):
        return self.thumb_url
        
class ClassVidble(sitesBase):
    regex='(vidble.com)'
    
    def is_album(self, media_url):
        if '/album/' in media_url:
            self.media_type = self.TYPE_ALBUM
            return True
        else:
            return False
    
    def get_playable_url(self, link_url, is_probably_a_video=False ):

        if self.is_album(link_url):
            self.media_type = sitesBase.TYPE_ALBUM
            return link_url, self.media_type
        
        #note: image can be got by just adding .jpg at end of url
        
        content = requests.get( link_url )
        #if 'pnnh' in media_url:
        #    log('      retrieved:'+ str(content) )
        
        if content.status_code==200:
            #<meta id="metaTag" property="og:image" content="http://www.vidble.com/a9CvdmX9gu_sqr.jpeg"></meta>
            thumb= parseDOM(content.text, "meta", attrs = { "id": "metaTag" }, ret = "content")
            #log('    thumb='+repr(thumb))
            if thumb:
                self.thumb_url=thumb[0]

            div_item_list = parseDOM(content.text, "div", attrs = { "id": "ContentPlaceHolder1_divContent" })
            #log('    div_item_list=' + repr(div_item_list))
            if div_item_list:
                images = parseDOM(div_item_list, "img", ret = "src")
                #for idx, item in enumerate(images):
                #    log('    %d %s' %(idx, item))
                if images[0]:
                    self.poster_url = 'http://www.vidble.com' + images[0]
                    
                    return self.poster_url, self.TYPE_IMAGE
        else:
            log('    error: vidble get_playable_url:' + str( content.status_code ) )
            
        return '', ''

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem
        content = requests.get( album_url )
        
        if content.status_code==200:
            #<meta id="metaTag" property="og:image" content="http://www.vidble.com/a9CvdmX9gu_sqr.jpeg"></meta>
            #thumb= parseDOM(content.text, "meta", attrs = { "id": "metaTag" }, ret = "content")
            #log('    thumb='+repr(thumb))

            div_item_list = parseDOM(content.text, "div", attrs = { "id": "ContentPlaceHolder1_divContent" })
            #log('      div_item_list=' + repr(div_item_list))
            
            if div_item_list:
                images = parseDOM(div_item_list, "img", ret = "src")
                prefix = 'http://www.vidble.com' 
            
                self.assemble_images_dictList(   (prefix + s for s in images)    )

            else:
                log('      vidble: no div_item_list:  ')
        else:
            log('    vidble:ret_album_list: ' + str( content.status_code ) )

        #log( pprint.pformat(self.dictList, indent=1) )
        return self.dictList    

    def get_thumb_url(self):
        if not self.thumb_url:
            img=self.request_meta_ogimage_content()
            self.thumb_url=img
            self.poster_url=self.thumb_url
                        
        return self.thumb_url

class ClassImgbox(sitesBase):
    SITE='imgbox'
    regex='(imgbox.com)'
    
    include_gif_in_get_playable=True
    
    def is_album(self, media_url):
        if '/g/' in media_url:
            self.media_type = self.TYPE_ALBUM
            return True
        else:
            return False
    
    def get_playable_url(self, media_url, is_probably_a_video=False ):
        if self.is_album(media_url):
            log('  is an album:'+ media_url )
            self.media_type = self.TYPE_ALBUM
            return media_url, sitesBase.TYPE_ALBUM

        log('  scraping:'+ media_url )            
        content = requests.get( media_url )
        
        if content.status_code==200:
            #https://github.com/downthemall/anticontainer/blob/master/plugins/imgbox.com.json
            match = re.compile("id=\"img\".+?src=\"(.+?)\" title=\"(.+?)\"", re.DOTALL).findall(content.text)
            #log('    match:' + repr(match))    
            if match:
                #log('      match' + match[0][0])
                self.poster_url=match[0][0]
                self.thumb_url=self.poster_url
                return self.poster_url, self.TYPE_IMAGE
            else:
                log("    %s can't scrape image " %(self.__class__.__name__ ) )
        else:
            log('    error: %s get_playable_url: %s' %(self.__class__.__name__, repr( content.status_code ) ) )
            
        return '', ''

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem
        
        content = requests.get( album_url )
        
        if content.status_code==200:
            div_item_list=parseDOM(content.text, "div", attrs = { "id": "gallery-view-content" })
            #log('    div_item_list='+repr(div_item_list))

            #<a href="/fbDGR5kF"><img alt="Fbdgr5kf" src="http://1.s.imgbox.com/fbDGR5kF.jpg" /></a>
            #<a href="/3f2FGZBl"><img alt="3f2fgzbl" src="http://4.s.imgbox.com/3f2FGZBl.jpg" /></a>
            #<a href="/qnUS37TF"><img alt="Qnus37tf" src="http://6.s.imgbox.com/qnUS37TF.jpg" /></a>
            #<a href="/PgEHrpIy"><img alt="Pgehrpiy" src="http://9.s.imgbox.com/PgEHrpIy.jpg" /></a>
            #<a href="/W2sv8pFp"><img alt="W2sv8pfp" src="http://3.s.imgbox.com/W2sv8pFp.jpg" /></a>
            
            if div_item_list:
                thumbs = parseDOM(div_item_list, "img", ret = "src" )
                href   = parseDOM(div_item_list,   "a", ret = "href" )
                #reassemble href into the image urls
                images = ('http://i.imgbox.com%s.jpg' %s for s in href)
                #self.assemble_images_dictList( images )

                #combine 2 list into 1 multidimensional list http://stackoverflow.com/questions/12624623/two-lists-into-one-multidimensional-list
                list3= map(list,zip( images, thumbs )) 
            
                #assemble_images_dictList expects the 1st item to be the image title, we don't have one
                #add an additional column in out multidimensional list
                list3 = [('',i,t) for i,t in list3]
                
                #for i in list3:
                #    log('    ' + repr(i))
                
                #for i in images:
                #    log('    ' + i)
                    
            
                self.assemble_images_dictList( list3 )
            else:
                log('      %s: cant find <div ... id="gallery-view-content"> '  %(self.__class__.__name__ ) )
        else:
            log('    %s :ret_album_list: %s ' %(self.__class__.__name__, repr(content.status_code) ) )


        #log( pprint.pformat(self.dictList, indent=1) )            
        return self.dictList    

    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url

class ClassReddit(sitesBase):
    regex='^\/r\/(.+)(?:\/|$)|(reddit.com)'
    
    def get_playable_url(self, link_url, is_probably_a_video):
        from utils import assemble_reddit_filter_string
        self.get_video_id()
        log('    subreddit=' + self.video_id )

        self.media_type=sitesBase.TYPE_REDDIT
        
        if self.video_id:   #link_url is in the form of "r/subreddit". this type of link is found in comments
            self.link_action='listSubReddit'
            reddit_url=assemble_reddit_filter_string('',self.video_id)
            return reddit_url, self.media_type
        else:               #link_url is in the form of https://np.reddit.com/r/teslamotors/comments/50bc6a/tesla_bumped_dying_man_up_the_production_queue_so/d72vfbg?context=2
            if '/comments/' in link_url:
                self.link_action='listLinksInComment'
                return link_url, self.media_type
        
        return '',''
    
    def get_video_id(self):
        self.video_id=''
        match = re.findall( '^\/r\/(.+)(?:\/|$)' , self.media_url)
        if match:
            self.video_id=match[0]
        
    def get_thumb_url(self):
        
        if self.video_id:
            #get subreddit icon_img, header_img or banner_img
            headers = {'User-Agent': reddit_userAgent}
            req='https://www.reddit.com/r/%s/about.json' %self.video_id
            #log( req )
            #log('headers:' + repr(headers))
            r = requests.get( req, headers=headers )
            if r.status_code == requests.codes.ok:
                j=r.json()
                j=j.get('data')
                #log( pprint.pformat(j, indent=1) )
                icon_img=j.get('icon_img')
                #header_img=j.get('icon_img')
                #banner_img=j.get('banner_img')
                self.thumb_url=icon_img
                self.poster_url=self.thumb_url
                #log( repr(self.thumb_url) )
            else:
                log( '    getting subreddit info:%s' %r.status_code ) 
            
class ClassKindgirls(sitesBase):
    regex='(kindgirls.com)'

    def is_album(self, media_url):
        if '/gallery/' in media_url:
            self.media_type = self.TYPE_ALBUM
            return True
        else:
            return False
    
    def get_playable_url(self, link_url, is_probably_a_video=False ):

        if self.is_album(link_url):
            self.media_type = sitesBase.TYPE_ALBUM
            return link_url, self.media_type
        
        content = requests.get( link_url )
        
        if content.status_code==200:
            #<meta id="metaTag" property="og:image" content="http://www.vidble.com/a9CvdmX9gu_sqr.jpeg"></meta>
            thumb= parseDOM(content.text, "meta", attrs = { "id": "metaTag" }, ret = "content")
            #log('    thumb='+repr(thumb))
            if thumb:
                self.thumb_url=thumb[0]

            div_item_list = parseDOM(content.text, "div", attrs = { "id": "photo" })
            
            #log('    div_item_list=' + repr(div_item_list))
            if div_item_list:
                images = parseDOM(div_item_list, "img", ret = "src")
                #for idx, item in enumerate(images):
                #    log('    %d %s' %(idx, item))
                if images[0]:
                    self.thumb_url = images[0]
                    self.poster_url= images[0]
                    
                    return self.poster_url, self.TYPE_IMAGE
        else:
            self.clog(content.status_code ,'get_playable_url')
            
        return '', ''

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem
        content = requests.get( album_url )
        images=[]
        if content.status_code==200:

            div_item_list = parseDOM(content.text, "div", attrs = { "id": "cuerpo" })
            #log('      div_item_list=' + repr(div_item_list))
            
            if div_item_list:
                thumb_div=parseDOM(div_item_list, "div", attrs = { "id": "up_der" })
                #log( repr( thumb_div) )
                if thumb_div:
                    #log('    thumb div')
                    thumb = parseDOM(thumb_div,"a", ret="href")[0]
                    if thumb:
                        self.thumb_url=thumb
                        self.poster_url=self.thumb_url
                        #log('    thumb:' + thumb )
                
                img_divs=parseDOM(div_item_list, "div", attrs = { "class": "gal_list" })
                
                if img_divs:
                    for div in img_divs:
                        image_p     = parseDOM(div,"img", ret="src")[0]
                        image_title = parseDOM(div,"img", ret="title")[0]
                        image_o     = parseDOM(div,"a", attrs={ "target":"_blank"}, ret="href")[0]
                        
                        images.append( [image_title, image_o, image_p]  ) 
            
                #for i in images: log( repr(i) )
                self.assemble_images_dictList( images )
                #log( pprint.pformat(self.dictList, indent=1) ) 
                
            else:
                log("      can't find div id cuerpo")
        else:
            self.clog(content.status_code ,album_url)

        #log( pprint.pformat(self.dictList, indent=1) )
        return self.dictList    

    def get_thumb_url(self):
        #log('    get thumb [%s]' %self.thumb_url )
        if self.thumb_url:
            return self.thumb_url
        
        #log('    checking if album')
        if self.is_album(self.original_url):
            #log('    is album')
            #this also gets the thumb and poster url's
            dictlist = self.ret_album_list( self.original_url )
            return self.thumb_url
            
class Class500px(sitesBase):
    regex='(500px.com)'

    key_string='consumer_key=aKLU1q5GKofJ2RDsNVEJScLy98aLKNmm7lADwOSB'
    
    def is_album(self, media_url):
        if '/galleries/' in media_url:
            self.media_type = self.TYPE_ALBUM
            return True
        else:
            return False
    
    def get_thumb_url(self, image_url="", thumbnail_type='b'):

        self.get_photo_info()

        if self.poster_url:
            return self.poster_url
        
        return ''

    def get_photo_info(self, photo_url=''):
        if not photo_url:
            photo_url=self.media_url
        
        self.get_video_id()
        #log('    videoID:' + self.video_id)
        if self.video_id:
            #image_size — Numerical size of the image to link to, 1 being the smallest and 4 being the largest.
            api_url= 'https://api.500px.com/v1/photos/%s?image_size=6&%s' %(self.video_id, self.key_string) 
            #log( '    ' + api_url )
            r = requests.get(api_url )
            #log(r.text)
            
            if r.status_code == 200:   #http status code 200 is success
                j=json.loads(r.text)   #.replace('\\"', '\'')
                j=j.get('photo')
                
                title=j.get('name')
                self.poster_url=j.get('image_url')
                self.media_w=j.get('width')  #width and height not accurate unless image size 6  (not sure if applies to all)
                self.media_h=j.get('height')
                self.media_url=self.poster_url
                
                #log('      %s %dx%d %s' %(title, self.media_w,self.media_h, self.poster_url )  )
                #return self.poster_url, sitesBase.TYPE_IMAGE
            else:
                self.clog(r.status_code ,api_url)
        else:
            log("    %s cannot get videoID %s" %( self.__class__.__name__, self.original_url) )
        
        
    def get_playable_url(self, media_url, is_probably_a_video=True ):
        #log('    class 500px prep media url')

        if self.is_album(media_url):
            return media_url, sitesBase.TYPE_ALBUM

        self.get_photo_info()

        if self.poster_url:
            return self.poster_url, sitesBase.TYPE_IMAGE
        
        return '',''

    def get_video_id(self):
        self.video_id=''
        #match = re.findall( '500px\.com/(?:photo)/(.+)(?:/|$)' , self.original_url)
        match = re.findall( '500px\.com/photo/(.+?)(?:\/|$)' , self.original_url)
        #log('    '+ repr(match) )
        if match:
            self.video_id=match[0]

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem

        #first query for the user id then call the request that gets the image list
        
        #gallery links look like this:
        #  https://500px.com/seanarcher/galleries/outdoor-portraits
        #  https://500px.com/mikimacovei/galleries/favorites
        #result = re.search('500px\.com/(.*?)/galleries', self.original_url)
        result = re.search('500px\.com/(.*?)/(.+)?', self.original_url)
        username  =result.group(1)
        album_name=result.group(2)
        log('    username:%s album:%s' %(username, album_name) )

        api_call='https://api.500px.com/v1/users/show?username=%s&%s' %(username, self.key_string)
        log('    req='+api_call)
        r = requests.get(api_call)
        if r.status_code == requests.codes.ok:
            j=r.json()
            user_id=j.get('user').get('id')
        else:
            log( '    error getting user ID:%s [%s]' %(r.status_code, api_call)  )
            return
        
        if user_id:
            #         https://api.500px.com/v1/users/777395/galleries/outdoor-portraits/items?consumer_key=aKLU1q5GKofJ2RDsNVEJScLy98aLKNmm7lADwOSB
            api_call='https://api.500px.com/v1/users/%s/%s/items?image_size=6&rpp=100&%s' %(user_id, album_name, self.key_string)
            log('    req='+api_call)
            r = requests.get(api_call)
            #log( r.text )
            if r.status_code == requests.codes.ok:
                images=[]
                j=r.json()
                j=j.get('photos')
                for photo in j:
                    title=photo.get('name') 
                    description=photo.get('description')
                    image=photo.get('image_url')
                    width=photo.get('width') 
                    height=photo.get('height') 
                    #combined=self.combine_title_and_description(title, description)
                    
                    #images.append( [combined, image ]  )
                    images.append( {'title': title,
                                    'description': description,
                                    'url': image,
                                    'width': width,
                                    'height': height,
                                    }  )
                     
                    
                #for i in images: log( repr(i) )
                self.assemble_images_dictList( images )
                #log( pprint.pformat(self.dictList, indent=1) ) 
            else:
                log( '    error getting user ID:%s [%s]' %(r.status_code, api_call)  )
                return
        else:
            log("    can't get user id")
            return
        return self.dictList

class ClassSlimg(sitesBase):
    regex='(sli.mg)'
    
    #header='Authorization: Client-ID {YOUR_CLIENT_ID}'
    header={'Authorization': 'Client-ID M5assQr4h9pj1xQNJ6ehAEXuDq27RsYE'}
    #api_key='M5assQr4h9pj1xQNJ6ehAEXuDq27RsYE'

    def is_album(self, link_url):
        if '/a/' in link_url:
            self.media_type = self.TYPE_ALBUM
            return True
        else:
            return False
            
    def get_playable_url(self, link_url, is_probably_a_video):
        
        if self.is_album(link_url):
            return link_url, sitesBase.TYPE_ALBUM
        
        self.get_video_id()
        
        api_req='https://api.sli.mg/media/' + self.video_id
        #log('  ' + api_req )
        r = requests.get(api_req, headers=self.header)
        
        #log('  ' + r.text)
        if r.status_code == requests.codes.ok:
            j=r.json()
            j=j.get('data')
            self.media_url=j.get('url_direct')
            self.thumb_url=self.media_url
            self.poster_url=self.media_url
            
            self.media_w=j.get('width')
            self.media_h=j.get('height')
            
            if j.get('webm'):  #use webm if available.
                self.link_action=sitesBase.DI_ACTION_PLAYABLE
                self.media_type=sitesBase.TYPE_VIDEO
                self.media_url=j.get('url_webm')
            else:  #we're assuming that all items without a webm is image
                self.media_type=sitesBase.TYPE_IMAGE
            
            #if 'gif' in j.get('mimetype'):
            #    self.media_url=j.get('url_mp4')   #url_webm is also available
            
            return self.media_url, self.media_type
            
        else:
            self.clog(r.status_code ,api_req)
            
    
    def get_video_id(self):
        #looks like the filename is also the video id
        self.video_id=''
        
        match = re.compile('sli\.mg/(?:a/|album/)?(.+)').findall(self.media_url)
        #log('    matches' + repr(match) )
        if match: 
            self.video_id=match[0]
        
    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url
    
    def ret_album_list(self, album_url, thumbnail_size_code=''):
        self.get_video_id()
        
        api_req='https://api.sli.mg/album/%s/media' % self.video_id
        #log('  ' + api_req )
        r = requests.get(api_req, headers=self.header)
        
        #log('  ' + r.text)
        if r.status_code == requests.codes.ok:
            j=r.json()
            j=j.get('data')
            
            media_count=j.get('media_count')
            images=[]
            for i in j.get('media'):
            
                title=i.get('title')
                description=i.get('description')
                media_url=i.get('url_direct')
                media_w=i.get('width')
                media_h=i.get('height')
                #combined='[B]%s[/B]\n%s' % (title, description)
                
                #combined= self.combine_title_and_description(title,description)
                
                if i.get('webm'):  #we don't support video in album but still avoid gif video  if possible. 
                    media_url=j.get('url_webm')
  
                images.append( {'title': title,
                                'description': description,
                                'url': media_url,
                                'width': media_w,
                                'height': media_h,
                                }  )
            
            self.assemble_images_dictList(images)
        else:
            self.clog(r.status_code ,api_req)
        
        return self.dictList

# class Deviantart(sitesBase):
#     regex='(deviantart.com)|(sta.sh)'
#     
#     clientid='5198'
#     
#     def get_playable_url(self, media_url, is_probably_a_video):
#         pass
#     
#     def get_thumb_url(self):
#         pass
#     
#     def ret_album_list(self, album_url, thumbnail_size_code=''):
#         pass

class genericAlbum1(sitesBase):
    regex='(http://www.houseofsummersville.com/)|(weirdrussia.com)|(cheezburger.com)'
    
    ps=[  [ 'houseofsummersville.com', '',          ['div', { "dir": "ltr" },None],  
                                                    ['div', { "class": "separator" },None], 
                                                    ['a', {}, "href"]     
            ],      
          [         'weirdrussia.com', '',          ['div', { "class": "thecontent clearfix" },None],  
                                                    ['img', {}, "data-layzr"]          
            ],
          [         'cheezburger.com', 'no_ext',    ['div', { "class": "nw-post-asset" },None],  
                                                   # ['li', { "class": "list-asset-item" },None],
                                                    ['img', {}, "src"]          
            ],
        ]
    
    def get_playable_url(self, link_url, is_probably_a_video=False ):
        return link_url, self.TYPE_ALBUM
    
    def get_thumb_url(self):
        pass
    
    def ret_album_list(self, album_url, thumbnail_size_code=''):
        #returns an object (list of dicts) that contain info for the calling function to create the listitem/addDirectoryItem
        
        for p in self.ps:
            if p[0] in album_url:
                break
        
        html = self.get_html( album_url )
        if html:
            
            
            images=self.get_images(html, p)
            
            for i in images: log( repr(i) )
            
            #log( pprint.pformat(self.dictList, indent=1) ) 
                
            self.assemble_images_dictList( images )


        #log( pprint.pformat(self.dictList, indent=1) )
        return self.dictList    

    def get_images(self, html, p):
        log(    'len %d' %(len(p)) )
        p_options=p[1]
        images=[]
        if len(p)==5:
            div_item_list = parseDOM(html, name=p[2][0], attrs = p[2][1], ret=p[2][2] )
            #log('        div_item_list=' + repr(div_item_list))
            if div_item_list:
                #img_divs=parseDOM(div_item_list, name="div", attrs = { "class": "separator" }, ret=None)
                img_divs=parseDOM(div_item_list, name=p[3][0], attrs=p[3][1], ret=p[3][2])
                if img_divs:
                    #log('          img_divs=' + repr(img_divs))
                    for div in img_divs:
                        #log('          img_div=' + repr(div))
                        #image_p     = parseDOM(div,"img", ret="src")[0]
                        #image_title = parseDOM(div,"img", ret="title")[0]
                        #image_o     = parseDOM(div,name="a", attrs={}, ret="href")
                        image_o      = parseDOM(div,name=p[4][0], attrs=p[4][1], ret=p[4][2])
                        #log('          image_o=' + repr(image_o))
                        if image_o:
                            if p_options=='no_ext':   #don't check for image extensions
                                images.append( image_o[0] )
                            else:
                                if link_url_is_playable( image_o[0] ) == 'image':
                                    #log('          appending:' + repr(image_o))
                                    images.append( image_o[0] )
        elif len(p)==4:
            #log( '***name=%s, attrs=%s, ret=%s)' %(p[2][0], p[2][1], p[2][2])) 
            big_div=parseDOM(html, name=p[2][0], attrs=p[2][1], ret=p[2][2])
            if big_div:
                #log('          big_div=' + repr(big_div))
                imgs = parseDOM(big_div,name=p[3][0], attrs=p[3][1], ret=p[3][2])
                #log('          image_o=' + repr(image_o))
                self.append_imgs( imgs, p, images)
        elif len(p)==3:
            #log( '***name=%s, attrs=%s, ret=%s)' %(p[1][0], p[1][1], p[1][2])) 
            imgs=parseDOM(html, name=p[2][0], attrs=p[2][1], ret=p[2][2])
            self.append_imgs( imgs, p, images)
        
        return images

    def append_imgs(self, imgs, p, images_list):
        p_options=p[1]
        if imgs:
            for i in imgs:
                #log('          i=' + repr(i))
                if i:
                    if p_options=='no_ext':   #don't check for image extensions
                        images_list.append( i )
                    else:
                        if link_url_is_playable( i ) == 'image':
                            images_list.append( i )
        

class genericImage(sitesBase):
    regex='(Redd.it/)|(RedditUploads)|(RedditMedia)|(\.(jpg|jpeg|png|gif)(?:\?|$))'
    
    def get_playable_url(self, media_url, is_probably_a_video=False ):
        media_url=media_url.replace('&amp;','&')  #this replace is only for  RedditUploads but seems harmless for the others...
        self.media_url=media_url
        
        #from urlparse import urlparse
        #hoster=urlparse(media_url).netloc
    
        u=media_url.split('?')[0]
        filename,ext=parse_filename_and_ext_from_url(u)
        #log( "  parsed filename" + filename + " ext---" + ext)
        if ext=='gif':  
            self.media_type = sitesBase.TYPE_VIDEO
            self.link_action =sitesBase.DI_ACTION_PLAYABLE  #playable uses pluginUrl directly   
        else:
            self.media_type=sitesBase.TYPE_IMAGE
            self.thumb_url=self.media_url
            self.poster_url=self.media_url
            
        return self.media_url, self.media_type

    def get_thumb_url(self):
        self.thumb_url=self.media_url
        self.poster_url=self.media_url
        return self.thumb_url

class genericVideo(sitesBase):
    regex='(\.(mp4|webm|avi|3gp|MPEG|WMV|ASF|FLV|MKV|MKA)(?:\?|$))'
    def get_thumb_url(self):
        pass

    def get_playable_url(self, media_url, is_probably_a_video):
        pass
    
class LinkDetails():
    def __init__(self, media_type, link_action, playable_url='', thumb='', poster='', poster_w=0, poster_h=0 ):
        #self.kodi_url = kodi_url
        self.playable_url = playable_url
        self.media_type = media_type
        self.link_action = link_action
        self.thumb = thumb
        self.poster = poster
        self.poster_w = poster_w
        self.poster_h = poster_h
        

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

    

def sitesManager( media_url ):
    #picks which class will handle the media identification and extraction for website_name
    for subcls in sitesBase.__subclasses__():
        regex=subcls.regex
        if regex:
            match=re.compile( regex  , re.I).findall( media_url )
            #if 'giphy' in media_url: log('      checking '+ subcls.regex )
            if match : 
                #log('      *****match '+ subcls.regex )
                return subcls( media_url )

def parse_reddit_link(link_url, assume_is_video=True, needs_preview=False, get_playable_url=False ):
    
    
    if not link_url: return

    hoster = sitesManager( link_url )
    #log( '  %s %s => %s' %(hoster.__class__.__name__, link_url, hoster.media_url if hoster else '[Not supported]' ) )

    if hoster:
        try:
            if get_playable_url:
                pass
            
            prepped_media_url, media_type = hoster.get_playable(link_url, assume_is_video)
            log( '    parsed: %s %s %s ' % ( hoster.link_action, media_type,  prepped_media_url ) )
            
            if needs_preview:
                thumb=hoster.get_thumb_url()
                #poster=hoster.poster_url
                #log('      poster_url:'+poster)

            if not hoster.link_action:
                if media_type==sitesBase.TYPE_IMAGE:
                    hoster.link_action='viewImage'
                if media_type==sitesBase.TYPE_ALBUM:
                    hoster.link_action='listAlbum'
#                 if media_type==sitesBase.TYPE_RDIT_IMG:  #reddit preview image is as good as the one from link
#                     media_type=sitesBase.TYPE_IMAGE
#                     hoster.link_action='viewImage'
#                     if previewimage:
#                         prepped_media_url=previewimage
#                     else:
#                         #if there was no preview image, hoster.get_thumb_url() would have gotten the preview image 
#                         prepped_media_url=hoster.poster_url
                        

            ld=LinkDetails(media_type, hoster.link_action, prepped_media_url, hoster.thumb_url, hoster.poster_url)
            return ld
        
        except Exception as e:
            log("  EXCEPTION parse_reddit_link "+ str( sys.exc_info()[0]) + "  " + str(e) )

    if ytdl_sites:  pass
    else: load_ytdl_sites()
    
    ytdl_match=False
    for rex in ytdl_sites:
        #if rex.startswith('f'):log( ' rex=='+ rex )
        if rex in link_url:
            #log( "    ydtl-" + rex +" matched IN>"+ media_url)
            hoster=rex
            ytdl_match=True
            break
        #regex is much slower than the method above.. left here in case needed in the future 
        # match = re.compile( "(%s)" %rex  , re.DOTALL).findall( media_url )
        # if match : log( "matched ytdl:"+ rex);  break
    if ytdl_match:
        ld=LinkDetails(sitesBase.TYPE_VIDEO, 'playYTDLVideo', link_url, '', '')
        return ld

def url_is_supported(url_to_check):
    #search our supported_sites[] to see if media_url can be handled by plugin
    #log('    ?url_is_supported:'+ url_to_check) 
    dont_support=False
    if ytdl_sites:  pass
    else: load_ytdl_sites()

    hoster = sitesManager( url_to_check )
    if hoster:
        log( '  url_is_supported by: %s %s ' %(hoster.__class__.__name__, url_to_check ) )
        return True
    
    #if this setting is set to true, all links are supported. it is up to ytdl to see if it actually plays
    if use_ytdl_for_unknown_in_comments:
        return True

    #originally ytdl sites were matched in supported sites[] but it is getting so big that it is moved to a separate configurable file.
    #check if it matches ytdl sites
    for rex in ytdl_sites:
        if rex in url_to_check:
            #log( "    ydtl-" + rex +" matched IN>"+ media_url)
            #hoster=rex
            return True

        #regex is much slower than the method above.. left here in case needed in the future 
        # match = re.compile( "(%s)" %rex  , re.DOTALL).findall( media_url )
        # if match : log( "matched ytdl:"+ rex);  break

    if url_to_check.startswith('/r/'):
        return True

    return False

def load_ytdl_sites():
    #log( '***************load_ytdl_sites '  )
    #reads the ytdl supported sites file 
    #http://stackoverflow.com/questions/1706198/python-how-to-ignore-comment-lines-when-reading-in-a-file
    global ytdl_sites
    with open(default_ytdl_psites_file) as f:   #ytdl_psites_file=special://profile/addon_data/script.reddit.reader/ytdl_psites_file
        for line in f:
            line = line.split('#', 1)[0]
            line = line.rstrip()
            ytdl_sites.append(line)
    
    with open(default_ytdl_sites_file) as f:   #ytdl_psites_file=special://profile/addon_data/script.reddit.reader/ytdl_psites_file
        for line in f:
            line = line.split('#', 1)[0]
            line = line.rstrip()
            ytdl_sites.append(line)


def ytdl_hoster( url_to_check ):
    pass

#def build_script( mode, url, name="", type="", script_to_call=addonID):
    #builds the parameter for xbmc.executebuiltin   --> 'RunAddon(script.reddit.reader, ... )'
#    return "RunAddon(%s,%s)" %(addonID, "?mode="+ mode+"&url="+urllib.quote_plus(url)+"&name="+str(name)+"&type="+str(type) )


if __name__ == '__main__':
    pass




def listImgurAlbum(album_url, name, type):
    #log("listImgurAlbum")
    #from resources.lib.domains import ClassImgur
    #album_url="http://imgur.com/a/fsjam"
    ci=ClassImgur()
        
    dictlist=ci.ret_album_list(album_url, 'l')
    display_album_from(dictlist, name)

def display_album_from(dictlist, album_name):

    directory_items=[]
    label=""
    
    using_custom_gui=True
    
    for idx, d in enumerate(dictlist):
        ti=d['li_thumbnailImage']
        media_url=d.get('DirectoryItem_url')

        #Error Type: <type 'exceptions.TypeError'> cannot concatenate 'str' and 'list' objects
        log('  display_album_from list:'+ media_url + "  " )  # ****** don't forget to add "[0]" when using parseDOM    parseDOM(div,"img", ret="src")[0]
        
        #There is only 1 textbox for Title and description in our custom gui. 
        #  I don't know how to achieve this in the xml file so it is done here:
        #  combine title and description without [CR] if label is empty. [B]$INFO[Container(53).ListItem.Label][/B][CR]$INFO[Container(53).ListItem.Plot]
        #  new note: this is how it is done: 
        #     $INFO[Container(53).ListItem.Label,[B],[/B][CR]] $INFO[Container(53).ListItem.Plot]  #if the infolabel is empty, nothing is printed for that block
        combined = '[B]'+ d['li_label2'] + "[/B][CR]" if d['li_label2'] else ""
        combined += d['infoLabels'].get('plot') if d['infoLabels'].get('plot') else ""
        d['infoLabels']['plot'] = combined
        #d['infoLabels']['genre'] = "0,-2000"
        #d['infoLabels']['year'] = 1998
        #log( d['infoLabels'].get('plot') ) 
            
        liz=xbmcgui.ListItem(label=label, 
                             label2=d['li_label2'],
                             iconImage='',
                             thumbnailImage='')

        #classImgur puts the media_url into  d['DirectoryItem_url']  no modification.
        #we modify it here...
        #url_for_DirectoryItem = sys.argv[0]+"?url="+ urllib.quote_plus(d['DirectoryItem_url']) +"&mode=viewImage"
        #hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, IsPlayable=make_addon_url_from(d['DirectoryItem_url'],False)
        #if poster_url=="": poster_url=ti
        
        
        liz.setInfo( type='video', infoLabels= d['infoLabels'] ) #this tricks the skin to show the plot. where we stored the picture descriptions
        #liz.setArt({"thumb": ti, "poster":poster_url, "banner":d['DirectoryItem_url'], "fanart":poster_url, "landscape":d['DirectoryItem_url']   })             
        liz.setArt({"thumb": ti, "banner":media_url })


        directory_items.append( (media_url, liz, False,) )

    from resources.lib.guis import cGUI
 
    #msg=WINDOW.getProperty(url)
    #WINDOW.clearProperty( url )
    #log( '   msg=' + msg )

    #<label>$INFO[Window(10000).Property(foox)]</label>
    #WINDOW.setProperty('view_450_slideshow_title',WINDOW.getProperty(url))
     
    li=[]
    for di in directory_items:
        #log( str(di[1] ) )
        li.append( di[1] )
         
    #ui = cGUI('FileBrowser.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li)
    ui = cGUI('view_450_slideshow.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, id=53)
    
    ui.include_parent_directory_entry=False
    #ui.title_bar_text=WINDOW.getProperty(url)
    
    ui.doModal()
    del ui
    #WINDOW.clearProperty( 'view_450_slideshow_title' )
    #log( '   WINDOW.getProperty=' + WINDOW.getProperty('foo') )

# def listTumblrAlbum(t_url, name, type):    
#     #from resources.lib.domains import ClassTumblr
#     log("listTumblrAlbum:"+t_url)
#     t=ClassTumblr(t_url)
#     
#     media_url, media_type =t.get_playable_url(t_url, True)
#     #log('  ' + str(media_url))
#     
#     if media_type=='album':
#         display_album_from( media_url, name )
#     else:
#         log("  listTumblrAlbum can't process " + media_type)    
# 
# def listEroshareAlbum(e_url, name, type):    
#     #from resources.lib.domains import ClassTumblr
#     log("listEroshareAlbum:"+e_url)
#     e=ClassEroshare()
#     
#     dictlist=e.ret_album_list(e_url, '')
#     display_album_from( dictlist, name )
# 
# def listVidbleAlbum(e_url, name, type):    
#     #from resources.lib.domains import ClassTumblr
#     log("listVidbleAlbum:"+e_url)
#     e=ClassVidble()
#     
#     dictlist=e.ret_album_list(e_url, '')
#     display_album_from( dictlist, name )
# 
# def listImgboxAlbum(e_url, name, type):    
#     #from resources.lib.domains import ClassTumblr
#     log("listImgboxAlbum:"+e_url)
#     e=ClassImgbox()
#     
#     dictlist=e.ret_album_list(e_url, '')
#     display_album_from( dictlist, name )

def listAlbum(album_url, name, type):
    from slideshow import slideshowAlbum
    log("listAlbum:"+album_url)
    
    hoster = sitesManager( album_url )
    log( '  %s %s ' %(hoster.__class__.__name__, album_url ) )

    if hoster:
        dictlist=hoster.ret_album_list(album_url)
        
        if type=='return_dictlist':  #used in autoSlideshow  
            return dictlist
        
        if not dictlist:
            xbmc.executebuiltin('XBMC.Notification("%s", "%s" )'  %( translation(32200), translation(32055) )  )  #slideshow, no playable items
            return
        
        if addon.getSetting('use_slideshow_for_album') == 'true':
            slideshowAlbum( dictlist, name )
        else:
            display_album_from( dictlist, name )
    

def playInstagram(media_url, name, type):
    #from resources.lib.domains import ClassInstagram
    log('playInstagram '+ media_url)
    #instagram video handled by ytdl. links that reddit says is image are handled here.
    i=ClassInstagram( media_url )
    image_url=i.get_playable_url(media_url, False)
    
    viewImage(image_url,"Instagram","")


def viewImage(image_url, name, preview_url):
    #url='d:\\aa\\lego_fusion_beach1.jpg'

    from resources.lib.guis import cGUI

    log('  viewImage %s, %s, %s' %( image_url, name, preview_url))
    
    #msg=WINDOW.getProperty(url)
    #WINDOW.clearProperty( url )
    #log( '   msg=' + msg )
    msg=""
    li=[]
    liz=xbmcgui.ListItem(label=msg, label2="", iconImage="", thumbnailImage=image_url)
    liz.setInfo( type='video', infoLabels={"plot": msg, } ) 
    liz.setArt({"thumb": preview_url, "banner":image_url })             

    li.append(liz)
    ui = cGUI('view_450_slideshow.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, id=53)   
    ui.include_parent_directory_entry=False
    
    ui.doModal()
    del ui
    return
    
#     from resources.lib.guis import qGUI
#     
#     ui = qGUI('view_image.xml' ,  addon_path, defaultSkin='Default', defaultRes='1080i')   
#     #no need to download the image. kodi does it automatically!!!
#     ui.image_path=url
#     ui.doModal()
#     del ui
#     return
# 
#     #this is a workaround to not being able to show images on video addon
#     log('viewImage:'+url +'  ' + name )
# 
#     ui = ssGUI('tbp_main.xml' , addon_path)
#     items=[]
#     
#     items.append({'pic': url ,'description': "", 'title' : name })
#     
#     ui.items=items
#     ui.album_name=""
#     ui.doModal()
#     del ui

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



def playFlickr(flickr_url, name, type):
    #from resources.lib.domains import ClassFlickr
    log('play flickr '+ flickr_url)
    f=ClassFlickr( flickr_url )

    try:
        media_url, media_type =f.get_playable_url(flickr_url, False)
        #log('  flickr class returned %s %s' %(media_type, media_url))
        if media_type=='photo':
            if media_url:
                viewImage(media_url,"Flickr", f.thumb_url )
            else:
                raise Exception(translation(32009))  #Cannot retrieve URL
        else: #if media_type in ['album','group','gallery']:
            display_album_from( media_url, name )
    
    except Exception as e:
        log('   playFlickr error:' + str(e) )
        xbmc.executebuiltin('XBMC.Notification("%s", "%s" )' %( e, flickr_url )  )

# def playImgurVideo(imgur_url, name, type):
#     #from resources.lib.domains import ClassImgur
#     #log('**************play imgur '+ imgur_url)
#     f=ClassImgur( imgur_url )
#  
#     media_url, media_type =f.get_playable_url(imgur_url, False)
#     if media_type=='album':
#         display_album_from( media_url, name )
#     elif media_type=='video':
#         playVideo(media_url, name, "")
#     elif media_type=='image':
#         viewImage(media_url,"Imgur","")


def playGfycatVideo(gfycat_url, name, type):
    log( "  play gfycat video " + gfycat_url )
    
    g=ClassGfycat()
    GfycatStreamUrl, media_type=g.get_playable_url( gfycat_url )
    
    playVideo(GfycatStreamUrl, name, type)


def playVidmeVideo(vidme_url, name, type):
    log('playVidmeVideo')
    v=ClassVidme(vidme_url)
    vidme_stream_url=v.get_playable_url(vidme_url, True)
    if vidme_stream_url:
        playVideo(vidme_stream_url, name, type)
    else:
        media_status=v.whats_wrong()
        xbmc.executebuiltin('XBMC.Notification("Vidme","%s")' % media_status  )
        
def playStreamable(media_url, name, type):
    log('playStreamable '+ media_url)
    
    s=ClassStreamable(media_url)
    playable_url=s.get_playable_url(media_url, True)

    if playable_url:
        playVideo(playable_url, name, type)
    else:
        #media_status=s.whats_wrong()  #streamable does not tell us if access to video is denied beforehand
        xbmc.executebuiltin('XBMC.Notification("Streamable","%s")' % "Access Denied"  )
    
def playVineVideo(vine_url, name, type):
    #from resources.lib.domains import ClassVine
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

#ytdl handles liveleak videos now.
def playLiveLeakVideo(id, name, type):
    playVideo(getLiveLeakStreamUrl(id), name, type)

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
