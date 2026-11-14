"""Errors cross the HTTP, storage, and Kodi boundaries without leaking payloads."""


class EfilmError(Exception):
    def __init__(self, message, status=None, uncertain=False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.uncertain = uncertain


class Cancelled(EfilmError):
    def __init__(self):
        super().__init__("cancelled")
