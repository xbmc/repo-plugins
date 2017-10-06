# -*- coding: utf-8 -*-
# Wakanim - Watch videos from the german anime platform Wakanim.tv on Kodi.
# Copyright (C) 2017 MrKrabat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import urllib


def parse_args():
    """Decode arguments.
    """
    if (sys.argv[2]):
        return Args(**dict([p.split("=")
                                for p in sys.argv[2][1:].split("&")]))

    else:
        # Args will turn the "None" into None.
        # Don't simply define it as None because unquote_plus in updateArgs
        # will throw an exception.
        # This is a pretty ugly solution.
        return Args(mode = "None",
                    url  = "None",
                    name = "None")


class Args(object):
    """Arguments class.
    Hold all arguments passed to the script and also persistent user data and
    reference to the addon. It is intended to hold all data necessary for the
    script.
    """
    def __init__(self, *args, **kwargs):
        """Initialize arguments object.
        Hold also references to the addon which can't be kept at module level.
        """
        self._addon     = sys.modules["__main__"]._addon
        self._addonname = sys.modules["__main__"]._plugin
        self._addonid   = sys.modules["__main__"]._plugId
        self._cj        = None

        for key, value in kwargs.iteritems():
            if value == "None":
                kwargs[key] = None
            else:
                kwargs[key] = urllib.unquote_plus(kwargs[key])
        self.__dict__.update(kwargs)
