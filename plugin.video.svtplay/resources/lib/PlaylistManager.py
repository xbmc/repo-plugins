import sys

import xbmc
import xbmcgui

import CommonFunctions as common

import svt
import helper

log = common.log

__playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

def add(url, title, thumbnail):
  list_item = __create_list_item(url, title, thumbnail)
  __playlist.add(list_item.getProperty("url"), list_item)

def remove(list_item):
  __playlist.remove(list_item.getfilename())

def clear():
  """
  Clears the playlist
  """
  __playlist.clear()

def getPlaylistAsListItems():
  """
  Returns the playlist as a list of xbmc.ListItems
  """
  size =  __playlist.size()
  i = 0
  items = []
  while i < size:
    list_item = __playlist.__getitem__(i)
    list_item.setProperty("id", str(i))
    items.append(list_item)
    i = i + 1

  return items

def play():
  """
  Starts playback of a playlist
  """
  xbmc.Player().play(__playlist)

def __create_list_item(url, title, thumbnail, urlResolved=False):
    list_item = xbmcgui.ListItem(
        label = title,
        thumbnailImage = thumbnail
        )
    video_url = url
    if not urlResolved:
      # If URL has not been resolved already
      video_url = __get_video_url(url)
    list_item.setProperty("url", video_url)
    return list_item


def __get_video_url(url):
  url = svt.BASE_URL + url + svt.JSON_SUFFIX
  show_obj = helper.resolveShowURL(url)
  if not show_obj["videoUrl"]:
    return ""
  return show_obj["videoUrl"]

# To support XBMC.RunScript
if __name__ == "__main__":
  log("PLM called as script!")
  if len(sys.argv) < 2:
    log("No argument given!")
  else:
    if sys.argv[1] == "add" and len(sys.argv) > 4:
      add(sys.argv[2], sys.argv[3], sys.argv[4])
