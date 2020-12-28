"""
Stub for 'xbmcgui'
"""

class ListItem:

  def __init__(self, label=None):
    self.__label = label

  def getLabel(self):
    return self.__label

  def setThumbnailImage(self, path):
    self.__thumb = path

  def setPath(self, path):
    self.__path = path
