# -*- coding: utf-8 -*-

import xbmc
import xbmcvfs
import json
import os
import re

class LOCAL:

    def __init__(self, plugin):
        self.plugin = plugin
        self.SITE = 'local'

    def get_videos(self, name):
        videos = []
        if self.plugin.get_setting('video_source') == '0':
            videos = self.get_videos_from_library(name)
        else:
            if self.plugin.utfenc(self.plugin.get_setting('video_path')):
                videos = self.get_videos_from_folder(name)
        return videos

    def get_video_url(self, id_):
        return id_

    def get_videos_from_library(self, name):
        videos = []
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": { "properties": [ "title", "artist", "runtime", "file", "streamdetails", "thumbnail" ] }, "id": "libMusicVideos"}')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        if json_response.has_key('result') and json_response['result'] != None and json_response['result'].has_key('musicvideos'):
            for mv in json_response['result']['musicvideos']:
                artist = self.plugin.utfenc(mv['artist'][0])
                title = self.plugin.utfenc(mv['title'])
                id_ = self.plugin.utfenc(mv['file'])
                duration = mv['runtime']
                image = mv['thumbnail']
                if artist.lower() == name.lower():
                    videos.append(
                        {
                            'site': self.SITE,
                            'artist': artist,
                            'title': title,
                            'duration': duration,
                            'id': id_,
                            'thumb': image
                        }
                    )
        return videos

    def get_videos_from_folder(self, name):
        video_path = self.plugin.utfenc(self.plugin.get_setting('video_path'))
        videos = []
        dirs, files = xbmcvfs.listdir(video_path)
        for d in dirs:
            path = os.path.join(video_path, d)
            videos = self.add_videos(name, path, videos)
        videos = self.add_videos(name, video_path, videos)
        return videos

    def add_videos(self, name, path, videos):
        dirs, files = xbmcvfs.listdir(path)
        for f in files:
            if f.endswith(('.strm','.webm','.mkv','.flv','.vob','.ogg','.avi','.mov','.qt','.wmv','.rm','.asf','.mp4','.m4v','.mpg','.mpeg','.3gp')):
                id_ = os.path.join(path, f)
                filename = os.path.splitext(os.path.basename(id_))[0]
                filename = re.sub('\_|\.', ' ', filename)
                match = filename.split(' - ')
                if len(match) == 1:
                    match = filename.split('-')
                if len(match) > 1:
                    artist = match[0].strip()
                    title = match[1].strip()
                    if artist.lower() == name.lower():
                        videos.append(
                            {
                                'site': self.SITE,
                                'artist': self.plugin.utfenc(artist),
                                'title': self.plugin.utfenc(title),
                                'duration': '',
                                'id': id_,
                                'thumb': ''
                            }
                        )
        return videos
