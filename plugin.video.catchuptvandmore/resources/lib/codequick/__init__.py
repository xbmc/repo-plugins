# -*- coding: utf-8 -*-
# Copyright: (c) 2016 - 2018 William Forde (willforde+codequick@gmail.com)
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

"""
Codequick is a framework for kodi add-on’s. The goal for this framework is to simplify add-on development.
This  is achieved by reducing the amount of boilerplate code to a minimum, while automating as many tasks
that can be automated. Ultimately, allowing the developer to focus primarily on scraping content from
websites and passing it to Kodi.

Github: https://github.com/willforde/script.module.codequick
Documentation: http://scriptmodulecodequick.readthedocs.io/en/latest/?badge=latest
Integrated Unit Tests: https://travis-ci.org/willforde/script.module.codequick
Code Coverage: https://coveralls.io/github/willforde/script.module.codequick?branch=master
Codacy: https://app.codacy.com/app/willforde/script.module.codequick/dashboard
"""

from __future__ import absolute_import

# Package imports
from resources.lib.codequick.support import run
from resources.lib.codequick.resolver import Resolver
from resources.lib.codequick.listing import Listitem
from resources.lib.codequick.script import Script
from resources.lib.codequick.route import Route
from resources.lib.codequick import utils, storage

__all__ = ["run", "Script", "Route", "Resolver", "Listitem", "utils", "storage"]
