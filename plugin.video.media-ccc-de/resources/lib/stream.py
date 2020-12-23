# coding: utf-8
from __future__ import print_function, division, absolute_import

from .helpers import user_preference_sorter


class Streams(object):
    def __init__(self, json):
        self.conferences = []
        for conference in json:
            self.conferences.append(Conference(conference))


class Conference(object):
    def __init__(self, json):
        self.rooms = []
        # Ignore groups for now
        for group in json['groups']:
            self.rooms += [Room(elem, group['group'])
                           for elem in group['rooms']]
        self.slug = json["slug"]
        self.name = json["conference"]


class Room(object):
    def __init__(self, json, group=''):
        self.streams = []
        for stream in json["streams"]:
            if len(stream["urls"]) > 0:
                for urlname, urldata in stream["urls"].items():
                    self.streams.append(Stream(urlname, urldata, stream))
        self.slug = json["slug"]
        self.display = json["display"]
        if len(group) > 0:
            self.display = group + ": " + self.display

    def streams_sorted(self, quality, format, dash=False, video=True):
        print("Requested quality %s and format %s" % (quality, format))
        typematch = ('video', 'dash') if video else ('audio', )
        want = sorted(filter(lambda stream: stream.type in typematch,
                             self.streams),
                      key=user_preference_sorter(quality, format, dash))
        return want


class Stream(object):
    def __init__(self, name, data, stream):
        self.format = name
        if self.format == 'hls':
            self.format = 'mp4'
        self.hd = None
        if stream['videoSize'] is not None:
            self.hd = stream['videoSize'][0] >= 1280
        self.url = data['url']
        self.translated = stream['isTranslated']
        self.type = stream['type']

    def __repr__(self):
        return '<Stream: %s, hd: %s, type: %s, trans: %s>' % (
            self.format, self.hd, self.type, self.translated)
