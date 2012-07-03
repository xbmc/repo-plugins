

class NetworkError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NoDownloadPath(Exception):
    pass


class NoQualitySelected(Exception):
    pass


class NoTrailerSelected(Exception):
    pass
