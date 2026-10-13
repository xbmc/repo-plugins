#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Constants for the DR API endpoints, channels and content areas."""

CHANNEL_IDS = [20875, 20876, 192099, 192100, 20892]
CHANNEL_PRESET = {
    'DR1': 1,
    'DR2': 2,
    'DR Ramasjang': 3,
    'TVA Live': 4,
    'DRTV Ekstra': 5
}
URL = 'https://production.dr-massive.com/api'
CLIENT_ID = '283ba39a2cf31d3b81e922b8'
GET_TIMEOUT = 10
A_AA = {
    'ramasjang': '/ramasjang_a-aa',
    'minisjang': '/minisjang/a-aa',
    'ultra': '/ultra_a-aa',
    'drtv': '/kategorier/a-aa',
    'gensyn': '/gensyn/a-aa',
}
