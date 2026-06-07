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
    from typing import Any
    from typing import Optional
    from typing import Text
except ImportError:
    pass


from requests import Response
from requests import Session
from requests.exceptions import HTTPError


class FranceTVVideoException(Exception):
    pass


class FranceTVVideo:
    _GEOLOCATION_URL = "https://geoftv-a.akamaihd.net/ws/edgescape.json"
    _API_URL = "https://player.webservices.francetelevisions.fr/v1/videos"

    def __init__(self):
        self._session = Session()
        self._session.hooks = {"response": [self._requests_raise_status]}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self._session:
            self._session.close()

    @staticmethod
    def _requests_raise_status(response, *_args, **_kwargs):
        # type: (Response, Any, Any) -> None

        try:
            response.raise_for_status()
        except HTTPError as ex:
            try:
                raise FranceTVVideoException(
                    ex, ex.response.json().get("message")
                )
            except ValueError:
                raise ex

    def _get_country_code(self):
        # type: () -> Optional[Text]

        response = self._session.get(self._GEOLOCATION_URL).json()

        return (
            response.get("reponse", {}).get("geo_info", {}).get("country_code")
        )

    def get_video_url(self, video_id, dash=True):
        # type: (Text, bool) -> Text

        data = self._session.get(
            "{}/{}".format(self._API_URL, video_id),
            params={
                "country_code": self._get_country_code(),
                "os": "android" if dash else "ios",
            },
        ).json()

        url = data.get("video", {}).get("url")
        token = data.get("video", {}).get("token")
        if not token or not url:
            raise FranceTVVideoException()

        video_url = (
            self._session.get(token, params={"url": url}).json().get("url")
        )
        if not video_url:
            raise FranceTVVideoException()

        return video_url
