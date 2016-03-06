from __future__ import print_function

from .helpers import user_preference_sorter


class Streams(object):
    def __init__(self, json):
        self.rooms = []
        # Ignore groups for now
        for group in json:
            self.rooms += [Room(elem, group['group'])
                           for elem in group['rooms']]


class Room(object):
    def __init__(self, json, group=''):
        self.streams = []
        for stream in json["streams"]:
            for urlname, urldata in stream["urls"].items():
                self.streams.append(Stream(urlname, urldata, stream))
        self.slug = json["slug"]
        self.display = json["display"]
        if len(group) > 0:
                self.display = group + ": " + self.display

    def streams_sorted(self, quality, format, video=True):
        print("Requested quality %s and format %s" % (quality, format))
        typematch = "video" if video else "audio"
        want = sorted(filter(lambda stream: stream.type == typematch,
                             self.streams),
                      key=user_preference_sorter(quality, format))
        return want


class Stream(object):
    def __init__(self, name, data, stream):
        self.format = name
        if self.format == 'hls':
            self.format = 'mp4'
        if stream['videoSize'] != None:
            self.hd = stream['videoSize'][0] >= 1280
        self.url = data['url']
        self.translated = stream['isTranslated']
        self.type = stream['type']
