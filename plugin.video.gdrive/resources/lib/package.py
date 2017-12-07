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

#
#
#
class package:
    # CloudService v0.2.0

    ##
    ##
    def __init__(self, file, folder):
        self.sortTitle = ''
        try:
            if file.title != '':
                self.sortTitle = file.title
            else:
                self.sortTitle = folder.title
        except:
            self.sortTitle = folder.title
        self.file = file
        self.folder = folder
        self.mediaurl = None

    def setMediaURL(self,mediaurl):
        self.mediaurl = mediaurl

    def getMediaURL(self):
        return self.mediaurl.url

    def __repr__(self):
        return '{}: {} {}'.format(self.__class__.__name__,
                                  self.sortTitle)

    def __cmp__(self, other):
        if hasattr(other, 'sortTitle'):
            return (cmp(self.sortTitle, other.sortTitle))

    def getKey(self):
        return self.sortTitle
