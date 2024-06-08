from tmdbhelper.lib.addon.logger import kodi_log
import jurialmunkey.dialog as jurialmunkey_dialog
""" Top level module only import plugin/constants/logger """


BusyDialog = jurialmunkey_dialog.BusyDialog
busy_decorator = jurialmunkey_dialog.busy_decorator


class ProgressDialog(jurialmunkey_dialog.ProgressDialog):
    @staticmethod
    def kodi_log(msg, level=0):
        kodi_log(msg, level)
