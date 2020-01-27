# -*- coding: utf-8 -*-
from __future__ import absolute_import,unicode_literals
import datetime
import json
import re
import requests
from xbmc import Keyboard # pylint: disable=import-error

from . import logging

try:
  # Python 2
  from urlparse import parse_qsl
  from urlparse import urljoin
  from urlparse import urlsplit
  from urllib import unquote
  from urllib import unquote_plus
except ImportError:
  # Python 3
  from urllib.parse import parse_qsl
  from urllib.parse import urljoin
  from urllib.parse import urlsplit
  from urllib.parse import unquote
  from urllib.parse import unquote_plus

def get_url_parameters(url):
  """
  Return URL parameters as a dict from a query string
  """
  return dict(parse_qsl(urlsplit(url).query))

def getInputFromKeyboard(heading):
  keyboard = Keyboard(heading=heading)
  keyboard.doModal()
  text = ""
  if keyboard.isConfirmed():
      text = keyboard.getText()
  return text
