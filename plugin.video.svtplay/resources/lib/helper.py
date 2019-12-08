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

  if keyboard.isConfirmed():
      text = keyboard.getText()

  return text

def get_thumb_url(thumbUrl, baseUrl):
  return __create_image_url(thumbUrl, baseUrl, "extralarge")

def get_fanart_url(fanartUrl, baseUrl):
  return __create_image_url(fanartUrl, baseUrl, "extralarge_imax")

def __create_image_url(image_url, base_url, image_size):
  if not image_url:
    return ""
  image_url = __clean_image_url(image_url, base_url)
  image_url = re.sub(r"\{format\}|small|medium|large|extralarge", image_size, image_url)
  return image_url

def __clean_image_url(url, baseUrl):
  if url.startswith("//"):
    url = url.lstrip("//")
    url = "http://" + url
  elif not (url.startswith("http://") or url.startswith("https://")) and baseUrl:
    url = baseUrl + url
  # Kodi has issues fetching images over SSL
  url = url.replace("https", "http")
  return url

def getVideoURL(json_obj):
  """
  Returns the video URL from a SVT JSON object.
  """
  video_url = None
  for video in json_obj["videoReferences"]:
    if video["format"] == "hls":
      if "resolve" in video:
         video_url = getResolvedUrl(video["resolve"])
      if video_url is None:
          video_url = video["url"]
  return video_url

def getResolvedUrl(resolve_url):
  location = None
  try:
    response = requests.get(resolve_url, timeout=2)
    location = response.json()["location"]
  except Exception:
    logging.error("Exception when querying " + resolve_url)
  return location

def getSubtitleUrl(json_obj):
  """
  Returns a subtitleURL from a SVT JSON object.
  """
  url = None
  try:
    for subtitle in json_obj["subtitleReferences"]:
      if subtitle["url"].endswith(".wsrt"):
        url = subtitle["url"]
      else:
        if len(subtitle["url"]) > 0:
          logging.log("Skipping unknown subtitle: " + subtitle["url"])
  except KeyError:
    pass
  return url

def resolveShowJSON(json_obj):
  """
  Returns an object containing the video and subtitle URL for a show URL.
  Takes all settings into account.
  """
  video_url = None
  subtitle_url = None
  video_url = getVideoURL(json_obj)
  if video_url:
    subtitle_url = getSubtitleUrl(json_obj)
    video_url = cleanUrl(video_url)
  return {"videoUrl": video_url, "subtitleUrl": subtitle_url}

def cleanUrl(video_url):
  """
  Returns a cleaned version of the URL.

  Put all permanent and temporary cleaning rules here.
  """
  tmp = video_url.split("?")
  newparas = []
  if len(tmp) == 2:
    # query parameters exists
    newparas.append("?")
    paras = tmp[1].split("&")
    for para in paras:
      if para.startswith("cc1"):
        # Clean out subtitle parameters for iOS
        # causing playback issues in xbmc.
        pass
      elif para.startswith("alt"):
        # Web player specific parameter that
        # Kodi doesn't need.
        pass
      else:
        newparas.append(para)
  return tmp[0]+"&".join(newparas).replace("?&", "?")

def episodeUrlToShowUrl(url):
  """
  Returns the show URL from episode url.
  Example: "/video/22132986/abel-och-fant/abel-och-fant-sasong-2-kupa-pa-rymmen" > "/abel-och-fant"

  Returns None for single video items (movies etc)
  """
  new_url = None
  stub_url = url.split("/")
  if len(stub_url) >= 5:
    new_url = "/" + stub_url[3]
  return new_url

def __errorMsg(msg):
  logging.error(msg)

def _infoMsg(msg):
  logging.log(msg)
