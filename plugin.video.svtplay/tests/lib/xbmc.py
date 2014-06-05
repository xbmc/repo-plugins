"""
Stub for module 'xbmc'
"""

LOGNOTICE = 10
PLAYLIST_MUSIC = 0
PLAYLIST_VIDEO = 1

def log(msg, level=None):
  print(msg)

def translatePath(path):
  return "./"


class Player:
  
  def play(item=None, listitem=None, windowed=None, startpos=None):
    if item:
      log("Player is playing "+str(item))

class PlayList:

  def __init__(self, list_id):
    self.__list_id = list_id
    self.__items = []

  def add(self, url, item):
    self.__items.append((url, item))

  def size(self):
    return len(self.__items)

  def dump(self):
    return str(self.__items)
