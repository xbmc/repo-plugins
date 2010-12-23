# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.gamestar - Downloads/view videos from gamestar.de
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
class VideoObject(object):
  def __init__(self,title,url,picture):
    self.title = title
    self.url = url
    self.picture = picture

class GalleryObject(object):
  def __init__(self,index,title,url,picture,rootLink):
    self.index = index
    self.title = title
    self.url = url
    self.picture = picture
    self.rootLink = rootLink
