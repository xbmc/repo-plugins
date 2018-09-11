#-------------------------------------------------------------------------------
# Copyright (C) 2017 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
# 
# This file is part of Google Drive for Kodi
# 
# Google Drive for Kodi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Cloud Drive Common Module for Kodi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

from clouddrive.common.service.download import DownloadService
from clouddrive.common.service.source import SourceService
from clouddrive.common.service.utils import ServiceUtil
from resources.lib.provider.googledrive import GoogleDrive
from clouddrive.common.service.export import ExportService
from clouddrive.common.service.player import PlayerService


if __name__ == '__main__':
    ServiceUtil.run([DownloadService(GoogleDrive), SourceService(GoogleDrive),
                     ExportService(GoogleDrive), PlayerService(GoogleDrive)])