# -*- coding: utf-8 -*-
# -------------LicenseHeader--------------
# plugin.video.Mediathek - Gives access to most video-platforms from German public service broadcasters
# Copyright (C) 2010  Raptor 2101 [raptor2101@gmx.de]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 
from mediathek.ard import *
from mediathek.zdf import *
from mediathek.arte import *
from mediathek.dreisat import *
from mediathek.kika import *


class MediathekFactory(object):
    def __init__(self):
        self.avaibleMediathekes = {
            ARDMediathek.name(): ARDMediathek,
            ZDFMediathek.name(): ZDFMediathek,
            ARTEMediathek.name(): ARTEMediathek,
            DreiSatMediathek.name(): DreiSatMediathek,
            # ORFMediathek.name():ORFMediathek,
            # NDRMediathek.name():NDRMediathek,
            KIKA.name(): KIKA
        }

    def getAvaibleMediathekTypes(self):
        return sorted(self.avaibleMediathekes.keys())

    def getMediathek(self, mediathekName, gui):
        return self.avaibleMediathekes[mediathekName](gui)
