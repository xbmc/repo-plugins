# -*- coding: utf-8 -*-
# Copyright: (c) 2016 William Forde (willforde+kodi@gmail.com)
#
# License: GPLv2, see LICENSE for more details
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

# Package imports
from codequick import youtube, Route, run


@Route.register
class Root(youtube.Playlists):
    def run(self, **kwargs):
        return super(Root, self).run("UCnavGPxEijftXneFxk28srA", loop=True, **kwargs)


# Initiate add-on
if __name__ == "__main__":
    run()
