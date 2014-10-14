import os
import random
import shutil
import urllib2
import urlparse
from xml.etree import ElementTree

import xbmc
from xbmc import PLAYLIST_MUSIC


__author__ = 'Oderik'


class Channel(object):
    def prepare_cache(self):
        self.ensure_dir(self.cache_dir)
        if not os.path.exists(self.version_file_path):
            with open(self.version_file_path, 'w') as version_file:
                version_file.write(self.get_simple_element("updated"))

    def cleanup_cache(self):
        if os.path.exists(self.version_file_path):
            with open(self.version_file_path) as version_file:
                cached_version = version_file.read()
                if cached_version != self.get_simple_element("updated"):
                    version_file.close()
                    shutil.rmtree(self.cache_dir, True)

    def __init__(self, handle, cache_dir, source=ElementTree.Element("channel"), quality_priority=None,
                 format_priority=None, firewall_mode=False):
        self.handle = handle
        self.source = source
        self.cache_dir = os.path.join(cache_dir, self.getid())
        self.version_file_path = os.path.join(self.cache_dir, "updated")
        self.cleanup_cache()
        self.prepare_cache()
        self.quality_priority = quality_priority
        self.format_priority = format_priority
        if not self.format_priority:
            self.format_priority = ['mp3', 'aac']
        if not self.quality_priority:
            self.quality_priority = ['fastpls', 'highestpls', 'slowpls']
        self.firewall_mode = firewall_mode

    def get_simple_element(self, *tags):
        for tag in tags:
            element = self.source.find('.//' + tag)
            if element is not None:
                return element.text

    def __repr__(self):
        return "{}: {} ({}, {}, {})".format(self.__class__.__name__, self.getid(),
                                            self.quality_priority, self.format_priority, self.firewall_mode)

    def get_prioritized_playlists(self):
        playlists = []
        for playlist_tag in self.quality_priority:
            for format in self.format_priority:
                for playlist_element in self.source.findall(playlist_tag):
                    format_attrib = playlist_element.attrib['format']
                    if format in format_attrib:
                        playlists.append((playlist_tag, format_attrib, playlist_element.text))
        return playlists

    def getid(self):
        return self.source.attrib['id']

    def ensure_dir(self, filepath):
        if not os.path.exists(filepath):
            os.makedirs(filepath)

    def get_playlist_file(self, playlist_url):
        url_path = urlparse.urlparse(playlist_url).path
        filename = os.path.split(url_path)[1]
        filepath = os.path.join(self.cache_dir, filename)
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            response = urllib2.urlopen(playlist_url)
            self.prepare_cache()
            with open(os.path.abspath(filepath), "w") as playlist_file:
                playlist_file.write(response.read())
            response.close()
        return filepath

    def get_content_url(self):
        for playlist_meta in self.get_prioritized_playlists():
            print "Trying " + str(playlist_meta)
            filepath = self.get_playlist_file(playlist_meta[2])
            play_list = xbmc.PlayList(PLAYLIST_MUSIC)
            play_list.load(filepath)
            streams = []
            for i in range(0, play_list.size()):
                stream_url = play_list.__getitem__(i).getfilename()
                if (urlparse.urlparse(stream_url).port is None) == self.firewall_mode:
                    streams.append(stream_url)
                    print "Accepting " + stream_url
                else:
                    print "Rejecting " + stream_url
            if len(streams) > 0:
                return random.choice(streams)

    def getthumbnail(self):
        return self.get_simple_element('xlimage', 'largeimage', 'image')


    def geticon(self):
        return self.get_simple_element('largeimage', 'xlimage', 'image')
