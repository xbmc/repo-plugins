__author__ = 'bromix'

__ALL__ = ['HttpClient', 'get', 'post', 'delete', 'options', 'head', 'put']

from .client import HttpClient
from .api import get, post, delete, options, head, put