# -*- coding: utf-8 -*-
# system imports
from __future__ import absolute_import,unicode_literals
import re
import requests
import time
# own imports
from resources.lib import logging
from resources.lib import helper

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

def getCategories():
  """
  Returns a list of all categories.
  """
  json_data = __get_json("clusters")
  if json_data is None:
    return None
  categories = []
  for cluster in json_data:
    category = {}
    category["title"] = cluster["name"]
    category["url"] = cluster["contentUrl"]
    category["genre"] = cluster["slug"]
    categories.append(category)
  return categories

def getLatestNews():
  """
  Returns a list of latest news programs.
  """
  json_data = __get_json("cluster_latest?cluster=nyheter")
  if json_data is None:
    return None
  programs = []
  for item in json_data:
    live_str = ""
    thumbnail = item.get("thumbnail", "")
    if item["broadcastedNow"]:
      live_str = " " + "[COLOR red](Live)[/COLOR]"
    versions = item.get("versions", [])
    url = "video/" + item["contentUrl"]
    if versions:
      url = __get_video_version(versions)
    program = {
      "title" : unescape(item["programTitle"] + " " + (item["title"] or "") + live_str),
      "thumbnail" : helper.get_thumb_url(thumbnail, baseUrl=PLAY_BASE_URL),
      "url" : url,
      "info" : { 
        "duration" : item.get("materialLength", 0), 
        "fanart" : helper.get_fanart_url(item.get("poster", ""), baseUrl=PLAY_BASE_URL)
      },
      "onlyAvailableInSweden": item.get("onlyAvailableInSweden", False)
    }
    programs.append(program)
  return programs

def getProgramsForGenre(genre):
  """
  Returns a list of all programs for a genre.
  """
  json_data = __get_json("cluster_titles_and_episodes?cluster="+genre)
  if json_data is None:
    return None
  programs = []
  for json_item in json_data:
    versions = json_item.get("versions", [])
    content_type = "video"
    if versions:
      url = __get_video_version(versions)
    else:
      url = json_item["contentUrl"]
      content_type = "program"
    title = json_item["programTitle"]
    plot = json_item.get("description", "")
    thumbnail = helper.get_thumb_url(json_item.get("thumbnail", ""), PLAY_BASE_URL)
    if not thumbnail:
      thumbnail = helper.get_thumb_url(json_item.get("poster", ""), PLAY_BASE_URL)
    info = {"plot": plot, "thumbnail": thumbnail, "fanart": thumbnail}
    programs.append({
      "title": title,
      "url": url,
      "thumbnail": thumbnail,
      "info": info,
      "type" : content_type,
      "onlyAvailableInSweden" : json_item["onlyAvailableInSweden"]
    })
  return programs

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
    item = {}
    program_title = channel["programmeTitle"]
    ch_id = channel["channel"].lower()
    if channel["channel"] == "SVTK":
      ch_id="kunskapskanalen"
    elif channel["channel"] == "SVTB":
      ch_id="barnkanalen"
    item["title"] = ch_id.upper() + " - " + program_title
    if channel["live"]:
      item["title"] = item["title"] + " [COLOR red]Live[/COLOR]"
    item["info"] = {}
    item["info"]["plot"] = channel.get("longDescription", "No description")
    item["info"]["title"] = item["title"]
    item["url"] = "ch-" + ch_id
    item["thumbnail"] = ""
    item["onlyAvailableInSweden"] = True # Channels are always geo restricted
    items.append(item)
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
