# -*- coding: utf-8 -*-

# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

class StreamURLS:

    def __init__(self, stream_url, subtitle_url=None, license_key=None, use_inputstream_adaptive=False):
        self._stream_url = stream_url
        self._subtitle_url = subtitle_url
        self._license_key = license_key
        self._use_inputstream_adaptive = use_inputstream_adaptive
        self._video_id = None

    @property
    def stream_url(self):
        return self._stream_url

    @property
    def subtitle_url(self):
        return self._subtitle_url

    @property
    def video_id(self):
        return self._video_id

    @property
    def license_key(self):
        return self._license_key

    @property
    def use_inputstream_adaptive(self):
        return self._use_inputstream_adaptive
