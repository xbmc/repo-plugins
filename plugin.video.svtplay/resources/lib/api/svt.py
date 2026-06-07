# -*- coding: utf-8 -*-
from __future__ import absolute_import,unicode_literals
import re
import requests
import time
# own imports
from resources.lib import logging
from resources.lib import helper
from resources.lib.listing.listitem import VideoItem

try:
  # Python 2
  from HTMLParser import HTMLParser
  from urllib import unquote
  parser = HTMLParser()
  unescape = parser.unescape
except ImportError:
  # Python 3
  from html import unescape
  from urllib.parse import unquote

PLAY_BASE_URL = "https://www.svtplay.se"
PLAY_API_URL = PLAY_BASE_URL+"/api/"
SVT_API_BASE_URL = "https://api.svt.se"
VIDEO_API_URL= SVT_API_BASE_URL+"/videoplayer-api/video/"

def getAlphas():
  """
  Returns a list of all letters in the alphabet that has programs.

  Hard coded as the API can't return a list.
  """
  alphas = []
  alphas.append("A")
  alphas.append("B")
  alphas.append("C")
  alphas.append("D")
  alphas.append("E")
  alphas.append("F")
  alphas.append("G")
  alphas.append("H")
  alphas.append("I")
  alphas.append("J")
  alphas.append("K")
  alphas.append("L")
  alphas.append("M")
  alphas.append("N")
  alphas.append("O")
  alphas.append("P")
  alphas.append("Q")
  alphas.append("R")
  alphas.append("S")
  alphas.append("T")
  alphas.append("U")
  alphas.append("V")
  alphas.append("W")
  alphas.append("X")
  alphas.append("Y")
  alphas.append("Z")
  alphas.append("Å")
  alphas.append("Ä")
  alphas.append("Ö")
  alphas.append("0-9")
  return alphas

def getVideoJSON(video_id):
  video_version_id = video_id
  if video_id.startswith("/video/"):
    # Special case as some listings don't have video versions available.
    # The second part (12345) of video_id is then the episode ID
    # /video/12345/mystring/
    episode_id = video_id.split("/")[2]
    video_version_id = __get_video_id_for_episode_id(episode_id)
  return __get_video_json_for_video_id(video_version_id)

def getSvtVideoJson(svt_id):
  return __get_svt_json("/video/{}".format(svt_id))

def __get_video_id_for_episode_id(episode_id):
  url = "episode?id=" + episode_id
  json_data = __get_json(url)
  if json_data is None:
    return None
  versions = json_data["versions"]
  return __get_video_version(versions)

def __get_video_version(versions):
  if len(versions) > 0:
    # This logic is mimicking the web player logic
    # 1. Try to get a version matching the accessibility service (AS)
    # 1.1 Since this plugin does not support AS it will look for "none"
    # 2. If no version matching AS is found, fallback to use the first stream
    for version in versions:
      # ungraceful access so we detect API changes
      if version["accessService"] == "none":
        return version["contentUrl"]
    return versions[0]["contentUrl"]
  return None

def episodeUrlToShowUrl(url):
  """
  Returns the show URL from episode url.
  Example1: "/video/22132986/abel-och-fant/abel-och-fant-sasong-2-kupa-pa-rymmen" > "abel-och-fant"
  Example2: "/bluey" > "bluey"
  Returns None for single video items (movies etc)
  """
  new_url = None
  stub_url = url.split("/")
  if len(stub_url) >= 5:
    new_url = stub_url[3]
  elif len(stub_url) == 2:
    new_url = stub_url[1]  
  return new_url

def resolveShowJson(json_obj):
  """
  Returns an object containing the video and subtitle URL.
  """
  video_url = None
  subtitle_url = None
  video_url = __get_video_url(json_obj)
  if video_url:
    subtitle_url = __get_subtitle_url(json_obj)
    video_url = __clean_url(video_url)
  return {"videoUrl": video_url, "subtitleUrl": subtitle_url}

def __get_video_url(json_obj):
  """
  Returns the video URL from a SVT JSON object.
  """
  video_url = None
  for video in json_obj["videoReferences"]:
    if video["format"] == "hls":
      if "resolve" in video:
         video_url = __get_resolved_url(video["resolve"])
      if video_url is None:
          video_url = video["url"]
  return video_url

def __get_resolved_url(resolve_url):
  location = None
  try:
    response = requests.get(resolve_url, timeout=2)
    location = response.json()["location"]
  except Exception:
    logging.error("Exception when querying " + resolve_url)
  return location

def __get_subtitle_url(json_obj):
  """
  Returns a supported subtitle URL from a SVT JSON object.
  """
  supported_exts = (".wsrt", ".vtt")
  url = None
  try:
    for subtitle in json_obj["subtitleReferences"]:
      if subtitle["url"].endswith(supported_exts):
        url = subtitle["url"]
      else:
        if len(subtitle["url"]) > 0:
          logging.log("Skipping unsupported subtitle: " + subtitle["url"])
  except KeyError:
    pass
  return url

def __clean_url(video_url):
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

def __get_video_json_for_video_id(video_id):
  url = VIDEO_API_URL + str(video_id)
  logging.log("Getting video JSON for {}".format(url))
  response = requests.get(url)
  if response.status_code != 200:
    logging.error("Could not fetch video data for {}".format(url))
    return None
  return response.json()

def __get_json(api_action):
  """
  Returns the JSON for 'api_action'.
  PLAY_API_URL is assumed to be the prefix of 'api_action'.
  Return None if the server responds with status code != 200.
  """
  url = PLAY_API_URL+api_action
  return __do_api_request(url)

def __get_svt_json(api_action):
  """
  Calls the SVT api endpoint instead of the SVTPlay
  endpoint.
  """
  url = SVT_API_BASE_URL + api_action
  return __do_api_request(url)

def __do_api_request(url):
  """
  Performs an API request. Returns None if
  HTTP response code is != 200.
  """
  logging.log("Requesting {}".format(url))
  response = requests.get(url)
  if response.status_code != 200:
    logging.error("Failed to reach {url}, response code {code}".format(url=url, code=response.status_code))
    return None
  else:
    return response.json()
