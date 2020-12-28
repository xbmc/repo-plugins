"""
Stub for 'xbmcaddon'
"""

class Addon:

  def __init__(self, id=None):
    self.id = id
    self.version = 1.0


  def getAddonInfo(self, id):
    if id == self.id:
      return self.id
    else:
      return "no info"
