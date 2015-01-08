# Copyright 2012 Charles Blaxland
# This file is part of rdio-xbmc.
#
# rdio-xbmc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rdio-xbmc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rdio-xbmc.  If not, see <http://www.gnu.org/licenses/>.

import re

def iso_date_to_xbmc_date(iso_date):
  iso_date_pattern = re.compile('(\d\d\d\d)-(\d\d)-(\d\d)')
  match = iso_date_pattern.match(iso_date)
  if match:
    return '%s.%s.%s' % (match.group(3), match.group(2), match.group(1))
  else:
    return iso_date
