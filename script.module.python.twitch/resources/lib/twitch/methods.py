# -*- encoding: utf-8 -*-

GET = 'GET'
POST = 'POST'
PUT = 'PUT'
DELETE = 'DELETE'

valid = [GET, POST, PUT, DELETE]


def validate(value):
    if value in valid:
        return value
    raise ValueError(value)
