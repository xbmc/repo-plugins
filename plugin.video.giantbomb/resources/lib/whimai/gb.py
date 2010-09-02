# WhiMai v1.0.0 - A Python interface for Whiskey Media sites
# Copyright (C) 2010 Anders Bugge
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Contact Info
# E-Mail: whimais@gmail.com

# Thanks To
# http://www.whiskeymedia.com/
# http://www.giantbomb.com/
# http://www.comicvine.com/

import wm

site = "giantbomb.com"
api_key = "0a204c5b48872c635a858970050ec807c381b13e"

class Detail(wm.DetailBase):
    def __init__(self,name):
        wm.DetailBase.__init__(self, name, site, api_key)

class List(wm.ListBase):
    def __init__(self,name):
        wm.ListBase.__init__(self, name, site, api_key)
