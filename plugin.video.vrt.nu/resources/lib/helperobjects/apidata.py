class ApiData:

    def __init__(self, client, media_api_url, video_id, publication_id, xvrttoken, is_live_stream ):
        self._client = client
        self._media_api_url = media_api_url
        self._video_id = video_id
        self._publication_id = publication_id
        self._xvrttoken = xvrttoken
        self.is_live_stream = is_live_stream

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def media_api_url(self):
        return self._media_api_url

    @media_api_url.setter
    def media_api_url(self, value):
        self._media_api_url = value

    @property
    def video_id(self):
        return self._video_id

    @video_id.setter
    def video_id(self, value):
        self._video_id = value

    @property
    def publication_id(self):
        return self._publication_id

    @publication_id.setter
    def publication_id(self, value):
        self._publication_id = value

    @property
    def xvrttoken(self):
        return self._xvrttoken

    @xvrttoken.setter
    def xvrttoken(self, value):
        self._xvrttoken = value

    @property
    def is_live_stream(self):
        return self.is_live_stream

    @is_live_stream.setter
    def is_live_stream(self, value):
        self.is_live_stream = value