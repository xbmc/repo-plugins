import xbmcgui


class OAuthDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_code = ""
        self.verification_uri = ""
        self.qr_path = None
        self.cancelled = False
        self.authorized = False

    def onInit(self):
        self.getControl(301).setLabel(self.verification_uri)
        self.getControl(302).setLabel("[B]Code: {}[/B]".format(self.user_code))
        if self.qr_path:
            self.getControl(200).setImage(self.qr_path)

    def onClick(self, control_id):
        if control_id == 9001:
            self.cancelled = True
            self.close()

    def onAction(self, action):
        if action.getId() in (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK):
            self.cancelled = True
            self.close()

    def set_status(self, text):
        try:
            self.getControl(400).setLabel(text)
        except Exception:
            pass

    def set_authorized(self):
        self.authorized = True
        self.close()
