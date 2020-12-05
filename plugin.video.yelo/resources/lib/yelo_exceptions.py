# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals


class NotAuthorizedException(Exception):
    pass


class ForbiddenException(Exception):
    pass


class YeloException(Exception):
    pass
