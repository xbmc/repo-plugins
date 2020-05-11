#!/usr/bin/python
# -*- coding: utf-8 -*-


class Episode:
    def __init__(self, cms_id, title, description, files, item_type, thumbnail, backdrop, station, logo, hidden=0, meta=None):
        if meta is None:
            meta = []
        self.hidden = hidden
        self.id = cms_id
        self.title = title
        self.description = description
        self.files = files
        self.thumbnail = thumbnail
        self.item_type = item_type
        self.backdrop = backdrop
        self.station = station
        self.logo = logo
        self.full_title = ""
        self.time = ""
        self.duration = 0
        self.trackname = ""
        self.artist = ""
        self.meta = meta
        if self.meta and len(self.meta):
            if 'trackname' in self.meta:
                self.trackname = self.meta['trackname']
            if 'artist' in meta:
                self.artist = self.meta['artist']
            if 'duration' in self.meta:
                self.duration = self.meta['duration']
            if 'start' in self.meta:
                self.time = self.meta['start']
            if 'end' in self.meta:
                self.time += " - %s" % self.meta['end']