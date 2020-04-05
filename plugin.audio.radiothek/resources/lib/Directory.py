#!/usr/bin/python
# -*- coding: utf-8 -*-


class Directory:
    def __init__(self, title, description, link, thumbnail, backdrop, station, logo):
        self.title = title
        self.description = description.strip()
        self.link = link
        self.thumbnail = thumbnail
        self.backdrop = backdrop
        self.station = station
        self.logo = logo

