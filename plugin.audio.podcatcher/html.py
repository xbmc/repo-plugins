# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.audio.PodCatcher - A plugin to play Podcasts
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

def transformHtmlCodes(string):
  replacements = (
    (u'Ä', u'&Auml;'),
    (u'Ü', u'&Uuml;'),
    (u'Ö', u'&Ouml;'),
    (u'ä', u'&auml;'),
    (u'ü', u'&uuml;'),
    (u'ö', u'&ouml;'),
    (u'ß', u'&szlig;'),
    (u'\"',u'&#034;'),
    (u'\"',u'&quot;'),
    (u'\'',u'&#039;'),
    (u'&', u'&amp;')
  )
  for replacement in replacements:
    string = string.replace(replacement[1],replacement[0]);
  return string;
