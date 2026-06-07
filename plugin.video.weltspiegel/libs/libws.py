# -*- coding: utf-8 -*-

# Copyright 2022 Christian Prasch
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
#
# This file is derived from libard.py from sarbes
# https://github.com/sarbes/script.module.libard

from libs import libparser
from libs.libparser import addon
from libmediathek4 import lm4

ADDON_ID = 'plugin.video.weltspiegel'

parser = libparser.parser()

language = addon.getLocalizedString
strings = { 'Shows':            language(30100),
            'ShowsDesc':        language(30101),
            'Reportage':        language(30102),
            'ReportageDesc':    language(30103),
            'Extras':           language(30104),
            'ExtrasDesc':       language(30105),
            'Videos':           language(30106),
            'VideosDesc':       language(30107),
            'All':              language(30108),
            'AllDesc':          language(30109)
}
        
class libws(lm4):
    def __init__(self):
        lm4.__init__(self)
        self.defaultMode = 'ListSelection'

        self.modes.update({
            'ListSelection':self.ListSelection,
            'ListMain':self.ListMain,
        })
        
        self.searchModes = {
            'ListSearch': self.ListSearch,
        }

        self.playbackModes = {
            'Play':self.Play,
        }

    def ListSelection(self):
        fan = 'special://home/addons/' + ADDON_ID + '/resources/fanart.jpg'
        thumb = 'special://home/addons/' + ADDON_ID + '/resources/icon.png'
        l = [
            {
                'metadata':{'name':strings['Shows'], 'plotoutline':strings['ShowsDesc'], 'content':'Servus','art':{'fanart':fan,   'thumb':thumb}},
                'params':{'mode':'ListMain', 'select':'shows'},
                'type':'dir'
            },
            {
                'metadata':{'name':strings['Reportage'], 'plotoutline':strings['ReportageDesc'], 'art':{'fanart':fan,   'thumb':thumb}},
                'params':{'mode':'ListMain', 'select':'report'},
                'type':'dir'
            },
            {
                'metadata':{'name':strings['Extras'], 'plotoutline':strings['ExtrasDesc'], 'art':{'fanart':fan, 'thumb':thumb}},
                'params':{'mode':'ListMain', 'select':'extra'},
                'type':'dir'
            },
            {
                'metadata':{'name':strings['Videos'], 'plotoutline':strings['VideosDesc'], 'art':{'fanart':fan, 'thumb':thumb}},
                'params':{'mode':'ListMain', 'select':'videos'},
                'type':'dir'
            },
            {
                'metadata':{'name':strings['All'], 'plotoutline':strings['AllDesc'], 'art':{'fanart':fan,   'thumb':thumb}},
                'params':{'mode':'ListMain', 'select':'all'},
                'type':'dir'
            }
        ]

        return {'items':l,'name':'root'}
    
    def ListMain(self):
        return parser.parseDefaultPage('daserste',self.params['select'])
        
    def Play(self):
        return parser.parseVideo(self.params['id'])

    def ListSearch(self,searchString):
        return parser.parseSearchVOD(self.params['client'],searchString)
        