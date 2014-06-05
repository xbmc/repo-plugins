
import PlaylistManager

import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon('plugin.video.svtplay')

ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10
ACTION_CONTEXT_MENU = 117
KEY_NAV_BACK = 92

class PlaylistDialog(xbmcgui.WindowXMLDialog):

  def __new__(cls):
    return super(PlaylistDialog, cls).__new__(cls, 'PlaylistDialog.xml', ADDON.getAddonInfo('path'))

  def onInit(self):
    self.__list = self.getControl(4000)
    self.__loadList()
    self.__setFocus()

  def __setFocus(self):
    if self.__list.size() > 0:
      f_id = 4000
    else:
      f_id = 4002
      self.getControl(4003).setEnabled(False)
      self.getControl(4001).setEnabled(False)
    self.setFocusId(f_id)

  def onAction(self, action):
    super(PlaylistDialog, self).onAction(action)
    if action.getId() == ACTION_SELECT_ITEM:
      c_id = self.getFocusId()
      if c_id == 4001:
        # Clear
        PlaylistManager.clear()
        self.close()
      elif c_id == 4002:
        # Close
        self.close()
      elif c_id == 4003:
        # Play
        PlaylistManager.play()
        self.close()
    elif action.getId() == ACTION_CONTEXT_MENU:
      c_id = self.getFocusId()
      if c_id == 4000:
        # Remvove playlist item
        sel_item = self.__list.getSelectedItem()
        PlaylistManager.remove(sel_item)
        self.__loadList()
        self.__setFocus()

  def __loadList(self):
    items = PlaylistManager.getPlaylistAsListItems()
    self.__list.reset()
    for item in items:
      self.__list.addItem(item)

