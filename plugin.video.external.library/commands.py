# Copyright (C) 2023, Roman Miroshnychenko aka Roman V.M.
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
import sys

import xbmc
import xbmcgui

from libs.exception_logger import catch_exception
from libs.json_rpc_api import update_playcount
from libs.kodi_service import GettextEmulator, initialize_logging

initialize_logging()
logger = logging.getLogger(__name__)
_ = GettextEmulator.gettext


def main():
    logger.debug('Executing command: %s', str(sys.argv))
    if len(sys.argv) == 1:
        xbmcgui.Dialog().ok(_('Kodi External Video Library Client'),
                            _(r'Please run this addon from \"Video addons\" section.'))
    elif sys.argv[1] == 'update_playcount':
        update_playcount(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
        xbmc.executebuiltin('Container.Refresh')


if __name__ == '__main__':
    with catch_exception():
        main()
