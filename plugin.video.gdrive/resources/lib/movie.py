'''
    Copyright (C) 2014-2016 ddurdle

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
import urllib
import re
import file


#
#
#
class movie(file):
    # CloudService v0.3


    ##
    ##
    def __init__(self, title, year, type, rating=None, genre=None, plot=None, thumbnail=None, fanart=None, country=None, set=None, director=None, authors=None):
        File.__init__(self,'', title, plot, type, fanart,thumbnail, date='', size=0, resolution=None, playcount=0, duration=-1, download='', checksum='')
        self.year = year
        self.rating = rating
        self.genre = genre
        self.plot = plot
        self.country = country
        self.set = set
        self.director = director
        self.authors = authors

    def __repr__(self):
        return '{}: {} {}'.format(self.__class__.__name__,
                                  self.title)

    def __cmp__(self, other):
        if hasattr(other, 'title'):
            return self.title.__cmp__(other.title)

    def getKey(self):
        return self.title
