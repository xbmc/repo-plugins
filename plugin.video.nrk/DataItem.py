# -*- coding: utf-8 -*-
'''
    NRK plugin for XBMC
    Copyright (C) 2010 Thomas Amland

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

class DataItem:
    def __init__(self, title="", description="", date="", author="", category="", thumb="", thumbBig="", url="", isPlayable=False):
        self._title = title
        self._description = description
        self._date = date
        self._author = author
        self._category = category
        self._thumb = thumb
        self._thumbBig = thumbBig
        self._url = url
        self._isPlayable = isPlayable
    
    @property
    def isPlayable(self):
        return self._isPlayable
    
    @property
    def title(self):
        return self._title
    
    @property
    def description(self):
        return self._description
    
    @property
    def date(self):
        return self._date
    
    @property
    def author(self):
        return self._author
    
    @property
    def category(self):
        return self._category
    
    @property
    def thumb(self):
        return self._thumb
    
    @property
    def thumbBig(self):
        return self._thumbBig
    
    @property
    def url(self):
        return self._url
