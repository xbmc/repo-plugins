# -*- coding: utf-8 -*-
# system imports
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
SVT_API_BASE_URL = "https://api.svt.se/"
VIDEO_API_URL= SVT_API_BASE_URL+"videoplayer-api/video/"

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

def getChannels():
  """
  Returns the live channels from the page "Kanaler".
  """
  time_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
  url = "program-guide/programs?channel=svt1,svt2,svt24,svtb,svtk&includePartiallyOverlapping=true&from={timestamp}&to={timestamp}".format(timestamp=time_str)
  json_data = __get_svt_json(url)
  if json_data is None:
    return None
  items = []
  for channel in json_data["hits"]:
    program_title = channel["programmeTitle"]
    ch_id = channel["channel"].lower()
    if channel["channel"] == "SVTK":
      ch_id="kunskapskanalen"
    elif channel["channel"] == "SVTB":
      ch_id="barnkanalen"
    title = ch_id.upper() + " - " + program_title
    if channel["live"]:
      title = title + " [COLOR red]Live[/COLOR]"
    info = {
      "plot" : channel.get("longDescription", "No description"),
      "title" : title
    }
    video_id = "ch-" + ch_id
    thumbnail = ""
    geo_restricted = True # Channels are always geo restricted
    video_item = VideoItem(title, video_id, thumbnail, geo_restricted, info)
    items.append(video_item)
  return items

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
