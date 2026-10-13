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

from clouddrive.common.ui.addon import CloudDriveAddon
from resources.lib.provider.dropbox import Dropbox


class DropboxAddon(CloudDriveAddon):
    _provider = Dropbox()
    # Dropbox doesn't report how many items a folder has: no item count while loading, no auto-refreshed slideshow.
    _child_count_supported = False
    _auto_refreshed_slideshow_supported = False

    def get_provider(self):
        return self._provider

    def get_custom_drive_folders(self, driveid):
        return []


if __name__ == '__main__':
    DropboxAddon().route()
