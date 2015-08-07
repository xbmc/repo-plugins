__author__ = 'bromix'


class ProviderException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
        self._message = message
        pass

    def get_message(self):
        return self._message

    pass


class CredentialsException(ProviderException):
    def __int__(self, message):
        ProviderException.__init__(self, message)
        pass
    pass
