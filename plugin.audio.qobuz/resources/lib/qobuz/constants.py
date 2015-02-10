#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.

__debugging__ = 0

class __Mode():

    def __init__(self):
        self.VIEW = 1
        self.PLAY = 2
        self.SCAN = 3
        self.VIEW_BIG_DIR = 4

    def to_s(self, mode):
        if mode == self.VIEW:
            return "view"
        elif mode == self.PLAY:
            return "play"
        elif mode == self.SCAN:
            return "scan"
        elif mode == self.VIEW_BIG_DIR:
            return "view big dir"
        else:
            return "Unknow mode: " + str(mode)

Mode = __Mode()
