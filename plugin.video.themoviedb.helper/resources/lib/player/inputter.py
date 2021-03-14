
import xbmc
from resources.lib.kodi.rpc import get_jsonrpc
from threading import Thread


class KeyboardInputter(Thread):
    def __init__(self, action=None, text=None, timeout=300):
        Thread.__init__(self)
        self.text = text
        self.action = action
        self.exit = False
        self.poll = 0.5
        self.timeout = timeout

    def run(self):
        while not xbmc.Monitor().abortRequested() and not self.exit and self.timeout > 0:
            xbmc.Monitor().waitForAbort(self.poll)
            self.timeout -= self.poll
            if self.text and xbmc.getCondVisibility("Window.IsVisible(DialogKeyboard.xml)"):
                get_jsonrpc("Input.SendText", {"text": self.text, "done": True})
                self.exit = True
            elif self.action and xbmc.getCondVisibility("Window.IsVisible(DialogSelect.xml) | Window.IsVisible(DialogConfirm.xml)"):
                get_jsonrpc(self.action)
                self.exit = True
