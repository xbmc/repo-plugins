# coding: utf-8
from __future__ import print_function, division, absolute_import

from .helpers import user_preference_sorter, maybe_json
from .kodi import log


class Recordings(object):
    def __init__(self, json):
        self.recordings = [Recording(elem) for elem in json['recordings']]

    def recordings_sorted(self, quality, format, video=True):
        log('Requested quality %s and format %s' % (quality, format))
        typematch = "video" if video else "audio"
        want = sorted(filter(lambda rec: (rec.type == typematch
            and not rec.folder.startswith('slides')),
            self.recordings),
            key=user_preference_sorter(quality, format))
        log(str(want))
        return want


class Recording(object):
    def __init__(self, json):
        self.mime = maybe_json(json, 'mime_type', 'video/mp4')
        self.type, self.format = self.mime.split('/')
        self.hd = maybe_json(json, 'high_quality', True)
        self.url = json['recording_url']
        self.length = maybe_json(json, 'length', 0)
        self.size = maybe_json(json, 'size', 0)
        self.folder = maybe_json(json, 'folder', '')
        lang = maybe_json(json, 'language', 'unk')
        if lang:
            self.languages = lang.split('-')
        else:
            self.languages = ('unk',)

    def __repr__(self):
        return "Recording<M:%s,HD:%s,LANG:%s>" % (self.mime, self.hd,
                                                  self.languages)

    def is_video(self):
        return self.type == 'video'

    def is_audio(self):
        return self.type == 'audio'
