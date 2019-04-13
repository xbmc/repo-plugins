#   Copyright (C) 2019 Lunatixz
#
#
# This file is part of USTVnow
#
# USTVnow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# USTVnow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with USTVnow. If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
#entrypoint
import sys
from resources.lib import ustvnow
if __name__ == '__main__': ustvnow.USTVnow(sys.argv).run()