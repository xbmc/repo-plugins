class BaseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class CopyError(BaseError): pass
class DownloadError(BaseError): pass
class XmlError(BaseError): pass
class MediatypeError(BaseError): pass
class DeleteError(BaseError): pass
class CreateDirectoryError(BaseError): pass
class HTTP400Error(BaseError): pass
class HTTP404Error(BaseError): pass
class HTTP503Error(BaseError): pass
class HTTPTimeout(BaseError): pass
class NoFanartError(BaseError): pass
class ItemNotFoundError(BaseError): pass
