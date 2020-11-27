# coding: utf-8
#
# Copyright © 2020 melmorabity
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import unicode_literals

try:
    from urllib.parse import parse_qsl
    from urllib.parse import urlencode
    from urllib.parse import urlparse
    from urllib.parse import urlunparse
except ImportError:
    from urlparse import parse_qsl
    from urllib import urlencode
    from urlparse import urlparse
    from urlparse import urlunparse

try:
    from typing import Optional
    from typing import Text
    from typing import Union
except ImportError:
    pass

from bs4 import BeautifulSoup


# Only capitalize the first letter
def capitalize(label):
    # type: (Optional[Text]) -> Optional[Text]

    if not label:
        return label

    return label[0].upper() + label[1:]


def html_to_text(html):
    # type: (Optional[Text]) -> Optional[Text]

    if not html:
        return html

    return BeautifulSoup(html, features="html.parser").get_text()


def update_url_params(url, **params):
    # type: (Text, Union[None, int, Text]) -> Text

    clean_params = {k: v for k, v in list(params.items()) if v is not None}

    parsed_url = list(urlparse(url))
    parsed_url_params = dict(parse_qsl(parsed_url[4]))
    parsed_url_params.update(clean_params)
    parsed_url[4] = urlencode(clean_params)

    return urlunparse(parsed_url)
