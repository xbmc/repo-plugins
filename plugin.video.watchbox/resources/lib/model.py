# -*- coding: utf-8 -*-
# Watchbox
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
try:
    from urlparse import parse_qs
    from urllib import unquote_plus
except ImportError:
    from urllib.parse import parse_qs, unquote_plus


def parse():
    """Decode arguments
    """
    if (sys.argv[2]):
        return Args(parse_qs(sys.argv[2][1:]))
    else:
        return Args({})


class Args(object):
    """Arguments class
    Hold all arguments passed to the script and also persistent user data and
    reference to the addon. It is intended to hold all data necessary for the
    script.
    """
    def __init__(self, kwargs):
        """Initialize arguments object
        Hold also references to the addon which can't be kept at module level.
        """
        self.PY2        = sys.version_info[0] == 2 #: True for Python 2
        self._addon     = sys.modules["__main__"]._addon
        self._addonname = sys.modules["__main__"]._plugin
        self._addonid   = sys.modules["__main__"]._plugId
        self._cj        = None
        self._login     = False

        for key, value in kwargs.items():
            if value:
                setattr(self, key, unquote_plus(value[0]))
