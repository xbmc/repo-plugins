import os,time
import xbmc,xbmcgui,xbmcplugin,xbmcaddon

addon = xbmcaddon.Addon()
img = xbmc.translatePath( os.path.join( addon.getAddonInfo('path'), 'rain.jpg' ) )
url = "http://174.36.223.28/audio1110/classic.ogg"
#url = "http://images.wikia.com/starwars/images/f/f5/A_little_short.ogg"

class MyPlayer(xbmc.Player):
  def __init__(self):
    self.playNoise()
  
  def onPlayBackEnded(self):
    self.playNoise()
  
  def playNoise(self):
    listitem = xbmcgui.ListItem('Rainy Mood')
    self.play(url, listitem, False)

class MyWindow(xbmcgui.WindowDialog):
  def __init__(self):
    self.addControl(xbmcgui.ControlImage(1, 1, 1280, 720, img))

  def onAction(self, action):
    #xbmc.log(str(action.getId()))
    # 10 = back, 13 = stop
    if action==10 or action == 13:
      p.stop()
      self.close()

p = MyPlayer()
w = MyWindow()
xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
w.doModal()
del w
