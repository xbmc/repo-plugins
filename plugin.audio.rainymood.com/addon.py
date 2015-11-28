import os,time
import xbmc,xbmcgui,xbmcplugin,xbmcaddon

addon = xbmcaddon.Addon()
img = xbmc.translatePath( os.path.join( addon.getAddonInfo('path'), 'rain.jpg' ) )
url = "http://rainymood.com/audio1110/0.ogg"
# short ogg file to test loop:
# url = "http://images.wikia.com/starwars/images/f/f5/A_little_short.ogg"

class MyPlayer(xbmc.Player):
  def __init__(self):
    self.playNoise()

  def onPlayBackEnded(self):
    self.playNoise()

  def playNoise(self):
    self.play(url)

class MyWindow(xbmcgui.WindowDialog):
  def __init__(self):
    self.addControl(xbmcgui.ControlImage(1, 1, 1280, 720, img))

  def onAction(self, action):
    xbmc.log(str(action.getId()))
    # 10 = ACTION_PREVIOUS_MENU, 13 = ACTION_STOP, 93 = ACTION_NAV_BACK
    # see https://github.com/xbmc/xbmc/blob/master/xbmc/input/Key.h
    if action==10 or action==13 or action==92:
      xbmc.executebuiltin("PlayerControl(Stop)")
      self.close()

p = MyPlayer()
w = MyWindow()
w.doModal()
del w
