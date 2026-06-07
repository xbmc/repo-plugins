#   Copyright (C) 2024 Lunatixz
#
#
# This file is part of iSpot.tv.
#
# iSpot.tv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iSpot.tv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iSpot.tv.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

#entrypoint
import sys
from resources.lib import ispot
if __name__ == '__main__': ispot.iSpotTV(sys.argv).run()