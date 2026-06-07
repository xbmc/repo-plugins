from time import time
import xbmcgui
import xbmcvfs
import xbmcaddon
import os


# https://github.com/cguZZman/script.module.clouddrive.common/blob/master/clouddrive/common/ui/dialog.py
class QRDialogProgress(xbmcgui.WindowXMLDialog):
    _heading_control = 1000
    _qr_control = 1001
    _text_control = 1002
    _cancel_btn_control = 1003
    addon = xbmcaddon.Addon()

    def __init__(self, *args, **kwargs):
        self.heading = QRDialogProgress.addon.getLocalizedString(30401)
        self.qr_code = ""
        self.line1 = QRDialogProgress.addon.getLocalizedString(
            30400) + QRDialogProgress.addon.getSettingString('baseUrl') + ' :'
        self.line2 = QRDialogProgress.addon.getLocalizedString(30423)
        self.line3 = QRDialogProgress.addon.getLocalizedString(30426)
        self.line4 = QRDialogProgress.addon.getLocalizedString(30427)
        self.time_left = 0
        self._image_path = None
        self.canceled = False

    def __del__(self):
        xbmcvfs.delete(self._image_path)
        pass

    @staticmethod
    def create():
        return QRDialogProgress("pin-dialog.xml", QRDialogProgress.addon.getAddonInfo('path'), "default", "1080i")

    def iscanceled(self):
        return self.canceled

    def onInit(self):
        self.getControl(self._heading_control).setLabel(self.heading)
        self.update(self.time_left, self.line2)

    def update(self, time_left=None, code=None):
        if time_left:
            self.time_left = time_left

        if code:
            self.line2 = code
            self.qr_code = os.path.join(QRDialogProgress.addon.getSettingString(
                'baseUrl'), f'authenticate?code={code}')

        text = f'{self.line1}[CR][COLOR red][B]{self.line2}[/B][/COLOR][CR][CR]{self.line3} {self.time_left} {self.line4}.'
        self.getControl(self._text_control).setText(text)
        self.updateQr()
        self.setFocus(self.getControl(self._cancel_btn_control))

    def onClick(self, control_id):
        if control_id == self._cancel_btn_control:
            self.canceled = True
            self.close()

    def onAction(self, action):
        if action.getId() == xbmcgui.ACTION_PREVIOUS_MENU or action.getId() == xbmcgui.ACTION_NAV_BACK:
            self.canceled = True
        super(QRDialogProgress, self).onAction(action)

    def updateQr(self):
        import pyqrcode
        self._image_path = os.path.join(xbmcvfs.translatePath(
            self.addon.getAddonInfo('profile')), "qr.png")
        qrcode = pyqrcode.create(self.qr_code)
        qrcode.png(self._image_path, scale=10)
        del qrcode
        self.getControl(self._qr_control).setImage(self._image_path)
