# -*- coding: utf-8 -*-

import re
import threading

from .cache import Cache,Hide_List
from .filter_list import filter_list

class Videos:

    def __init__(self, plugin):
        self.plugin = plugin
        self.sites = self.plugin.sites()

    def get_videos(self, artist):
        videos = []
        result = []
        threads = []
        for site in self.sites:
            threads.append(
                threading.Thread(
                    target = self.videos_thread,
                    args = (site, artist, result)
                )
            )

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for r in result:
            for v in r:
                videos.append(v)
        videos = self.filter_videos(videos)
        videos = self.sort_videos(videos)
        videos = self.remove_duplicates(videos)
        return videos

    def videos_thread(self, site, artist, result):
        video_list = []
        cache = Cache(self.plugin)
        video_list = cache.get_value(site, artist)
        if video_list == None:
            video_list = self.plugin.import_site(site, self.plugin).get_videos(artist)
            cache.save_value(site, artist, video_list)
        result.append(video_list)
        return result

    def remove_duplicates(self, videos):
        all_ids = [ self.clean(i['title'].lower()) for i in videos ]
        videos = [ videos[ all_ids.index(id) ] for id in set(all_ids) ]
        return videos

    def clean(self, title):
        if '|' in title:
            title = title.split('|')[0]
        title = self.plugin.utfdec(title)
        title = re.sub('\\x92|\\xe2\\x80\\x98', '', title)
        title = self.plugin.utfenc(title)
        title = re.sub(' and | und |(?:^|\s)der |(?:^|\s)die |(?:^|\s)das |(?:^|\s)the ','', title)
        title = re.sub('[(]feat.*?$|[(]ft.*?$|( ft(.| ).*?$)|[(]with .*?[)]| feat. .*?$','', title)
        title = re.sub('extended version|extended video', 'extended', title)
        title = re.sub('\s|\n|([[])|([]])|\s(vs|v[.])\s|(:|;|-|\+|\~|\*|"|\'|,|\.|\?|\!|\=|\&|/)|([(])|([)])', '', title)
        return title

    def sort_videos(self, videos):
        sorted_video_list = []
        for site in self.sites:
            for video in videos:
                video_site = video['site']
                if video_site == site:
                    video['title'] = self.plugin.clean_title(video['title'])
                    sorted_video_list.append(video)  
        return sorted_video_list

    def filter_videos(self, videos):
        for f in filter_list:
            videos = [x for x in videos if not re.findall((f), self.plugin.utfenc(x['title']), re.IGNORECASE)]
        videos = [x for x in videos if not re.findall(self.plugin.utfenc(x['artist']), self.plugin.utfenc(x['title']), re.IGNORECASE)]
        hide_list = Hide_List(self.plugin).get_hide_list()
        for i in hide_list:
            videos = [x for x in videos if not (str(i['id']) == str(x['id']) and i['site'] == x['site'])]
        return videos
