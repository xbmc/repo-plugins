# coding: utf-8
from __future__ import print_function, division, absolute_import

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from .helpers import maybe_json


class Relives(object):
    def __init__(self, json):
        self.recordings = [ReliveItem(elem) for elem in json]

    def by_conference(self, conf):
        items = list(filter(lambda x: x.project == conf, self.recordings))
        # assumption: there is at most one entry per project
        return items[0] if len(items) == 1 else None


class ReliveItem(object):
    def __init__(self, json):
        self.index_url = json['index_url']
        self.project = json['project']

    def get_url(self):
        return urlparse(self.index_url, 'https').geturl()


class ReliveRecordings(object):
    def __init__(self, json):
        self.recordings = [ReliveRecording(el) for el in json]

    def unreleased(self):
        return list(filter(lambda rec: rec.mp4 != '', self.recordings))


class ReliveRecording(object):
    def __init__(self, json):
        self.duration = maybe_json(json, 'duration', 0)
        self.mp4 = maybe_json(json, 'mp4', '')
        self.thumbnail = maybe_json(json, 'thumbnail', '')
        self.room = maybe_json(json, 'room', '')
        self.title = json['title']

    def get_video_url(self):
        return urlparse(self.mp4, 'https').geturl()

    def get_thumb_url(self):
        return urlparse(self.thumbnail, 'https').geturl()
