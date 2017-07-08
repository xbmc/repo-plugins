#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import sys
import re
import requests
import json
import urlparse


from default import addon, streamable_quality   #,addon_path,pluginhandle,addonID
from default import addon_path, pluginhandle, reddit_userAgent, REQUEST_TIMEOUT
from utils import log, parse_filename_and_ext_from_url, image_exts, link_url_is_playable, ret_url_ext, remove_duplicates, safe_cast, clean_str,pretty_datediff, nested_lookup

use_addon_for_youtube     = addon.getSetting("use_addon_for_youtube") == "true"
use_addon_for_Liveleak    = addon.getSetting("use_addon_for_Liveleak") == "true"


from CommonFunctions import parseDOM

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
      ,'link_action'
      ,'channel_id'         #used in youtube videos
      ,'video_id'           #used in youtube videos
      ]

ytdl_sites=[]


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
    description=None  #additional description gathered from link
    video_id=''

    include_gif_in_get_playable=False   #it is best to parse the link and get the mp4/webm version of a gif media. we can't do this with some sites so we just return the gif media instead of looking for mp4/webm

    TYPE_IMAGE='image'
    TYPE_ALBUM='album'
    TYPE_VIDEO='video'
    TYPE_GIF='gifvideo'   #this indicates that the video needs to be repeated
    TYPE_VIDS ='vids'
    TYPE_MIXED='mixed'
    TYPE_REDDIT='reddit'
    TYPE_UNKNOWN='unknown'
    DI_ACTION_PLAYABLE='playable'
    DI_ACTION_YTDL='playYTDLVideo'
    DI_ACTION_URLR='playURLRVideo'
    DI_ACTION_ERROR='error_message'

    def __init__(self, link_url):
        self.media_url=link_url
        self.original_url=link_url

    def get_html(self,link_url=''):
        if not link_url:
            link_url=self.original_url

        content = self.requests_get(link_url)

        return content.text

    @classmethod
    def requests_get(self, link_url, headers=None, timeout=REQUEST_TIMEOUT, allow_redirects=True):
        content = requests.get( link_url, headers=headers, timeout=timeout, allow_redirects=allow_redirects )

        if content.status_code==requests.codes.ok:
            return content
        else:
            log('    error: %s requests_get: %s %s' %(self.__class__.__name__, repr( content.status_code ), link_url ) )
            content.raise_for_status()

            return None

    def get_playable(self, media_url='', is_probably_a_video=False ):
        media_type=''
        if not media_url:
            media_url=self.media_url

        _,ext=parse_filename_and_ext_from_url(media_url)
        if self.include_gif_in_get_playable:
            if ext in ["mp4","webm","gif"]:
                media_type=self.TYPE_VIDEO
                if ext=='gif':
                    media_type=self.TYPE_GIF
                    self.link_action=sitesBase.DI_ACTION_PLAYABLE
                    self.thumb_url=media_url
                    self.poster_url=self.thumb_url
                return media_url,media_type
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

            return link_url #will a video link resolve to a preview image?
        else:
            try:

                head=requests.head(link_url, timeout=(4,4),allow_redirects=True)

                if head.status_code==requests.codes.ok:
                    if 'html' in head.headers.get('content-type') :
                        r = self.requests_get(link_url,headers=None, timeout=(4,4), allow_redirects=True)

                        if r:
                            a=parseDOM(r.text, "meta", attrs = { "property": "og:image" }, ret="content" )   #most sites use <meta property="
                            b=parseDOM(r.text, "meta", attrs = {     "name": "og:image" }, ret="content" )   #boardgamegeek uses <meta name="
                            i=next((item for item in [a,b] if item ), '')

                            if i:
                                try:
                                    return urlparse.urljoin(link_url, i[0]) #handle relative or absolute
                                except IndexError: pass
                                else:
                                    log('      %s: cant find <meta property="og:image" '  %(self.__class__.__name__ ) )
            except Exception as e:
                log('request_meta_ogimage_content:'+str(e))


    def clog(self, error_code, request_url):
        log("    %s error:%s %s" %( self.__class__.__name__, error_code ,request_url) )
    @classmethod
    def get_first_url_from(self,string_with_url,return_all_as_list=False):
        if string_with_url:
            match = re.compile("(https?://[^\s/$.?#].[^\s]*)['\\\"]?(?:$)?").findall(string_with_url)

            if match:
                if return_all_as_list:
                    return match
                else:
                    return match[0]

    @classmethod
    def split_text_into_links(self,string_with_url):
        if string_with_url:
            string_with_url=string_with_url+" \nhttp://blank.padding\n" #imperfect regex: need a padding to make regex work

            match = re.compile("([\s\S]*?(?:(https?://\S*?\.\S*?)(?:[\s)\[\]{},;\"\':<]|$)))").findall(string_with_url) #imperfect regex: this regex needs more work so that we don't need to add the padding above and modify the match to remove the http... later in code.
            if match:

                return match

    def set_media_type_thumb_and_action(self,media_url,default_type=TYPE_VIDEO, default_action=DI_ACTION_YTDL):
        _,ext=parse_filename_and_ext_from_url(media_url)
        self.media_url=media_url
        if ext=='gif':
            self.media_type=self.TYPE_GIF #sitesBase.TYPE_VIDEO
            self.link_action=self.DI_ACTION_PLAYABLE  #playable uses pluginUrl directly
        elif ext in image_exts:    #image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp']
            self.media_type=self.TYPE_IMAGE
        elif ext in ["mp4","webm"]:
            self.media_type=self.TYPE_VIDEO
            self.link_action=self.DI_ACTION_PLAYABLE
        else:
            self.media_type=default_type
            self.link_action=default_action

        if self.media_type in [self.TYPE_GIF, self.TYPE_IMAGE]:

            self.thumb_url=media_url if self.thumb_url else self.thumb_url
            self.poster_url=media_url if self.poster_url else self.poster_url

    def assemble_images_dictList(self,images_list):
        title=''
        desc=''
        image_url=''
        thumbnail=''
        width=0
        height=0
        item_type=None
        isPlayable=None
        for item in images_list:

            if isinstance(item, (basestring,unicode) ):   #type(item) in [str,unicode]:  #if isinstance(item, basestring):

                image_url=item
                thumbnail=image_url
            elif  isinstance(item, list):    #type(item) is list:
                if len(item)==1:

                    image_url=item[0]
                elif len(item)==2:

                    title=item[0]
                    image_url=item[1]
                    thumbnail=image_url
                elif len(item)==3:

                    title=item[0]
                    image_url=item[1]
                    thumbnail=item[2]
            elif isinstance(item, dict):  #type(item) is dict:
                title    =item.get('title') if item.get('title') else ''
                label2   =item.get('label2','')
                desc     =item.get('description') if item.get('description') else ''
                image_url=item.get('url')
                thumbnail=item.get('thumb')
                width    =item.get('width') if item.get('width') else 0
                height   =item.get('height') if item.get('height') else 0
                item_type=item.get('type')
                isPlayable=item.get('isPlayable')
                link_action=item.get('link_action','')
                channel_id=item.get('channel_id','')
                video_id=item.get('video_id','')

            infoLabels={ "Title": title, "plot": desc }
            e=[ title                   #'li_label'           #  the text that will show for the list (we use description because most albumd does not have entry['type']
               ,label2                  #'li_label2'          #
               ,""                      #'li_iconImage'       #
               ,thumbnail               #'li_thumbnailImage'  #
               ,image_url               #'DirectoryItem_url'  #
               ,False                   #'is_folder'          #
               ,item_type               #'type'               # video pictures  liz.setInfo(type='pictures',
               ,isPlayable              #'isPlayable'         # key:value       liz.setProperty('IsPlayable', 'true')  #there are other properties but we only use this
               ,infoLabels              #'infoLabels'         # {"title": post_title, "plot": description, "plotoutline": description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": hoster, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin
               ,'none'                  #'context_menu'       # ...
               ,width
               ,height
               ,desc                    #'description'
               ,link_action             #'link_action'
               ,channel_id              #'channel_id'
               ,video_id                #'video_id'
                ]
            self.dictList.append(dict(zip(keys, e)))



def all_same(items):

    return all(x == items[0] for x in items)

def url_resolver_support(link_url):
    import urlresolver
    if urlresolver.HostedMediaFile(link_url).valid_url():
        return True
    return False

