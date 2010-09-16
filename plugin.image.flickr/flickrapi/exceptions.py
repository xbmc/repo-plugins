'''Exceptions used by the FlickrAPI module.'''

class IllegalArgumentException(ValueError):
    '''Raised when a method is passed an illegal argument.
    
    More specific details will be included in the exception message
    when thrown.
    '''

class FlickrError(Exception):
    '''Raised when a Flickr method fails.
    
    More specific details will be included in the exception message
    when thrown.
    '''

class CancelUpload(Exception):
    '''Raise this exception in an upload/replace callback function to
    abort the upload.
    '''

class LockingError(Exception):
    '''Raised when TokenCache cannot acquire a lock within the timeout
    period, or when a lock release is attempted when the lock does not
    belong to this process.
    '''
