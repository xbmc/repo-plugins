from dataclasses import dataclass


@dataclass
class RequestError(Exception):
    error_code: int
    url: str
    method: str
    body: str
