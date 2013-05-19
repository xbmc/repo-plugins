# -*- coding: utf-8 -*-
import CommonFunctions
import re

common = CommonFunctions
THUMB_SIZE = "extralarge"

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

  match = re.match(r'(^(\d+)\sh)*(\s*(\d+)\smin)*(\s*(\d+)\ssek)*',duration)

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


def tabExists(html,tabname):
  """
  Check if a specific tab exists in the DOM.
  """
  return elementExists(html,"div",{ "data-tabname": tabname})


def elementExists(html,etype,attrs):
  """
  Check if a specific element exists in the DOM.
  """

  htmlelement = common.parseDOM(html,etype, attrs = attrs)

  return len(htmlelement) > 0


def prepareThumb(thumbnail):
  """
  Returns a thumbnail with size 'large'
  """
  common.log("old thumbnail: " + thumbnail)
  if not thumbnail.startswith("http://"):
    thumbnail = "http://www.svtplay.se" + thumbnail
  thumbnail = re.sub(r"/small|medium|large|extralarge/", "/"+THUMB_SIZE+"/", thumbnail)
  common.log("new thumbnail: " + thumbnail)
  return thumbnail