class ClassYoutube(sitesBase):
    regex='(youtube.com/)|(youtu.be/)|(youtube-nocookie.com/)|(plugin.video.youtube/play)'
    video_id=''
    url_type=''

    api_key='AIzaSyBilnA0h2drOvpnqno24xeVqGy00fp07so'

    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url

        o = urlparse.urlparse(media_url)
        query = urlparse.parse_qs(o.query)

        self.url_type, id_from_url=self.get_video_channel_user_or_playlist_id_from_url( self.media_url )

        if self.url_type=='video':
            self.video_id=id_from_url
            self.get_thumb_url() #there is no request penalty for getting yt thumb url so we do it here
            self.link_action, playable_url=self.return_action_and_link_tuple_accdg_to_setting_wether_to_use_addon_for_youtube()

            if 't' in query or '#t=' in media_url:
                return media_url, self.TYPE_VIDEO
            else:
                return playable_url, self.TYPE_VIDEO
        elif self.url_type in ['channel','playlist','user']:
            log("    %s_ID=%s <--%s" %( self.url_type, repr(id_from_url), self.media_url) )
            self.link_action='listRelatedVideo'
            return media_url, self.TYPE_VIDS
        else:
            self.link_action='playYTDLVideo'
            return media_url, self.TYPE_VIDEO

    @classmethod
    def get_video_channel_user_or_playlist_id_from_url(self, youtube_url):
        o = urlparse.urlparse(youtube_url)
        query = urlparse.parse_qs(o.query)

        video_id=self.get_video_id( youtube_url )
        if video_id:
            return 'video', video_id
        else:
            channel_id=self.get_channel_id_from_url( youtube_url )
            user_id=self.get_user_id_from_url( youtube_url )
            playlist_id=query.get('list','')

            if channel_id:
                return 'channel', channel_id
            elif playlist_id:
                return 'playlist', playlist_id[0]
            elif user_id:
                return 'user', user_id
        return '',''

    def return_action_and_link_tuple_accdg_to_setting_wether_to_use_addon_for_youtube(self, video_id=None):
        if not video_id:
            video_id=self.video_id
        link_actn=''
        link_=''

        if video_id:
            if use_addon_for_youtube:
                link_actn=self.DI_ACTION_PLAYABLE
                link_="plugin://plugin.video.youtube/play/?video_id=" + video_id
            else:
                link_actn=self.DI_ACTION_YTDL

                link_="http://youtube.com/v/{0}".format(video_id)

            return link_actn, link_

    @classmethod
    def get_video_id(self, yt_url):

        video_id_regex=re.compile('(?:youtube(?:-nocookie)?\.com/(?:\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&;]v=)|youtu\.be\/|plugin:\/\/plugin\.video\.youtube\/play\/\?video_id=)([a-zA-Z0-9_-]{11})', re.DOTALL)
        video_id=''
        match = video_id_regex.findall(yt_url)
        if match:
            video_id=match[0]
        else:

            o = urlparse.urlparse(yt_url)
            query = urlparse.parse_qs(o.query)
            if 'a' in query and 'u' in query:   #if all (k in query for k in ("a","u")):
                u=query['u'][0]

                match = video_id_regex.findall('youtube.com'+u)
                if match:
                    video_id=match[0]
                else:
                    log("    Can't get youtube video id:"+yt_url)
        return video_id

    @classmethod
    def get_channel_id_from_url(self, yt_url):
        channel_id=''
        channel_id_regex=re.compile('(?:https?:\/\/)?(?:www\.)?youtube\.com\/(?:channel\/)([a-zA-Z0-9\-_]{1,})', re.DOTALL)
        match = channel_id_regex.findall(yt_url)
        if match:
            channel_id=match[0]

        return channel_id

    @classmethod
    def get_user_id_from_url(self, yt_url):
        channel_id=''
        channel_id_regex=re.compile('(?:https?:\/\/)?(?:www\.)?youtube\.com\/(?:user\/)([a-zA-Z0-9\-_]{1,})', re.DOTALL)
        match = channel_id_regex.findall(yt_url)
        if match:
            channel_id=match[0]

        return channel_id

    def get_thumb_url(self):
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

        """
        quality0123=1
        if not self.video_id:
            self.video_id=self.get_video_id(self.media_url)

        if self.video_id:
            self.thumb_url='http://img.youtube.com/vi/%s/%d.jpg' %(self.video_id,quality0123)
            self.poster_url='http://img.youtube.com/vi/%s/%d.jpg' %(self.video_id,0)

        return self.thumb_url

    def get_links_in_description(self, return_channelID_only=False):
        links=[]
        self.video_id=self.get_video_id( self.media_url )
        youtube_api_key=self.ret_api_key()
        if self.video_id:

            query_params = {
                'key': youtube_api_key,
                'id': self.video_id,
                'fields':'items(snippet(channelId,title,description))',  #use '*' to get all fields
                'part': 'id,snippet',
            }

            api_url='https://www.googleapis.com/youtube/v3/videos?'+urllib.urlencode(query_params)
            r = self.requests_get(api_url)

            j=r.json()   #.loads(r.text)  #j=json.loads(r.text.replace('\\"', '\''))
            description=clean_str(j, ['items',0,'snippet','description'])
            channel_id=clean_str(j, ['items',0,'snippet','channelId'])
            if return_channelID_only:
                return channel_id


            text_and_links_tuple_list=self.split_text_into_links(description)

            if text_and_links_tuple_list:
                for text, link in text_and_links_tuple_list:
                    ld=parse_reddit_link(link, assume_is_video=False, needs_preview=False )  #setting needs_preview=True slows things down
                    if ld:
                        links.append( {'title': text,
                                        'type': ld.media_type,
                                        'description': text,
                                        'url': ld.playable_url if ld.playable_url else link,
                                        'thumb':ld.thumb,

                                        'link_action':ld.link_action,
                                        'video_id':ld.video_id,
                                        }  )
                    else:
                        links.append( {'title': text,
                                        'type': self.TYPE_UNKNOWN,
                                        'description': text,
                                        'url': link,
                                        }  )
                self.assemble_images_dictList(links)
                return self.dictList
        else:
            log("  can't get video id")
            if return_channelID_only:
                channel_id=self.get_channel_id_from_url( self.media_url )
                log("    got channel id:"+channel_id)
                return channel_id

    def ret_api_key(self):
        youtube_api_key = addon.getSetting("youtube_api_key")
        if not youtube_api_key:
            youtube_api_key=self.api_key
        return youtube_api_key

    def ret_album_list(self, type_='related'):
        youtube_api_key=self.ret_api_key()
        links=[]
        query_params={}

        self.url_type, id_from_url=self.get_video_channel_user_or_playlist_id_from_url( self.media_url )

        if type_=='channel':  #here, user specifically asked to show videos in channel via context menu
            channel_id=self.get_links_in_description(return_channelID_only=True)
            if not channel_id:
                raise ValueError('Could not get channel_id')
            request_action, query_params = self.build_query_params_for_channel_videos(youtube_api_key,channel_id)
        else:  #if type_=='related':
            if self.url_type=='video':
                self.video_id=id_from_url

                request_action='search'
                query_params = {    #https://developers.google.com/youtube/v3/docs/search/list#relatedToVideoId
                    'key': youtube_api_key,
                    'fields':'items(id(videoId),snippet(publishedAt,channelId,title,description,thumbnails(medium)))',
                    'type': 'video',
                    'maxResults': '50',
                    'part': 'snippet',
                    'order': 'date',
                    'relatedToVideoId': self.video_id,
                }

            elif self.url_type=='channel': #try to see if we were able to parse channel_id from url if no video_id was parsed
                request_action, query_params = self.build_query_params_for_channel_videos(youtube_api_key,id_from_url)
            elif  self.url_type=='playlist':
                request_action, query_params = self.build_query_params_for_playlist_videos(youtube_api_key,id_from_url)
            elif  self.url_type=='user':

                channel_id,uploads=self.get_id_from_user(id_from_url)

                request_action, query_params = self.build_query_params_for_playlist_videos(youtube_api_key,uploads)    #  2 quota cost

        if query_params:
            links.extend( self.get_video_list(request_action, query_params) )

            self.assemble_images_dictList(links)
            return self.dictList

    def build_query_params_for_channel_videos(self,youtube_api_key, channel_id):
        return  'search', {
                'key': youtube_api_key,
                'fields':'items(id(videoId),snippet(publishedAt,channelId,title,description,thumbnails(medium)))',
                'type': 'video',         #video,channel,playlist.

                'maxResults': '50',      # Acceptable values are 0 to 50
                'part': 'snippet',
                'order': 'date',
                'channelId': channel_id,
            }

    def build_query_params_for_channel(self, channel_display_name):
        return  'search', {
                'key': self.ret_api_key(),
                'fields':'items(id(videoId),snippet(publishedAt,channelId,title,description,thumbnails(medium)))',
                'type': 'channel',         #video,channel,playlist.
                'maxResults': '50',      # Acceptable values are 0 to 50
                'part': 'snippet',
                'order': 'date',
                'q': channel_display_name,
            }
    def build_query_params_for_playlist_videos(self,youtube_api_key, playlist_id):
        return  'playlistItems', {
                'key': youtube_api_key,

                'type': 'video',         #video,channel,playlist.
                'maxResults': '50',      # Acceptable values are 0 to 50
                'part': 'snippet',
                'playlistId': playlist_id,
            }
    def build_query_params_for_user_videos(self,youtube_api_key, user_id):
        return  'channels', {
                'key': youtube_api_key,
                'maxResults': '50',      # Acceptable values are 0 to 50
                'part': 'snippet,contentDetails',
                'forUsername': user_id,
            }

    def get_id_from_user(self,user_id):
        query_params = {
            'key': self.ret_api_key(),
            'part': 'snippet,contentDetails',
            'forUsername': user_id,
        }
        api_url='https://www.googleapis.com/youtube/v3/channels?'+urllib.urlencode(query_params)
        r = self.requests_get(api_url)

        j=r.json()   #.loads(r.text)  #j=json.loads(r.text.replace('\\"', '\''))
        channel_id=clean_str(j, ['items',0,'id'])
        uploads=clean_str(j, ['items',0,'contentDetails','relatedPlaylists','uploads'])

        return channel_id,uploads

    def get_video_list(self, request_action, query_params):
        links=[]
        api_url='https://www.googleapis.com/youtube/v3/{0}?{1}'.format(request_action,urllib.urlencode(query_params))

        r = self.requests_get(api_url)

        j=r.json()
        items=j.get('items')
        for i in items:


            if request_action=='search':
                videoId=clean_str(i, ['id','videoId'])
            elif request_action=='playlistItems': #videoId is located somewhere else in the json if using playlistItems
                videoId=clean_str(i, ['snippet','resourceId','videoId'])

            publishedAt=clean_str(i, ['snippet','publishedAt'])
            pretty_date=self.pretty_date(publishedAt)


            channel_id=clean_str(i, ['snippet','channelId'])
            title=clean_str(i, ['snippet','title'])
            description=clean_str(i, ['snippet','description'])

            thumb640=clean_str(i, ['snippet','thumbnails','standard','url']) #640x480
            thumb480=clean_str(i, ['snippet','thumbnails','high','url'])   #480x360
            thumb320=clean_str(i, ['snippet','thumbnails','medium','url']) #320x180

            link_action, playable_url=self.return_action_and_link_tuple_accdg_to_setting_wether_to_use_addon_for_youtube(videoId)

            links.append( {'title': title,
                            'type': self.TYPE_VIDEO,
                            'label2': pretty_date,
                            'description': description,
                            'url': playable_url,
                            'thumb': next((i for i in [thumb640,thumb480,thumb320] if i ), ''),
                            'isPlayable': 'true' if link_action==self.DI_ACTION_PLAYABLE else 'false',
                            'link_action':link_action,
                            'channel_id':channel_id,
                            'video_id':videoId,
                            }  )
        return links

    def pretty_date(self, yt_date_string):
        from datetime import datetime
        import time

        try:
            date_object = datetime.strptime(yt_date_string,"%Y-%m-%dT%H:%M:%S.000Z")
        except TypeError:
            date_object = datetime(*(time.strptime(yt_date_string,"%Y-%m-%dT%H:%M:%S.000Z")[0:6]))

        now_utc = datetime.utcnow()

        return pretty_datediff(now_utc, date_object)

class ClassImgur(sitesBase):
    regex='(imgur.com)'

    request_header={ "Authorization": "Client-Id 7b82c479230b85f" }

    is_an_album_type=""
    is_an_album_link=""
    images_count=0
    image_url_of_a_single_image_album=''

    def get_album_thumb(self, media_url):

        album_id=self.get_album_or_gallery_id(media_url)

        request_url="https://api.imgur.com/3/album/"+album_id

        r = self.requests_get(request_url, headers=ClassImgur.request_header)

        j = r.json()    #j = json.loads(r.text)

        thumb_image_id=j['data'].get('cover')


        if thumb_image_id:

            return 'http://i.imgur.com/'+thumb_image_id+'m.jpg', 'http://i.imgur.com/'+thumb_image_id+'l.jpg'

        return "",""

    def is_an_album(self, media_url):

        r=None
        request_url=''
        media_url=media_url.split('?')[0] #get rid of the query string

        if "/a/" in media_url:
            album_id=media_url.split("/a/",1)[1]

            request_url="https://api.imgur.com/3/album/"+album_id
            r=self.requests_get(request_url, headers=ClassImgur.request_header)
        else:

            if '/gallery/' in media_url:
                r=self.get_gallery_info(media_url)

        if r:

            j = r.json()

            jdata=j.get('data')
            if jdata:
                self.is_an_album_type= jdata.get('type')   #"image/png" , "image\/gif"
                self.is_an_album_link= jdata.get('link')

                if jdata.get('mp4'):
                    self.is_an_album_link= jdata.get('mp4')

            self.images_count=jdata.get('images_count')
            if self.images_count:

                if self.images_count == 1:

                    if jdata.get('images')[0].get('mp4'):
                        self.image_url_of_a_single_image_album=jdata.get('images')[0].get('mp4')
                    else:
                        self.image_url_of_a_single_image_album=jdata.get('images')[0].get('link')

                    return False
                else:

                    images=self.ret_images_dict_from_album_json(j)
                    self.assemble_images_dictList(images)
                    return True
            else:

                self.image_url_of_a_single_image_album=self.is_an_album_link
                return False

        else:
            return False

    def get_gallery_info(self, media_url):
        gallery_name = media_url.split("/gallery/",1)[1]
        if gallery_name=="":
            return False

        request_url="https://api.imgur.com/3/gallery/"+gallery_name

        try:
            r = self.requests_get(request_url, headers=ClassImgur.request_header)
        except requests.exceptions.HTTPError:

            request_url="https://api.imgur.com/3/image/"+gallery_name

            try:
                r = self.requests_get(request_url, headers=ClassImgur.request_header)
            except requests.exceptions.HTTPError:

                request_url="https://api.imgur.com/3/album/"+gallery_name

                r = self.requests_get(request_url, headers=ClassImgur.request_header)

        return r

    def ask_imgur_for_link(self, media_url):


        media_url=media_url.split('?')[0] #get rid of the query string
        img_id=media_url.split("com/",1)[1]  #.... just get whatever is after "imgur.com/"   hope nothing is beyond the id

        if '/' in img_id:

            img_id = img_id.split('/')[-1]     #the -1 gets the last item on the list returned by split

        if img_id:
            request_url="https://api.imgur.com/3/image/"+img_id
            r = self.requests_get(request_url, headers=ClassImgur.request_header)
            j=r.json()

            if j['data'].get('mp4'):
                return j['data'].get('mp4')
            else:
                return j['data'].get('link')

    def get_thumb_url(self):
        return self.get_thumb_from_url()

    def get_thumb_from_url(self,link_url=''):


        thumbnail_type='b'

        if not link_url:
            link_url=self.original_url

        if self.thumb_url:
            return self.thumb_url

        is_album=self.is_an_album(link_url)

        if is_album:

            self.thumb_url, self.poster_url= self.get_album_thumb(link_url)
            return self.thumb_url

        o=urlparse.urlparse(link_url)
        filename,ext=parse_filename_and_ext_from_url(link_url)

        if ext=="":

            filename = o.path[1:]
            ext = 'jpg'
        elif ext in ['gif', 'gifv', 'webm', 'mp4']:
            ext = 'jpg'

        thumb= ("%s://%s/%s%c.%s" % ( o.scheme, o.netloc, filename, thumbnail_type, ext ) )


        return thumb

    def get_album_or_gallery_id(self,album_url):

        match = re.compile(r'imgur\.com/(?:a|gallery)/(.*)/?', re.DOTALL).findall(album_url)
        if match:
            album_name = match[0]  #album_url.split("/a/",1)[1]
        else:
            log(r"ret_album_list: Can't determine album name from["+album_url+"]" )
            album_name=""
        return album_name

    def ret_album_list(self, album_url):


        album_name = self.get_album_or_gallery_id(album_url)

        if album_name=="":
            log(r"ret_album_list: Can't determine album name from["+album_url+"]" )
            return self.dictList

        request_url="https://api.imgur.com/3/album/"+album_name+"/images"

        r = self.requests_get(request_url, headers=ClassImgur.request_header)

        images=[]

        if r.status_code==200:  #http status code 200 = success

            j = r.json()   #json.loads(r.text)

            images=self.ret_images_dict_from_album_json(j)

            self.assemble_images_dictList(images)
        else:
            self.clog(r.status_code ,request_url)

        return self.dictList

    def ret_images_dict_from_album_json(self, j):
        images=[]

        if 'images' in j['data']:
            imgs=j.get('data').get('images')
        else:
            imgs=j.get('data')

        for _, entry in enumerate(imgs):
            link_type=entry.get('type')         #image/jpeg
            if link_type=='image/gif':
                media_url=entry.get('mp4')
                media_type=self.TYPE_VIDEO
                isPlayable='true'
            else:
                media_url=entry.get('link')
                media_type=self.TYPE_IMAGE
                isPlayable='false'
            width    =entry.get('width')
            height   =entry.get('height')
            title    =entry.get('title')
            descrip  =entry.get('description')
            media_thumb_url=self.get_thumb_from_url(media_url)

            images.append( {'title': title,
                            'type': media_type,
                            'description': descrip,
                            'url': media_url,
                            'thumb': media_thumb_url,
                            'width': width,
                            'height': height,
                            'isPlayable':isPlayable,
                            }  )
        return images

    def media_id(self, media_url):

        pass

    def get_playable_url(self, media_url, is_probably_a_video): #is_probably_a_video means put video extension on it if media_url has no ext
        webm_or_mp4='.mp4'  #6/18/2016  using ".webm" has stopped working
        media_url=media_url.split('?')[0] #get rid of the query string?

        is_album=self.is_an_album(media_url)
        if is_album:
            return media_url, sitesBase.TYPE_ALBUM
        else:
            if '/gallery/' in media_url:

                media_url=self.is_an_album_link

        if self.image_url_of_a_single_image_album:
            media_url=self.image_url_of_a_single_image_album

        _,ext=parse_filename_and_ext_from_url(media_url)

        if ext == "":
            media_url=self.ask_imgur_for_link(media_url)
            _,ext=parse_filename_and_ext_from_url(media_url)


        if ext in ['gif', 'gifv', 'mp4'] :   #NOTE: we're treating all mp4 links as gif and set them to loop playback
            media_url=media_url.replace(".gifv",webm_or_mp4) #can also use .mp4.  crass but this method uses no additional bandwidth.  see playImgurVideo
            media_url=media_url.replace(".gif",webm_or_mp4)  #xbmc won't play gif but replacing .webm works!

            self.media_type=sitesBase.TYPE_GIF
            self.link_action=self.DI_ACTION_PLAYABLE

            self.thumb_url=media_url.replace(webm_or_mp4,'.jpg')
            self.poster_url=self.thumb_url
        elif ext in image_exts:    #image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp']
            self.thumb_url=media_url
            self.poster_url=self.thumb_url

            self.media_type=sitesBase.TYPE_IMAGE
        else:
            self.media_type=sitesBase.TYPE_VIDEO
            self.link_action=self.DI_ACTION_PLAYABLE

        self.media_url=media_url
        return self.media_url, self.media_type

class ClassVidme(sitesBase):
    regex='(vid.me)'

    request_header={ "Authorization": "Basic aneKgeMUCpXv6FdJt8YGRznHk4VeY6Ps:" }

    def get_playable_url(self,media_url, is_probably_a_video=True):

        request_url="https://api.vid.me/videoByUrl?url="+ urllib.quote_plus( media_url )

        r = requests.get(request_url, headers=ClassVidme.request_header, timeout=REQUEST_TIMEOUT)


        if r.status_code != 200:   #http status code 200 is success
            log("    vidme request failed, trying alternate method: "+ str(r.status_code))

            id_=re.findall( 'vid\.me/(.+?)(?:/|$)', media_url )   #***** regex capture to end-of-string or delimiter. didn't work while testing on https://regex101.com/#python but will capture fine

            request_url="https://api.vid.me/videoByUrl/" + id_[0]
            r = requests.get(request_url, headers=ClassVidme.request_header, timeout=REQUEST_TIMEOUT)

            if r.status_code != 200:
                log("    vidme request still failed:"+ str(r.text) )
                t= r.json()
                raise Exception( str(r.status_code) + ' ' + t.get('error'))

        j = r.json()    #j = json.loads(r.text)
        vid_info=j.get('video')

        status = vid_info.get( 'state' )

        if status != 'success':
            raise Exception( "vidme video: " +vid_info.get('state'))

        self.thumb_url=vid_info.get("thumbnail_url")

        self.link_action=self.DI_ACTION_PLAYABLE
        return ( vid_info.get('complete_url') ), sitesBase.TYPE_VIDEO

    def get_thumb_url(self):
        return self.thumb_url


class ClassVimeo(sitesBase):
    regex='(vimeo\.com/)'
    video_id=''

    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url

        self.get_video_id()

        if self.video_id:

            self.link_action=sitesBase.DI_ACTION_YTDL
            return media_url, self.TYPE_VIDEO

        else:
            log("    %s cannot get videoID %s" %( self.__class__.__name__, media_url) )

            self.link_action=sitesBase.DI_ACTION_YTDL
            return media_url, self.TYPE_VIDEO

    def get_video_id(self):

        match = re.compile('vimeo.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|album\/(?:\d+)\/video\/|)(\d+)(?:$|\/|\?)', re.DOTALL).findall(self.media_url)
        if match:

            self.video_id=match[0]

    def get_thumb_url(self):

        if not self.video_id:
            self.get_video_id()

        request_url='http://vimeo.com/api/v2/video/%s.json' % self.video_id

        r = self.requests_get(request_url)

        j=r.json()
        self.poster_url=j[0].get('thumbnail_large')
        self.thumb_url=self.poster_url


        return self.thumb_url

class ClassGiphy(sitesBase):
    regex='(giphy\.com)|(gph\.is)'

    key='dc6zaTOxFJmzC'
    video_url=''
    video_id=''

    def get_playable_url(self, media_url, is_probably_a_video=True ):

        if 'gph.is' in media_url:
            log('    giphy short url detected:' + media_url)
            media_url=self.request_meta_ogimage_content(media_url)

        if 'media' in media_url:
            if 'giphy.gif' in media_url:
                self.media_url=media_url.replace('giphy.gif','giphy-loop.mp4')

                self.link_action=sitesBase.DI_ACTION_PLAYABLE
                log('    simple replace ' + self.media_url )
                return self.media_url, sitesBase.TYPE_VIDEO    #giphy auto loops x times

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

            content = self.requests_get(request_url)
            j = content.json()

            images=j.get('data').get('images')


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
            log("cannot get giphy id")

        return False

    def get_video_id(self):
        self.video_id=''
        match = re.compile('giphy\.com/media/([^ /]+)/|i\.giphy\.com/([^ /]+)\.gif|giphy\.com/gifs/(?:.*-)?([^ /?]+)').findall(self.media_url)

        for m in match[0]:
            if m:
                self.video_id=m
                return

    def get_thumb_url(self):

        if self.thumb_url:
            return self.thumb_url
        else:
            self.get_media_info()

        return self.thumb_url

class ClassDailymotion(sitesBase):
    regex='(dailymotion\.com)'

    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url

        self.link_action=sitesBase.DI_ACTION_YTDL
        return media_url, self.TYPE_VIDEO


    def get_video_id(self):
        match = re.compile('.+dailymotion.com\/(?:video\/([^_]+))?[^#]*(?:#video=([^_&]+))?', re.DOTALL).findall(self.media_url)

        for m in match[0]:
            if m:
                self.video_id=m
                return

    def get_thumb_url(self):

        return self.media_url.replace('/video/','/thumbnail/video/')

class ClassLiveleak(sitesBase):
    regex='(liveleak.com)'


    def get_playable_url(self, media_url='', is_probably_a_video=False ):
        if use_addon_for_Liveleak:
            self.link_action=self.DI_ACTION_PLAYABLE
            return "plugin://plugin.video.liveleak/?mode=view&url={0}".format(urllib.quote_plus( media_url )), self.TYPE_VIDEO
        else:
            self.link_action=sitesBase.DI_ACTION_YTDL
            return self.media_url, self.TYPE_VIDEO

    def get_thumb_url(self):

        if not self.thumb_url:
            img=self.request_meta_ogimage_content()
            if img:
                self.thumb_url=img
                self.poster_url=self.thumb_url

                return self.thumb_url

class ClassStreamable(sitesBase):
    regex='(streamable.com)'
    video_id=''

    def get_playable_url(self, media_url, is_probably_a_video=True):


        self.get_video_id()

        url_mp4=""
        url_mp4m=""
        url_webm=""
        url_webmm=""

        if self.video_id:
            api_url='https://api.streamable.com/videos/%s' %self.video_id
            r = self.requests_get(api_url)

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

                url_hq=url_mp4 if url_mp4 else url_mp4m
                if url_hq=="":
                    url_hq=url_webm if url_webm else url_webmm

                url_mq=url_mp4m if url_mp4m else url_mp4
                if url_mq=="":
                    url_mq=url_webmm if url_webmm else url_webm

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

        for m in match[0]:
            if m:
                self.video_id=m
                return


    def get_thumb_url(self):
        log('    getting thumbnail [%s] %s' %(self.video_id, self.media_url ) )
        if not self.video_id:
            self.get_video_id()

        self.thumb_url="https://cdn.streamable.com/image/%s.jpg" %self.video_id
        self.poster_url=self.thumb_url

        return self.thumb_url

class ClassTumblr(sitesBase):
    regex='(tumblr\.com)'

    api_key='no0FySaKYuQHKl0EBQnAiHxX7W0HY4gKvlmUroLS2pCVSevIVy'
    include_gif_in_get_playable=True

    def get_thumb_url(self):

        return self.thumb_url

    def get_playable_url(self, media_url, is_probably_a_video=True ):


        if "www.tumblr.com" in media_url:   #warning:nsfw!!  https://www.tumblr.com/video/johncena2014/144096330849/500/
            match = re.findall('https?://www.tumblr.com/(?:post|image|video)/(.+?)/(.+?)(?:/|$)',media_url)
        else:
            match = re.findall('https?://(.*)\.tumblr.com/(?:post|image|video)/(.+?)(?:/|$)',media_url)

        blog_identifier = match[0][0]
        post_id         = match[0][1]

        api_url='http://api.tumblr.com/v2/blog/%s/posts?api_key=%s&id=%s' %(blog_identifier,self.api_key,post_id )

        r = self.requests_get(api_url)

        j=json.loads(r.text.replace('\\"', '\''))

        post=j['response']['posts'][0]

        media_type=post['type']  #  text, photo, quote, link, chat, audio, video, answer


        if media_type == 'photo':

            self.thumb_url=post['photos'][0]['alt_sizes'][1]['url']    #alt_sizes 0-5

            if len(post['photos'])==1:
                image=post['photos'][0]['original_size']['url']


                self.poster_url=image
                return image, sitesBase.TYPE_IMAGE

            else:

                return self.media_url, sitesBase.TYPE_ALBUM

        elif media_type == 'video':
            self.thumb_url=post['thumbnail_url']
            return post['video_url'], sitesBase.TYPE_VIDEO
        elif media_type == 'audio':
            return post['audio_url'], media_type

        return "", media_type

    def ret_album_list(self, album_url, thumbnail_size_code=''):


        if "www.tumblr.com" in album_url:   #warning:nsfw!!  https://www.tumblr.com/video/johncena2014/144096330849/500/
            match = re.findall('https?://www.tumblr.com/(?:post|image|video)/(.+?)/(.+?)(?:/|$)',album_url)
        else:
            match = re.findall('https?://(.*)\.tumblr.com/(?:post|image|video)/(.+?)(?:/|$)',album_url)

        blog_identifier = match[0][0]
        post_id         = match[0][1]

        api_url='http://api.tumblr.com/v2/blog/%s/posts?api_key=%s&id=%s' %(blog_identifier,self.api_key,post_id )

        r = self.requests_get(api_url)

        j=json.loads(r.text.replace('\\"', '\''))

        post=j['response']['posts'][0]

        media_type=post['type']  #  text, photo, quote, link, chat, audio, video, answer


        if media_type == 'photo':

            self.thumb_url=post['photos'][0]['alt_sizes'][1]['url']    #alt_sizes 0-5

            list_=(        [ photo.get('caption'), photo.get('original_size').get('url'), photo['alt_sizes'][3]['url'] ]  for photo in post['photos']   )

            self.assemble_images_dictList( list_ )

        else:
            log('      %s wrong media type: %s '  %(self.__class__.__name__ ), media_type )

        return self.dictList

class ClassBlogspot(sitesBase):
    regex='(blogspot\.com)'
    include_gif_in_get_playable=True


    key_string='key=AIzaSyCcKuHRAYT1qreLx_Z3zwks9ODuEauJmUU'


    def get_playable_url(self, media_url, is_probably_a_video=True):


        content = self.ret_blog_post_request()
        if content:
            j = content.json()


            html=j.get('content')





            images=parseDOM(html, name='img', ret="src")

            if images:

                self.thumb_url=images[0]
                self.poster_url=self.thumb_url

                if len(images) == 1:
                    return images[0], self.TYPE_IMAGE
                else:
                    return media_url, self.TYPE_ALBUM



            images=parseDOM(html, name='a', ret="href")

            if images:

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
        o=urlparse.urlparse(self.media_url)   #scheme, netloc, path, params, query, fragment

        blog_path= o.path

        if not blog_path:
            log('    could not determine blog path in:' + self.media_url)
            return None

        blog_info_request='https://www.googleapis.com/blogger/v3/blogs/byurl?' + self.key_string + '&url=' + self.media_url
        content = self.requests_get(blog_info_request)

        j = content.json()

        blog_id=j.get('id')

        blog_post_request='https://www.googleapis.com/blogger/v3/blogs/%s/posts/bypath?%s&path=%s' %( blog_id, self.key_string, blog_path)

        content = self.requests_get(blog_post_request)
        return content

    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        content = self.ret_blog_post_request()
        if content:
            j = content.json()    #log( pprint.pformat(j, indent=1) )
            html=j.get('content')

            all_images=[]


            names = ['img', 'a']
            rets = ['src','href']
            all_images = []

            for name, ret in zip(names, rets):
                images = parseDOM(html, name = name, ret = ret)

                if images:
                    all_images.extend(images)


            list1=remove_duplicates(all_images)
            list2 =[]

            for i in list1:

                if link_url_is_playable(i) == 'image':
                    list2.append(i)

            self.assemble_images_dictList(  list2    )

            return self.dictList
        else:
            log('    content blank ')

class ClassInstagram(sitesBase):
    regex='(instagram.com)'

    def get_playable_url(self, media_url, is_probably_a_video=True):

        r = self.requests_get(media_url)

        jo=re.compile('window._sharedData = ({.*});</script>').findall(r.text)
        if jo:

            try:
                j=json.loads(jo[0] )

                entry_data=j.get('entry_data')
                if entry_data:

                    if 'PostPage' in entry_data.keys():
                        post_pages=entry_data.get('PostPage')

                        post_page=post_pages[0]
                        media=post_page.get('media')
                        if media:

                            display_src=media.get('display_src')
                        else:

                            media=nested_lookup('shortcode_media',post_page)[0]
                            display_src=media.get('display_url')

                        is_video=media.get('is_video')
                        self.media_w=media.get('dimensions').get('width')
                        self.media_h=media.get('dimensions').get('height')

                        self.thumb_url=display_src
                        self.poster_url=self.thumb_url

                        if is_video:
                            self.media_url=media.get('video_url')
                            self.link_action=sitesBase.DI_ACTION_PLAYABLE
                            return self.media_url, sitesBase.TYPE_VIDEO
                        else:
                            return display_src, sitesBase.TYPE_IMAGE
                    if 'ProfilePage' in entry_data.keys():
                        profile_page=entry_data.get('ProfilePage')[0]


                        self.thumb_url=nested_lookup('profile_pic_url',profile_page)[0]


                        images=self.ret_images_dict_from_album_json(profile_page)

                        self.assemble_images_dictList(images)

                        return media_url, sitesBase.TYPE_ALBUM
                else:
                    log("  Could not get 'entry_data' from scraping instagram [window._sharedData = ]")

            except (AttributeError,TypeError) as e:
                log('    exception while parsing json:'+str(e))

        return '', ''

    def ret_images_dict_from_album_json(self, j):
        images=[]
        album_nodes=j.get('user').get('media').get('nodes') #only returns about 12. we're not getting the rest for now


        for entry in album_nodes:
            is_video=entry.get('is_video')
            link_action=''
            if is_video:

                media_url=entry.get('video_url')  #video_url is not in json!

                link_action=sitesBase.DI_ACTION_PLAYABLE
                media_type=self.TYPE_VIDEO
                isPlayable='true'
            else:
                media_url=entry.get('display_src')
                media_type=self.TYPE_IMAGE
                isPlayable='false'

            width    =entry.get('dimensions').get('width')
            height   =entry.get('dimensions').get('height')
            title    =entry.get('caption')
            descrip  =entry.get('caption')
            thumb_url=entry.get('thumbnail_src')

            images.append( {'title': title,
                            'type': media_type,
                            'description': descrip,
                            'url': media_url,
                            'thumb': thumb_url,
                            'width': width,
                            'height': height,
                            'isPlayable':isPlayable,
                            'link_action':link_action,
                            }  )
        return images

    def ret_album_list(self,album_url):
        r = self.requests_get(album_url)
        jo=re.compile('window._sharedData = ({.*});</script>').findall(r.text)
        if jo:

            try:
                j=json.loads(jo[0] )
                entry_data=j.get('entry_data')
                if entry_data:
                    if 'ProfilePage' in entry_data.keys():
                        profile_page=entry_data.get('ProfilePage')[0]

                        images=self.ret_images_dict_from_album_json(profile_page)

                        self.assemble_images_dictList(images)

                        return self.dictList
                else:
                    log("  Could not get 'entry_data' from scraping instagram [window._sharedData = ]")

            except (AttributeError,TypeError) as e:
                log('    exception while parsing json:'+str(e))

    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url

class ClassGyazo(sitesBase):
    regex='(gyazo\.com)'

    def get_playable_url(self, link_url, is_probably_a_video=True):

        api_url='https://api.gyazo.com/api/oembed?url=%s' %(link_url )

        r = self.requests_get(api_url)

        j=json.loads(r.text.replace('\\"', '\''))

        media_type=j.get('type')
        self.media_w=j.get('width')
        self.media_h=j.get('height')
        media_url=j.get('url')

        log('      gyazo=%s %dx%d %s' %(media_type, self.media_w,self.media_h, j.get('url'))  )

        if ret_url_ext(link_url)=='gif':
            self.link_action=sitesBase.DI_ACTION_PLAYABLE
            self.media_type=sitesBase.TYPE_GIF
            self.media_url=link_url
        else:
            if media_type=='photo':
                self.thumb_url=media_url
                self.poster_url=self.thumb_url

                self.media_type=sitesBase.TYPE_IMAGE
                self.media_url=media_url
            elif media_type=='video':

                self.link_action=sitesBase.DI_ACTION_YTDL
                self.media_type=sitesBase.TYPE_VIDEO

                self.media_url=link_url

        return self.media_url,self.media_type


    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url

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

    def get_thumb_url(self):

        return self.thumb_url

    def get_photo_id_flic_kr(self, url):


        from base58 import decode
        b58e_id=url.split('/')[-1] #https://flic.kr/p/KSt6Hh   https://flic.kr/s/aHskGjN56V

        a = decode(b58e_id)
        sa= str(a)


        if self.media_type==self.fTYPE_GROUP:

            sa =( sa[0:-2] + '@N' + sa[-2:] )

        if self.media_type==self.fTYPE_GALLERY:

            a = a + 72157616180848087
            sa=str(a)

        log( '    decoding flickrID:' + b58e_id + ' => ' + sa )
        return sa

    def get_video_id(self):


        self.video_id=''
        if 'flic.kr' in self.media_url:
            photo_id=self.get_photo_id_flic_kr(self.media_url)
        else:

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

        self.fmedia_type=self.flickr_link_type(media_url)
        log( '    media_type='+ self.fmedia_type + "  from:" + media_url)

        self.get_video_id()
        photo_id=self.video_id

        if self.fmedia_type==self.fTYPE_ALBUM:

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

        r = self.requests_get(api_url)

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

                if i==0:
                    self.thumb_url=thumb_url
                    self.poster_url=poster_url

            return dictList

        elif self.fmedia_type==self.fTYPE_PHOTO:

            sizes=j['sizes']

            for s in sizes['size']:

                if s['label'] == 'Medium 640':
                    self.poster_url=s['source']


                if s['label'] == 'Thumbnail':
                    self.thumb_url=s['source']

                if s['label'] == 'Small':
                    self.thumb_url=s['source']

                if s['label'] == 'Medium':
                    ret_url=s['source']


                if s['label'] == 'Medium 640':
                    ret_url=s['source']


                if s['label'] == 'Medium 800':
                    ret_url=s['source']


                if s['label'] == 'Large':
                    ret_url=s['source']


                if s['label'] == 'Large 1600':
                    ret_url=s['source']


        return ret_url, self.TYPE_IMAGE

    @classmethod
    def is_an_album(self,media_url):

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

        return self.fTYPE_PHOTO

    def ret_album_list(self, album_url, thumbnail_size_code=''):

        if not self.is_an_album(album_url):
            log('  flickr link is not an album' + album_url)
            return ''

        self.fmedia_type="photo"

        self.fmedia_type=self.flickr_link_type(album_url)
        log( '    media_type='+ self.fmedia_type + "  from:" + album_url)

        self.get_video_id()
        photo_id=self.video_id

        if self.fmedia_type==self.fTYPE_ALBUM:

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

        r = self.requests_get(api_url)

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

class ClassGifsCom(sitesBase):
    regex='(gifs\.com)'


    api_key='gifs577da09e94ee1'   #gifs577da0485bf2a'
    headers = { 'Gifs-API-Key': api_key, 'Content-Type': "application/json" }


    def get_playable(self, media_url='', is_probably_a_video=False ):
        media_type=self.TYPE_VIDEO
        if not media_url:
            media_url=self.media_url

        filename,ext=parse_filename_and_ext_from_url(media_url)

        if ext in ["mp4","webm","gif"]:
            if ext=='gif':
                media_type=self.TYPE_GIF
                self.link_action=sitesBase.DI_ACTION_PLAYABLE
                self.thumb_url=media_url.replace( '%s.%s'%(filename,ext) , '%s.jpg' %(filename))
                self.poster_url=self.thumb_url
                self.media_url=media_url.replace( '%s.%s'%(filename,ext) , '%s.mp4' %(filename))   #just replacing gif to mp4 works
            return self.media_url, media_type

        if ext in image_exts:  #excludes .gif
            self.link_action='viewImage'
            self.thumb_url=media_url
            self.poster_url=self.thumb_url
            return media_url,self.TYPE_IMAGE

        return self.get_playable_url(self.media_url, is_probably_a_video=False )


    def get_thumb_url(self):

        return self.thumb_url

    def get_video_id(self):

        self.video_id=''


        match = re.compile('gifs\.com/(?:gif/)?(.+)(?:.gif|$)').findall(self.media_url)


        if match:
            vid=match[0]
            if '-' in vid:
                vid= vid.split('-')[-1]

            self.video_id=vid

    def get_playable_url(self, media_url, is_probably_a_video=True ):



        self.get_video_id()
        log('    gifs.com videoID:' + self.video_id )

        self.link_action=sitesBase.DI_ACTION_PLAYABLE
        return 'http://j.gifs.com/%s.mp4' %self.video_id , sitesBase.TYPE_VIDEO

class ClassGfycat(sitesBase):
    regex='(gfycat.com)'

    def get_playable_url(self, media_url, is_probably_a_video=True ):

        self.get_video_id()

        if self.video_id:

            request_url="https://gfycat.com/cajax/get/" + self.video_id


            try:
                content = self.requests_get(request_url)

                content = content.json()
            except requests.exceptions.HTTPError:
                log('    Error requesting info via api endpoint. Trying actual link: '+media_url)

                r = self.requests_get(media_url)
                jo=re.compile('___INITIAL_STATE__=({.*});').findall(r.text)
                if jo:

                    j=json.loads(jo[0])
                    content=j.get('detail')

            gfyItem=content.get('gfyItem')
            if gfyItem:
                self.media_w=safe_cast(gfyItem.get('width'),int,0)
                self.media_h=safe_cast(gfyItem.get('height'),int,0)
                webmSize=safe_cast(gfyItem.get('webmSize'),int,0)
                mp4Size =safe_cast(gfyItem.get('mp4Size'),int,0)

                self.thumb_url =gfyItem.get('posterUrl')  #thumb100PosterUrl
                self.poster_url=gfyItem.get('posterUrl')

                if mp4Size > webmSize:

                    stream_url=gfyItem.get('webmUrl') if gfyItem.get('webmUrl') else gfyItem.get('mp4Url')
                else:

                    stream_url=gfyItem.get('mp4Url') if gfyItem.get('mp4Url') else gfyItem.get('webmUrl')

                log('      %dx%d %s' %(self.media_w,self.media_h,stream_url)  )

                self.link_action=sitesBase.DI_ACTION_PLAYABLE
                return stream_url, self.TYPE_GIF #sitesBase.TYPE_VIDEO
            else:
                error=content.get('error')
                if error:
                    self.link_action=self.DI_ACTION_ERROR
                    return error, ""
        else:
            log("cannot get gfycat id")

        return '', ''

    def get_video_id(self):
        self.video_id=''

        match = re.findall('gfycat.com/(.+?)(?:-|$)', self.media_url)
        if match:
            self.video_id=match[0]


    def get_thumb_url(self):

        return self.thumb_url

class ClassEroshare(sitesBase):
    SITE='eroshare'
    regex='(eroshare.com)'

    def get_playable_url(self, link_url, is_probably_a_video=True ):

        content = self.requests_get( link_url )


        match = re.compile('var album\s=\s(.*)\;').findall(content.text)

        if match:
            j = json.loads(match[0])
            items = j.get('items')


            self.media_type, playable_url, self.poster_url, self.thumb_url=self.get_media(items[0])
            if len(items) == 1:

                if self.media_type==sitesBase.TYPE_VIDEO:
                    self.link_action=sitesBase.DI_ACTION_PLAYABLE

                return playable_url, self.media_type

            else:

                media_types = []
                for item in items:

                    media_types.append( item.get('type').lower() )

                images=self.ret_images_dict_from_album_json(j)
                self.assemble_images_dictList(images)

                if all_same(media_types):
                    if media_types[0]==self.TYPE_IMAGE:
                        log('    eroshare link has all images %d' %len(items) )
                        self.media_type=self.TYPE_ALBUM

                    elif media_types[0]==self.TYPE_VIDEO:
                        log('    eroshare link has all video %d' %len(items) )
                        self.link_action=sitesBase.DI_ACTION_YTDL
                        self.media_type=self.TYPE_VIDS

                    return link_url, self.media_type

                else: #video and images
                    log('    eroshare link has mixed video and images %d' %len(items) )
                    self.link_action=None #sitesBase.DI_ACTION_YTDL
                    self.media_type=self.TYPE_ALBUM
                    return link_url, self.media_type
        else:


            div_item_list = parseDOM(content.text, "div", attrs = { "class": "item-list" })

            poster = parseDOM(div_item_list, "video", ret = "poster")

            if poster:

                self.poster_url='http:' + poster[0]

                playable_url = parseDOM(div_item_list, "source", ret = "src")

                if playable_url:
                    self.link_action=sitesBase.DI_ACTION_PLAYABLE
                    return playable_url[0], self.TYPE_VIDEO
            else:

                image=parseDOM(div_item_list, "img", ret = "src")
                if image:
                    self.poster_url='http:' + image[0]
                    return self.poster_url, self.TYPE_IMAGE

        return '', ''

    def ret_album_list(self, album_url, thumbnail_size_code=''):

        content = self.requests_get( album_url)

        match = re.compile('var album\s=\s(.*)\;').findall(content.text)

        if match:
            j = json.loads(match[0])
            images=self.ret_images_dict_from_album_json(j)
            self.assemble_images_dictList(images)


        else:
            log('      eroshare:ret_album_list: var album string not found. ')

        return self.dictList

    def ret_images_dict_from_album_json(self,j):
        images=[]
        try:
            reddit_submission=j.get('reddit_submission')
            reddit_submission_title=''
            if reddit_submission:
                reddit_submission_title=reddit_submission.get('title')

            title=j.get('title') if j.get('title') else reddit_submission_title
            items=j.get('items')

            prefix='https:'
            for s in items:
                media_type=s.get('type').lower()
                description=s.get('description') if s.get('description') else title  #use title if description is blank

                media_url=prefix+s.get('url_full')
                width=s.get('width')
                height=s.get('height')
                thumb=prefix+s.get('url_thumb')
                if media_type==self.TYPE_VIDEO:
                    self.link_action=sitesBase.DI_ACTION_PLAYABLE
                    images.append( {
                                    'isPlayable':True,
                                    'thumb':thumb,
                                    'type': self.TYPE_VIDEO,
                                    'description': description,
                                    'url': s.get('url_mp4'),
                                    'width': width,
                                    'height': height,
                                    }  )
                else:
                    images.append( {
                                    'thumb':thumb,
                                    'description': description,
                                    'url': media_url,
                                    'width': width,
                                    'height': height,
                                    }  )
        except AttributeError as e:
            log('  error parsing eroshare album:'+str(e))
        return images

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


        content = self.requests_get( link_url)

        thumb= parseDOM(content.text, "meta", attrs = { "id": "metaTag" }, ret = "content")

        if thumb:
            self.thumb_url=thumb[0]

        div_item_list = parseDOM(content.text, "div", attrs = { "id": "ContentPlaceHolder1_divContent" })

        if div_item_list:
            images = parseDOM(div_item_list, "img", ret = "src")

            if images[0]:
                self.poster_url = 'http://www.vidble.com' + images[0]

                return self.poster_url, self.TYPE_IMAGE

    def ret_album_list(self, album_url, thumbnail_size_code=''):

        content = self.requests_get(album_url)


        div_item_list = parseDOM(content.text, "div", attrs = { "id": "ContentPlaceHolder1_divContent" })


        if div_item_list:
            images = parseDOM(div_item_list, "img", ret = "src")
            prefix = 'http://www.vidble.com'

            self.assemble_images_dictList(   (prefix + s for s in images)    )

        else:
            log('      vidble: no div_item_list:  ')

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
        content = self.requests_get( media_url)

        match = re.compile("id=\"img\".+?src=\"(.+?)\" title=\"(.+?)\"", re.DOTALL).findall(content.text)

        if match:

            self.poster_url=match[0][0]
            self.thumb_url=self.poster_url
            return self.poster_url, self.TYPE_IMAGE
        else:
            log("    %s can't scrape image " %(self.__class__.__name__ ) )

    def ret_album_list(self, album_url, thumbnail_size_code=''):


        content = self.requests_get( album_url)

        div_item_list=parseDOM(content.text, "div", attrs = { "id": "gallery-view-content" })


        if div_item_list:
            thumbs = parseDOM(div_item_list, "img", ret = "src" )
            href   = parseDOM(div_item_list,   "a", ret = "href" )

            images = ('http://i.imgbox.com%s.jpg' %s for s in href)

            list3= map(list,zip( images, thumbs ))

            list3 = [['',i,t] for i,t in list3]


            self.assemble_images_dictList( list3 )
        else:
            log('      %s: cant find <div ... id="gallery-view-content"> '  %(self.__class__.__name__ ) )

        return self.dictList

    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url

class ClassReddit(sitesBase):

    regex='^\/r\/(.+)(?:\/|$)|(^\/u\/)(.+)(?:\/|$)|(reddit\.com)'

    def get_playable_url(self, link_url, is_probably_a_video):
        from reddit import assemble_reddit_filter_string
        subreddit=self.get_video_id(link_url)
        self.video_id=subreddit


        self.media_type=sitesBase.TYPE_REDDIT

        if '/comments/' in link_url:
            self.link_action='listLinksInComment'
            return link_url, self.media_type
        else:

            if subreddit:
                self.link_action='listSubReddit'
                reddit_url=assemble_reddit_filter_string('',subreddit)
                return reddit_url, self.media_type
            if link_url.startswith('/u/'):
                author=link_url.split('/u/')[1]
                self.link_action='listSubReddit'

                reddit_url=assemble_reddit_filter_string("","/user/"+author+'/submitted')
                return reddit_url, self.media_type
        return '',''
    @classmethod
    def get_video_id(self, reddit_url):

        match = re.findall( '^\/?r\/(.+?)(?:\/|$)|https?://.+?\.reddit\.com\/r\/(.+?)(?:\/|$)' , reddit_url)

        if match:
            for m in match[0]:
                if m: #just use the first non-empty match
                    return m

    def get_thumb_url(self):
        headers = {'User-Agent': reddit_userAgent}
        body_text=None
        from utils import clean_str

        if '/comments/' in self.original_url:

            u=self.original_url
            if '?' in self.original_url:
                url=self.original_url.split('?', 1)[0]+'.json?limit=1&'+self.original_url.split('?', 1)[1]
                u=self.original_url.replace('?','/')
            else:
                url=self.original_url+'.json?limit=1'
                if not self.original_url.endswith('/'):
                    u=self.original_url+'/'

            s_count=u.count('/')  #very crude way to determine how many id's in the url is to just count the '/' separators


            if s_count > 8:#this is a comment (t1)
                r = self.requests_get( url, headers=headers)
                j=r.json()
                body_text=clean_str(j,[1,'data','children',0,'data','body']  )
            else:  #this is a post (t3)

                pass

            self.description=body_text

        if self.video_id:

            req='https://www.reddit.com/r/%s/about.json' %self.video_id

            r = self.requests_get( req, headers=headers)
            j=r.json()
            j=j.get('data')

            icon_img=j.get('icon_img')
            banner_img=j.get('banner_img')
            header_img=j.get('header_img')

            icon=next((item for item in [icon_img,header_img,banner_img] if item ), '')

            self.thumb_url=icon
            self.poster_url=banner_img

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

        content = self.requests_get( link_url)

        thumb= parseDOM(content.text, "meta", attrs = { "id": "metaTag" }, ret = "content")

        if thumb:
            self.thumb_url=thumb[0]

        div_item_list = parseDOM(content.text, "div", attrs = { "id": "photo" })

        if div_item_list:
            images = parseDOM(div_item_list, "img", ret = "src")

            if images[0]:
                self.thumb_url = images[0]
                self.poster_url= images[0]

                return self.poster_url, self.TYPE_IMAGE

        div_video = parseDOM(content.text, "div", attrs = { "id": "cuerpo" })

        if div_video:
            vid_thumb = parseDOM(div_video, "video", ret = "poster")

            if vid_thumb:
                self.thumb_url='http://www.kindgirls.com'+vid_thumb[0]
                self.poster_url=self.thumb_url

            self.link_action=sitesBase.DI_ACTION_YTDL
            self.media_type=sitesBase.TYPE_VIDEO
            return link_url, self.media_type

    def ret_album_list(self, album_url, thumbnail_size_code=''):

        content = self.requests_get(album_url)
        images=[]
        div_item_list = parseDOM(content.text, "div", attrs = { "id": "cuerpo" })


        if div_item_list:
            thumb_div=parseDOM(div_item_list, "div", attrs = { "id": "up_der" })

            if thumb_div:

                thumb = parseDOM(thumb_div,"a", ret="href")[0]
                if thumb:
                    self.thumb_url=thumb
                    self.poster_url=self.thumb_url


            img_divs=parseDOM(div_item_list, "div", attrs = { "class": "gal_list" })

            if img_divs:
                for div in img_divs:
                    image_p     = parseDOM(div,"img", ret="src")[0]
                    image_title = parseDOM(div,"img", ret="title")[0]
                    image_o     = parseDOM(div,"a", attrs={ "target":"_blank"}, ret="href")[0]

                    images.append( [image_title, image_o, image_p]  )

            self.assemble_images_dictList( images )


        else:
            log("      can't find div id cuerpo")

        return self.dictList

    def get_thumb_url(self):

        if self.thumb_url:
            return self.thumb_url

        if self.is_album(self.original_url):

            self.ret_album_list( self.original_url )
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

    def get_thumb_url(self):

        self.get_photo_info()

        if self.poster_url:
            return self.poster_url

        return ''

    def get_photo_info(self, photo_url=''):
        if not photo_url:
            photo_url=self.media_url

        self.get_video_id()

        if self.video_id:

            api_url= 'https://api.500px.com/v1/photos/%s?image_size=6&%s' %(self.video_id, self.key_string)

            r = self.requests_get(api_url)


            j=json.loads(r.text)   #.replace('\\"', '\'')
            j=j.get('photo')

            self.poster_url=j.get('image_url')
            self.media_w=j.get('width')  #width and height not accurate unless image size 6  (not sure if applies to all)
            self.media_h=j.get('height')
            self.media_url=self.poster_url

        else:
            log("    %s cannot get videoID %s" %( self.__class__.__name__, self.original_url) )


    def get_playable_url(self, media_url, is_probably_a_video=True ):


        if self.is_album(media_url):
            return media_url, sitesBase.TYPE_ALBUM

        self.get_photo_info()

        if self.poster_url:
            return self.poster_url, sitesBase.TYPE_IMAGE

        return '',''

    def get_video_id(self):
        self.video_id=''

        match = re.findall( '500px\.com/photo/(.+?)(?:\/|$)' , self.original_url)

        if match:
            self.video_id=match[0]

    def ret_album_list(self, album_url, thumbnail_size_code=''):

        result = re.search('500px\.com/(.*?)/(.+)?', self.original_url)
        username  =result.group(1)
        album_name=result.group(2)
        log('    username:%s album:%s' %(username, album_name) )

        api_call='https://api.500px.com/v1/users/show?username=%s&%s' %(username, self.key_string)
        log('    req='+api_call)
        r = self.requests_get(api_call)

        j=r.json()
        user_id=j.get('user').get('id')

        if user_id:

            api_call='https://api.500px.com/v1/users/%s/%s/items?image_size=6&rpp=100&%s' %(user_id, album_name, self.key_string)
            log('    req='+api_call)
            r = self.requests_get(api_call)

            images=[]
            j=r.json()
            j=j.get('photos')
            for photo in j:
                title=photo.get('name')
                description=photo.get('description')
                image=photo.get('image_url')
                width=photo.get('width')
                height=photo.get('height')

                images.append( {'title': title,
                                'description': description,
                                'url': image,
                                'width': width,
                                'height': height,
                                }  )

            self.assemble_images_dictList( images )

        else:
            log("    can't get user id")
            return
        return self.dictList

class ClassSlimg(sitesBase):
    regex='(sli.mg)'

    header={'Authorization': 'Client-ID M5assQr4h9pj1xQNJ6ehAEXuDq27RsYE'}


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

        r = self.requests_get(api_req, headers=self.header)

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


        return self.media_url, self.media_type

    def get_video_id(self):

        self.video_id=''

        match = re.compile('sli\.mg/(?:a/|album/)?(.+)').findall(self.media_url)

        if match:
            self.video_id=match[0]

    def get_thumb_url(self):
        if self.thumb_url:
            return self.thumb_url

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        self.get_video_id()

        api_req='https://api.sli.mg/album/%s/media' % self.video_id

        r = self.requests_get(api_req, headers=self.header)

        j=r.json()
        j=j.get('data')

        images=[]
        for i in j.get('media'):

            title=i.get('title')
            description=i.get('description')
            media_url=i.get('url_direct')
            media_w=i.get('width')
            media_h=i.get('height')


            if i.get('webm'):  #we don't support video in album but still avoid gif video  if possible.
                media_url=j.get('url_webm')

            images.append( {'title': title,
                            'description': description,
                            'url': media_url,
                            'width': media_w,
                            'height': media_h,
                            }  )

        self.assemble_images_dictList(images)

        return self.dictList


class ClassImgTrex(sitesBase):
    SITE='imgtrex'
    regex='(imgtrex.com)'

    include_gif_in_get_playable=True

    def get_playable(self, media_url='', is_probably_a_video=False ):
        if not media_url:
            media_url=self.media_url
        return self.get_playable_url(self.media_url, is_probably_a_video=False )

    def get_playable_url(self, link_url, is_probably_a_video=False ):
        content = self.requests_get(link_url)


        image=parseDOM(content.text, name='img', attrs = { "class": "pic" }, ret="src")

        if image[0]:

            self.set_media_type_thumb_and_action(image[0])
            return self.media_url, self.media_type

    def get_thumb_url(self):
        pass

class ClassImgFlip(sitesBase):
    SITE='imgflip'
    regex='(imgflip.com)'
    include_gif_in_get_playable=True

    def get_playable_url(self, link_url, is_probably_a_video=False ):
        content = self.requests_get(link_url)
        i=parseDOM(content.text, "meta", attrs = { "property": "og:image" }, ret="content" )
        iw=parseDOM(content.text, "meta", attrs = { "property": "og:image:width" }, ret="content" )
        ih=parseDOM(content.text, "meta", attrs = { "property": "og:image:height" }, ret="content" )
        if i:
            image=i[0]
            self.set_media_type_thumb_and_action(image)
            self.media_w=iw[0]
            self.media_h=ih[0]
            return self.media_url,self.media_type
        else:
            log('      %s: cant find <meta property'  %(self.__class__.__name__ ) )

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        return None

    def get_thumb_url(self):
        pass

class ClassSupload(sitesBase):
    regex='(supload.com)'

    def get_playable_url(self, link_url, is_probably_a_video=False ):
        self.media_url=link_url

        html=self.requests_get(link_url)

        meta_og_type=parseDOM(html.text, "meta", attrs = { "property": "og:type" }, ret="content" )
        og_image_list=parseDOM(html.text, "meta", attrs = { "property": "og:image" }, ret="content" )

        if og_image_list:
            og_image=og_image_list[0]
            self.thumb_url=og_image
            self.poster_url=og_image
        else:
            log('      %s: cant find <meta property="og:image" '  %(self.__class__.__name__ ) )

        if meta_og_type:
            meta_og_type=meta_og_type[0]
            if meta_og_type=='image':
                self.media_type=sitesBase.TYPE_IMAGE
                self.media_url=og_image
            elif meta_og_type=='video':
                self.media_type=sitesBase.TYPE_VIDEO
            else:
                log('      unknown meta og type:'+meta_og_type)
        else:
            log('      no meta og type')
            raise Exception("Could not determine media type" )

        section_imageWrapper=parseDOM(html.text, "section", attrs = { "class": "imageWrapper" }, ret=None )

        if section_imageWrapper:
            if meta_og_type=='image':

                img=parseDOM(section_imageWrapper, "img", attrs={}, ret='src' )
                if img:
                    self.set_media_type_thumb_and_action(img[0])
            elif meta_og_type=='video':
                video_url=parseDOM(html.text, "meta", attrs = { "property": "og:video" }, ret="content" )

                if video_url:
                    self.set_media_type_thumb_and_action(video_url[0])

                    if self.is_a_gif(og_image_list):

                        self.media_type=sitesBase.TYPE_GIF

        return self.media_url, self.media_type

    def get_thumb_url(self):
        self.thumb_url=self.media_url
        self.poster_url=self.media_url
        return self.thumb_url

    @classmethod
    def is_a_gif(self, og_image_list):
        for i in og_image_list:
            if '.gif' in i:
                return True
        return False

class ClassAcidcow(sitesBase):
    regex='(acidcow.com)'

    include_gif_in_get_playable=True
    p=['acidcow.com', '', ['div', { "class": "newsarea" },None],
                        ['div', {"class": "fb-like"}, "data-image"]
        ]

    def get_playable_url(self, link_url, is_probably_a_video=False ):
        self.media_url=link_url

        html=self.requests_get(link_url)


        images=self.get_images(html.text,self.p)
        if images:

            self.media_type=self.TYPE_ALBUM
            return self.media_url, self.media_type
        else:

            self.link_action=self.DI_ACTION_YTDL
            return self.media_url, self.TYPE_VIDEO

    def ret_album_list(self, album_url, thumbnail_size_code=''):
        html=self.requests_get(album_url)

        images=self.get_images(html.text,self.p)
        if images:

            self.assemble_images_dictList(images)
            return self.dictList

    def get_images(self, html, p):
        images=[]

        big_div=parseDOM(html, name=p[2][0], attrs=p[2][1], ret=p[2][2])
        if big_div:

            imgs = parseDOM(big_div,name=p[3][0], attrs=p[3][1], ret=p[3][2])

            images.extend(imgs)

        return images

    def get_thumb_url(self):
        self.thumb_url=self.media_url
        self.poster_url=self.media_url
        return self.thumb_url

class genericAlbum1(sitesBase):
    regex='(http://www.houseofsummersville.com/)|(weirdrussia.com)|(cheezburger.com)|(hentailair.xyz)|(designyoutrust.com)'


    ps=[  [ 'houseofsummersville.com', '',          ['div', { "dir": "ltr" },None],
                                                    ['div', { "class": "separator" },None],
                                                    ['a', {}, "href"]
            ],
          [         'weirdrussia.com', '',          ['div', { "class": "thecontent clearfix" },None],
                                                    ['img', {}, "data-layzr"]
            ],
          [         'cheezburger.com', 'no_ext',    ['div', { "class": "nw-post-asset" },None],

                                                    ['img', {}, "src"]
            ],
          [         'hentailair.xyz', '',           ['div', { "class": "box-inner-block" },None],   # with hentailair.xyz->imgtrex the actual image is in  the style attribute of the img tag
                                                    ['a', {}, "style"]                              #  "background-image: url('http://raptor.imgtrex.com/i/01882/gntod25j7lcf_t.jpg'); background-size: cover; background-position: 50% 50%; background-repeat: no-repeat;"
            ],
          [     'designyoutrust.com', '',          ['div', { "class": "mainpost" },None],
                                                    ['img', {}, "src"]
            ],
        ]


    def get_playable_url(self, link_url, is_probably_a_video=False ):
        return link_url, self.TYPE_ALBUM

    def get_thumb_url(self):
        img=self.request_meta_ogimage_content()
        self.thumb_url=img
        self.poster_url=self.thumb_url

    def ret_album_list(self, album_url, thumbnail_size_code=''):


        for p in self.ps:
            if p[0] in album_url:
                break

        html = self.get_html( album_url )
        if html:
            images=self.get_images(html, p)

            self.assemble_images_dictList( images )

        return self.dictList

    def get_images(self, html, p):
        log(    'len %d' %(len(p)) )
        p_options=p[1]
        images=[]
        if len(p)==5:
            div_item_list = parseDOM(html, name=p[2][0], attrs = p[2][1], ret=p[2][2] )

            if div_item_list:

                img_divs=parseDOM(div_item_list, name=p[3][0], attrs=p[3][1], ret=p[3][2])
                if img_divs:

                    for div in img_divs:

                        image_o      = parseDOM(div,name=p[4][0], attrs=p[4][1], ret=p[4][2])

                        if image_o:
                            if p_options=='no_ext':   #don't check for image extensions
                                images.append( image_o[0] )
                            else:
                                if link_url_is_playable( image_o[0] ) == 'image':

                                    images.append( image_o[0] )
        elif len(p)==4:

            big_div=parseDOM(html, name=p[2][0], attrs=p[2][1], ret=p[2][2])
            if big_div:

                imgs = parseDOM(big_div,name=p[3][0], attrs=p[3][1], ret=p[3][2])

                self.append_imgs( imgs, p, images)
        elif len(p)==3:

            imgs=parseDOM(html, name=p[2][0], attrs=p[2][1], ret=p[2][2])
            self.append_imgs( imgs, p, images)

        return images

    def append_imgs(self, imgs, p, images_list):
        p_options=p[1]
        if imgs:
            for i in imgs:

                if i:
                    i=self.get_first_url_from(i)   # this is added for hentailair.xyz the actual image is in the style attribute of the img tag. probably fine for others

                    if p_options=='no_ext':   #don't check for image extensions
                        images_list.append( i )
                    else:
                        if link_url_is_playable( i ) == 'image':
                            images_list.append( i )

class genericImage(sitesBase):
    regex='(Redd.it/)|(RedditUploads)|(RedditMedia)|(\.(jpg|jpeg|png|gif)(?:\?|$))'

    def get_playable_url(self, link_url, is_probably_a_video=False ):
        media_url=link_url.replace('&amp;','&')  #this replace is only for  RedditUploads but seems harmless for the others...
        self.media_url=media_url

        u=media_url.split('?')[0]
        self.set_media_type_thumb_and_action(u,
                                             default_type=self.TYPE_IMAGE,
                                             default_action='')

        return media_url, self.media_type

    def get_thumb_url(self):
        self.thumb_url=self.media_url
        self.poster_url=self.media_url
        return self.thumb_url

class genericVideo(sitesBase):
    regex='(\.(mp4|webm|avi|3gp|gif|MPEG|WMV|ASF|FLV|MKV|MKA)(?:\?|$))'
    def get_thumb_url(self):
        pass

    def get_playable(self, link_url='', is_probably_a_video=False ):
        if not link_url:
            link_url=self.media_url

        self.set_media_type_thumb_and_action(link_url)
        if url_resolver_support(link_url):
            self.link_action=self.DI_ACTION_URLR
            self.media_type=self.TYPE_VIDEO

        return self.media_url,self.media_type

    def get_playable_url(self, link_url, is_probably_a_video):
        pass


class LinkDetails():
    def __init__(self, media_type, link_action, playable_url='', thumb='', poster='', poster_w=0, poster_h=0, dictlist=None, description='' , video_id=''):

        self.playable_url = playable_url
        self.media_type = media_type
        self.link_action = link_action
        self.thumb = thumb
        self.poster = poster
        self.poster_w = poster_w
        self.poster_h = poster_h
        self.dictlist = dictlist #for img albums
        self.desctiption=description #for text gathered from link to present to the user. (r/bestof comment body for now)
        self.video_id=video_id   #for youtube video id

def sitesManager( media_url ):

    shorteners=['bit.ly','goo.gl','tinyurl.com']
    if any(shortener in media_url for shortener in shorteners):

        v = requests.head( media_url, timeout=REQUEST_TIMEOUT, allow_redirects=True )
        log('  short url(%s)=%s'%(media_url,repr(v.url)))
        media_url=v.url

    for subcls in sitesBase.__subclasses__():
        regex=subcls.regex
        if regex:
            match=re.compile( regex  , re.I).findall( media_url )
            if match :
                return subcls( media_url )

def parse_reddit_link(link_url, assume_is_video=True, needs_preview=False, get_playable_url=False, image_ar=0 ):
    if not link_url: return

    album_dict_list=None
    hoster = sitesManager( link_url )


    try:
        if hoster:
            hoster.dictList=[]  #make sure the dictlist is empty otherwise we end up appending for every post
            if get_playable_url:
                pass

            prepped_media_url, media_type = hoster.get_playable(link_url, assume_is_video)

            if not prepped_media_url:
                log("  Failed to parse %s" %(link_url) )

            if needs_preview:
                hoster.get_thumb_url()

            if not hoster.link_action:
                if media_type==sitesBase.TYPE_IMAGE:
                    if image_ar>0 and image_ar < 0.4: #special action for tall images
                        hoster.link_action='viewTallImage'
                    else:
                        hoster.link_action='viewImage'

                if media_type==sitesBase.TYPE_ALBUM:
                    album_dict_list=hoster.dictList
                    hoster.link_action='listAlbum'

            ld=LinkDetails(media_type, hoster.link_action, prepped_media_url, hoster.thumb_url, hoster.poster_url, dictlist=album_dict_list,description=hoster.description  )
            return ld

        else:
            if url_resolver_support(link_url):
                ld=LinkDetails(sitesBase.TYPE_VIDEO, sitesBase.DI_ACTION_URLR, link_url, '', '')
                return ld

            if False: #resolve_undetermined:  (abandoned, too slow)
                log('sending undetermined link to ytdl...')
                media_url=ydtl_get_playable_url(link_url)
                if media_url:
                    ld=LinkDetails(sitesBase.TYPE_VIDEO, sitesBase.DI_ACTION_PLAYABLE, media_url[0], '', '')
                    return ld

    except Exception as e:
        log("  EXCEPTION parse_reddit_link "+ str( sys.exc_info()[0]) + " - " + str(e) )
        ld=LinkDetails('', sitesBase.DI_ACTION_ERROR, str(e) )
        return ld



def ydtl_get_playable_url( url_to_check ):
    from resources.lib.utils import link_url_is_playable
    from default import YDStreamExtractor

    if link_url_is_playable(url_to_check)=='video':
        return url_to_check

    choices = []

    if YDStreamExtractor.mightHaveVideo(url_to_check,resolve_redirects=True):

        vid = YDStreamExtractor.getVideoInfo(url_to_check,0,True)  #quality is 0=SD, 1=720p, 2=1080p and is a maximum
        if vid:

            if vid.hasMultipleStreams():

                log("          video hasMultipleStreams %d" %len(vid._streams) )
                for s in vid.streams():
                    title = s['title']

                    choices.append(s['xbmc_url'])


            choices.append(vid.streamURL())
            return choices

    return None

if __name__ == '__main__':
    pass

def build_DirectoryItem_url_based_on_media_type(ld, url, arg_name='', arg_type='', script_to_call="", on_autoplay=False, img_w=0, img_h=0):
    setProperty_IsPlayable='false'  #recorded in vieoxxx.db if set to 'true'
    isFolder=True
    DirectoryItem_url=''
    title_prefix=''
    url='' if url==None else url.decode('unicode_escape').encode('ascii','ignore')
    arg_name=arg_name.encode('utf-8')             #sometimes we pass the title of the post on &name=. need to encode('utf-8') here otherwise we get a keyError
    if ld:
        if ld.media_type==sitesBase.TYPE_IMAGE:
            if addon.getSetting("hide_IMG") == "true": return
            title_prefix='[IMG]'
            isFolder=False
            if ld.link_action=='viewTallImage':  #viewTallImage uses/needs the name and type arg to hold the image width and height
                arg_name=str(img_w)
                arg_type=str(img_h)

        elif ld.media_type==sitesBase.TYPE_ALBUM:
            if addon.getSetting("hide_IMG") == "true": return
            title_prefix='[ALBUM]'
            isFolder=True

        elif ld.media_type==sitesBase.TYPE_REDDIT:
            if addon.getSetting("hide_reddit") == "true": return
            title_prefix='[Reddit]'
            isFolder=True

        elif ld.media_type==sitesBase.TYPE_VIDEO:
            if addon.getSetting("hide_video") == "true": return
            setProperty_IsPlayable='true'
            isFolder=False


        elif ld.media_type==sitesBase.TYPE_VIDS:
            if addon.getSetting("hide_video") == "true": return

            title_prefix='[ALBUM]'   #treat link with multiple video as album
            ld.link_action='listAlbum'
            isFolder=True

        elif ld.media_type==sitesBase.TYPE_GIF:
            if addon.getSetting("hide_video") == "true": return
            if on_autoplay:

                pass
            else:
                ld.link_action = 'loopedPlayback'
                setProperty_IsPlayable='false'

                isFolder=False

        elif ld.media_type=='' or ld.media_type==None:  #ld.link_action=sitesBase.DI_ACTION_ERROR

            setProperty_IsPlayable='false'
            isFolder=False

        if ld.link_action == sitesBase.DI_ACTION_PLAYABLE:
            setProperty_IsPlayable='true'
            isFolder=False
            DirectoryItem_url=ld.playable_url
        else:
            DirectoryItem_url=sys.argv[0]\
            +"?url="+ urllib.quote_plus(ld.playable_url) \
            +"&mode="+urllib.quote_plus(ld.link_action) \
            +"&name="+urllib.quote_plus(arg_name) \
            +"&type="+urllib.quote_plus(arg_type)
    else:
        if addon.getSetting("hide_undetermined") == "true": return
        title_prefix='[?]'

        setProperty_IsPlayable='true'  #pluginhandle=-1 if set to 'false' and isFolder set to False
        isFolder=False                 #isFolder=True avoids the WARNING: XFILE::CFileFactory::CreateLoader /  ERROR: InputStream: Error opening, ...
        DirectoryItem_url=sys.argv[0]\
        +"?url="+ urllib.quote_plus(url) \
        +"&name="+urllib.quote_plus(arg_name) \
        +"&mode=playYTDLVideo"

    return DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix

'''

class hosterBase(object):

    def __init__(self, url):
        self.url = url

    @classmethod
    def from_url(cls, url):
        for subclass in cls.__subclasses__():
            if subclass.recc.match(url):
                return subclass(url)



class cVidme(hosterBase):
    regex = 'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]*)'
    recc=re.compile(regex)

class b(hosterBase):
    regex = 'bbb'
    recc=re.compile(regex)


    m = hosterBase.from_url(media_url)
    log("  "+str(m))
    if m:
        a = m.get_playable_url(media_url, assume_is_video)
        log("  " + a)



'''
