"""SRGSSR Subtitles API Client"""

from .srgssr_api_client import SRGSSRApiClient


class SRGSSRSubtitlesApiClient(SRGSSRApiClient):
    """Subtitles API client"""

    _VERSION = "v1"
    _API_NAME = "Subtitles"
    _API_URL_NAME = "srgssr-play-subtitles"

    @SRGSSRApiClient._renew_access_token
    def get_subtitles(self, video_urn: str):
        """Returns the subtitles for a video
        :param video_urn: URN of the video
        """
        resp = self._get(f"identifier/{video_urn}")
        return self._handle_response(resp)
