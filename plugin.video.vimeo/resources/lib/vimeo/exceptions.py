#!/usr/bin/env python


class BaseVimeoException(Exception):
    """Base class for Vimeo Exceptions."""

    def __get_message(self, response):
        if type(response) is Exception:
            return response.message

        json = None
        try:
            json = response.json()
        except Exception:
            pass

        if json:
            message = json.get('error') or json.get('Description')
        elif hasattr(response, 'text'):
            response_message = getattr(response, 'message', 'There was an unexpected error.')
            message = getattr(response, 'text', response_message)
        else:
            message = getattr(response, 'message')

        return message

    def __init__(self, response, message):
        """Base Exception class init."""
        # API error message
        self.message = self.__get_message(response)

        # HTTP status code
        if type(response) is Exception:
            self.status_code = 500
        elif hasattr(response, 'status_code'):
            self.status_code = response.status_code
        else:
            self.status_code = 500

        super(BaseVimeoException, self).__init__(self.message)


class ObjectLoadFailure(Exception):
    """Object Load failure exception."""

    def __init__(self, message):
        """Object Load failure exception init."""
        super(ObjectLoadFailure, self).__init__(message)


class UploadQuotaExceeded(Exception):
    """Exception for upload quota execeeded."""

    def __get_free_space(self, num):
        """Transform bytes in gigabytes."""
        return 'Free space quota: %sGb' % (round((num / 1073741824.0), 1))

    def __init__(self, free_quota, message):
        """Init method for this subclass of BaseVimeoException."""
        message = message + self.__get_free_space(num=free_quota)
        super(UploadQuotaExceeded, self).__init__(message)


class UploadAttemptCreationFailure(BaseVimeoException):
    """Exception for upload attempt creation failure."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(UploadAttemptCreationFailure, self).__init__(response, message)


class UploadTicketCreationFailure(BaseVimeoException):
    """Exception for upload ticket creation failure."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(UploadTicketCreationFailure, self).__init__(response, message)


class VideoCreationFailure(BaseVimeoException):
    """Exception for failure on the delete during the upload."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(VideoCreationFailure, self).__init__(response, message)


class VideoUploadFailure(BaseVimeoException):
    """Exception for failures during the actual upload od the file."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(VideoUploadFailure, self).__init__(response, message)


class PictureCreationFailure(BaseVimeoException):
    """Exception for failure on initial request to upload a picture."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(PictureCreationFailure, self).__init__(response, message)


class PictureUploadFailure(BaseVimeoException):
    """Exception for failure on the actual upload of the file."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(PictureUploadFailure, self).__init__(response, message)


class PictureActivationFailure(BaseVimeoException):
    """Exception for failure on activating the picture."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(PictureActivationFailure, self).__init__(response, message)


class TexttrackCreationFailure(BaseVimeoException):
    """Exception for failure on the initial request to upload a text track."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(TexttrackCreationFailure, self).__init__(response, message)


class TexttrackUploadFailure(BaseVimeoException):
    """Exception for failure on the actual upload of the file."""

    def __init__(self, response, message):
        """Init method for this subclass of BaseVimeoException."""
        super(TexttrackUploadFailure, self).__init__(response, message)


class APIRateLimitExceededFailure(BaseVimeoException):
    """Exception used when the user has exceeded the API rate limit."""

    def __get_message(self, response):
        guidelines = 'https://developer.vimeo.com/guidelines/rate-limiting'
        message = super(APIRateLimitExceededFailure, self).__get_message(
            response
        )
        limit_reset_time = response.headers.get('x-ratelimit-reset')
        if limit_reset_time:
            text = '{} \n limit will reset on: {}.\n About this limit: {}'
            message = text.format(
                message,
                limit_reset_time,
                guidelines
            )
        return message
