# -*- coding: utf-8 -*-
import datetime
import json
import re
import urllib

import xbmcaddon

import CommonFunctions as common

addon = xbmcaddon.Addon("plugin.video.svtplay")
THUMB_SIZE = "extralarge"

# Available bandwidths
BANDWIDTH = [300, 500, 900, 1600, 2500, 5000]

def getPage(url):
  if not url.startswith("/") and not url.startswith("http://"):
    url = "/" + url

  result = common.fetchPage({ "link": url })

  if result["status"] == 200:
    return result["content"]

  if result["status"] == 500:
    common.log("redirect url: %s" %result["new_url"])
    common.log("header: %s" %result["header"])
    common.log("content: %s" %result["content"])
    return None


def convertChar(char):
  if char == "&Aring;":
    return "Å"
  elif char == "&Auml;":
    return "Ä"
  elif char == "&Ouml;":
    return "Ö"
  else:
    return char


def convertDuration(duration):
  """
  Converts SVT's duration format to XBMC friendly format (minutes).

  SVT has the following format on their duration strings:
  1 h 30 min
  1 min 30 sek
  1 min
  """

  match = re.match(r'(^(\d+)\sh)*(\s*(\d+)\smin)*(\s*(\d+)\ssek)*', duration)

  dhours = 0
  dminutes = 0
  dseconds = 0

  if match.group(1):
    dhours = int(match.group(2)) * 60

  if match.group(3):
    dminutes = int(match.group(4))

  if match.group(5):
    dseconds = int(match.group(6)) / 60

  return str(dhours + dminutes + dseconds)

def convertDate(date):
  """
  Converts a SVT date string to a XBMC date string

  Examples:
  From "lör 21 mar" to "2014-03-21"
  From "idag 18.00" to "2014-03-24"
  From "igår 20.00" to "2014-03-23"
  """
  if not date:
    return ""

  months = {
      "jan": 1,
      "feb": 2,
      "mar": 3,
      "apr": 4,
      "maj": 5,
      "jun": 6,
      "jul": 7,
      "aug": 8,
      "sep": 9,
      "okt": 10,
      "nov": 11,
      "dec": 12
      }
  today = datetime.date.today()
  one_day = datetime.timedelta(days=1)
  return_date = today

  match = re.match(r"(.+)\s(\d+)\s(\w+)", date)
  if match:
    # "lör 21 mar" match
    month = months[match.group(3)]
    day = int(match.group(2))
    return_date = today.replace(day=day, month=month)
  else:
    match = re.match(r"(.+)\s.+", date)
    if match:
      if match.group(1) == "ig&aring;r":
        # "igår 18.00" match
        return_date = today - one_day
  return return_date.isoformat()

def getUrlParameters(arguments):
  """
  Return URL parameters as a dict from a query string
  """
  params = {}

  if arguments:

      start = arguments.find("?") + 1
      pairs = arguments[start:].split("&")

      for pair in pairs:

        split = pair.split("=")

        if len(split) == 2:
          params[split[0]] = split[1]

  return params


def tabExists(html, tabname):
  """
  Check if a specific tab exists in the DOM.
  """
  return elementExists(html, "div", { "data-tabname": tabname})


def elementExists(html, etype, attrs):
  """
  Check if a specific element exists in the DOM.
  """

  htmlelement = common.parseDOM(html, etype, attrs = attrs)

  return len(htmlelement) > 0


def prepareThumb(thumbnail, baseUrl):
  """
  Returns a thumbnail with size THUMB_SIZE
  """
  if not thumbnail.startswith("http://") and baseUrl:
    thumbnail = baseUrl + thumbnail
  thumbnail = re.sub(r"/small|medium|large|extralarge/", ""+THUMB_SIZE+"", thumbnail)
  return thumbnail

def prepareFanart(url, baseUrl):
  """
  Returns a fanart image URL.
  """
  if not url.startswith("http://") and baseUrl:
    url = baseUrl + url
  new_url = re.sub(r"/small|medium|large|extralarge/", "extralarge_imax", url)
  return new_url


def mp4Handler(jsonObj):
  """
  Returns a mp4 stream URL.

  If there are several mp4 streams in the JSON object:
  pick the one with the highest bandwidth.

  Some programs are available with multiple mp4 streams
  for different bitrates. This function ensures that the one
  with the highest bitrate is chosen.

  Can possibly be extended to support some kind of quality
  setting in the plugin.
  """
  videos = []

  # Find all mp4 videos
  for video in jsonObj["video"]["videoReferences"]:
    if video["url"].endswith(".mp4"):
      videos.append(video)

  if len(videos) == 1:
    return videos[0]["url"]

  bitrate = 0
  url = ""

  # Find the video with the highest bitrate
  for video in videos:
    if video["bitrate"] > bitrate:
      bitrate = video["bitrate"]
      url = video["url"]

  common.log("Info: bitrate="+str(bitrate)+" url="+url)
  return url


