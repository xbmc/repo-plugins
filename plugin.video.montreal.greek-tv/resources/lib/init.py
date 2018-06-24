# -*- coding: utf-8 -*-

'''
    Montreal Greek TV Add-on
    Author: greektimes

        License summary below, for more details please read license.txt file

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from __future__ import absolute_import, division, unicode_literals

from sys import argv
from resources.lib.compat import parse_qsl

syshandle = int(argv[1])
sysaddon = argv[0]
params_tuple = parse_qsl(argv[2].replace('?',''))
params = dict(params_tuple)
action = params.get('action')
url = params.get('url')
image = params.get('image')

__all__ = ["syshandle", "sysaddon", "params", "action", "url", "image"]
