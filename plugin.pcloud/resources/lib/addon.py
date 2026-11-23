#-------------------------------------------------------------------------------
# Copyright (C) 2026 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
#
# This file is part of pCloud for Kodi
#
# pCloud for Kodi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pCloud for Kodi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

from clouddrive.common.ui.addon import CloudDriveAddon
from resources.lib.provider.pcloud import PCloud


class PCloudAddon(CloudDriveAddon):
    # pCloud doesn't report how many items a folder has: no item count while loading.
    _child_count_supported = False

    def __init__(self):
        self._provider = PCloud()
        super(PCloudAddon, self).__init__()

    def get_provider(self):
        return self._provider


if __name__ == '__main__':
    PCloudAddon().route()
