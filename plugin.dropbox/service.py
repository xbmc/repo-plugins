#-------------------------------------------------------------------------------
# Copyright (C) 2017 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
#
# This file is part of Dropbox for Kodi
#
# Dropbox for Kodi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dropbox for Kodi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

from clouddrive.common.service.download import DownloadService
from clouddrive.common.service.export import ExportService
from clouddrive.common.service.player import PlayerService
from clouddrive.common.service.source import SourceService
from clouddrive.common.service.utils import ServiceUtil
from clouddrive.common.ui.utils import KodiUtils
from resources.lib.provider.dropbox import Dropbox


if __name__ == '__main__':
    # Dropbox 1.0.0 to 1.0.3 used Google Drive's source port by mistake: with both add-ons, one source server couldn't start.
    if KodiUtils.get_addon_setting('port_directory_listing') == '8587':
        KodiUtils.set_addon_setting('port_directory_listing', '8588')
    ServiceUtil.run([DownloadService(Dropbox), SourceService(Dropbox),
                     ExportService(Dropbox), PlayerService(Dropbox)])
