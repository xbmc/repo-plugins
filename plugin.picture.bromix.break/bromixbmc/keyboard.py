import xbmc

class Keyboard(object):
    def __init__(self, title, default='', hidden=False):
        self._keyboard = xbmc.Keyboard(default, title, hidden)
    
    def doModal(self):
        self._keyboard.doModal()
        return self._keyboard.isConfirmed() and self._keyboard.getText()
    
    def getText(self):
        return self._keyboard.getText()