def hlsStrip(videoUrl):
    """
    Extracts the stream that supports the
    highest bandwidth and is not using the avc1.77.30 codec.
    """
    common.log("Stripping file: " + videoUrl)

    ufile = urllib.urlopen(videoUrl)
    lines = ufile.readlines()

    hlsurl = ""
    bandwidth = 0
    foundhigherquality = False

    for line in lines:
      if foundhigherquality:
        # The stream url is on the line proceeding the header
        foundhigherquality = False
        hlsurl = line
      if "EXT-X-STREAM-INF" in line: # The header
        if not "avc1.77.30" in line:
          match = re.match(r'.*BANDWIDTH=(\d+).+', line)
          if match:
            if bandwidth < int(match.group(1)):
              foundhigherquality = True
              bandwidth = int(match.group(1))
          continue

    if bandwidth == 0:
      return None

    ufile.close()
    hlsurl = hlsurl.rstrip()
    common.log("Returned stream url : " + hlsurl)
    return hlsurl


def getStreamForBW(url):
  """
  Returns a stream URL for the set bandwidth,
  and an error message, if applicable.
  """
  low_bandwidth  = int(float(addon.getSetting("bandwidth")))
  high_bandwidth = getHighBw(low_bandwidth)

  f = urllib.urlopen(url)
  lines = f.readlines()

  hlsurl = ""
  marker = "#EXT-X-STREAM-INF"
  found = False

  for line in lines:
    if found:
      # The stream url is on the line proceeding the header
      hlsurl = line
      break
    if marker in line: # The header
      match = re.match(r'.*BANDWIDTH=(\d+)000.+', line)
      if match:
        if low_bandwidth < int(match.group(1)) < high_bandwidth:
          common.log("Found stream with bandwidth " + match.group(1) + " for selected bandwidth " + str(low_bandwidth))
          found = True

  f.close()

  if found:
    hlsurl = hlsurl.rstrip()
    common.log("Returned stream url: " + hlsurl)
    return (hlsurl, '')
  else:
    errormsg = "No stream found for bandwidth setting " + str(low_bandwidth)
    common.log(errormsg)
    return (None, errormsg)


def getHighBw(low):
  """
  Returns the higher bandwidth boundary
  """
  i = BANDWIDTH.index(low)
  return BANDWIDTH[i+1]

def getJSONObj(show_url):
  """
  Returns a SVT JSON object from a show URL
  """
  url_obj = urllib.urlopen(show_url)
  json_obj = json.load(url_obj)
  url_obj.close()
  return json_obj


def getVideoURL(json_obj):
  """
  Returns the video URL from a SVT JSON object.
  """
  video_url = None

  for video in json_obj["video"]["videoReferences"]:
    if video["playerType"] == "ios":
      video_url = video["url"]

  return video_url

def resolveShowURL(show_url):
  """
  Returns an object containing the video and subtitle URL for a show URL.
  Takes all settings into account.
  """
  json_obj = getJSONObj(show_url)
  video_url = getVideoURL(json_obj)
  subtitle_url = getSubtitleUrl(json_obj)
  extension = getVideoExtension(video_url)
  errormsg = None

  if extension == "HLS":
    if getSetting("hlsstrip"):
      video_url = hlsStrip(video_url)
    elif getSetting("bwselect"):
      (video_url, errormsg) = getStreamForBW(video_url)

  return {"videoUrl": video_url, "subtitleUrl": subtitle_url}

def getSubtitleUrl(json_obj):
  """
  Returns a subtitleURL from a SVT JSON object.
  """
  url = None

  for subtitle in json_obj["video"]["subtitleReferences"]:
    if subtitle["url"].endswith(".wsrt"):
      url = subtitle["url"]
    else:
      if len(subtitle["url"]) > 0:
        common.log("Skipping unknown subtitle: " + subtitle["url"])

  return url


def getVideoExtension(video_url):
  """
  Returns a string representation of the video extension.
  """
  # Remove all query strings
  url = video_url.split("?")[0]
  extension = None
  if url.endswith(".m3u8"):
    extension = "HLS"
  elif url.endswith(".mp4"):
    extension = "MP4"

  return extension


def getSetting(setting):
  return True if addon.getSetting(setting) == "true" else False
