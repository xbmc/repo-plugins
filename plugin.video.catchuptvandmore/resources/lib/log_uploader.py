# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

# Inspired by https://gitlab.com/ronie/script.kodi.loguploader/blob/master/default.py

from builtins import str
import os
import re

import pyqrcode
from kodi_six import xbmc, xbmcgui, xbmcvfs

from codequick import Script
import urlquick

PROFILE = Script.get_info('profile')
CWD = Script.get_info('path')
URL = 'https://paste.kodi.tv/'
LOGPATH = xbmcvfs.translatePath('special://logpath')
LOGFILE = os.path.join(LOGPATH, 'kodi.log')
REPLACES = (
    ('//.+?:.+?@', '//USER:PASSWORD@'),
    ('password.*', 'password*******LINE_DELETED*********'),
    ('login.*', 'login******LINE_DELETED**********'),
    ('Password.*', 'Password*******LINE_DELETED*********'),
    ('Login.*', 'Login******LINE_DELETED**********'),
    ('email.*', 'email******LINE_DELETED**********'),
    ('<user>.+?</user>', '<user>USER</user>'),
    ('<pass>.+?</pass>', '<pass>PASSWORD</pass>'),
)


class QRCode(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.image = kwargs["image"]
        self.text = kwargs["text"]

    def onInit(self):
        self.imagecontrol = 501
        self.textbox = 502
        self.okbutton = 503
        self.showdialog()

    def showdialog(self):
        self.getControl(self.imagecontrol).setImage(self.image)
        self.getControl(self.textbox).setText(self.text)
        self.setFocus(self.getControl(self.okbutton))

    def onClick(self, controlId):
        if (controlId == self.okbutton):
            self.close()


def read_log(path):
    try:
        lf = xbmcvfs.File(path)
        cnt = 0
        content_file = lf.read()
        content_l = content_file.splitlines()
        content = ""
        for line in reversed(content_l):
            cnt = cnt + 1
            # Keep only the 10000 last lines
            if cnt == 10000:
                break
            content = line + '\n' + content
        lf.close()
        if not content:
            return False, "Log file is empty"
        return True, content
    except Exception:
        return False, "Unable to read log file"


def clean_log(content):
    for pattern, repl in REPLACES:
        content = re.sub(pattern, repl, content)
    return content


def post_log(data):
    try:
        response = response = urlquick.post(URL + 'documents', data=data)
        if 'key' in response.json():
            result = URL + response.json()['key']
            return True, result

        if 'message' in response.json():
            return False, "Unable to upload log file: " + response.json()['message']

        Script.log('error: %s' % response.text)
        return False, "Unable to upload log file"
    except Exception:
        return False, "Unable to retrieve the paste url"


def ask_to_share_log():
    """
    Ask the if he wants to share his log
    directly by mail with a QR code
    or by sharing the pastebin URL by mail,
    on github or forum
    """
    r = xbmcgui.Dialog().yesno(Script.localize(30600),
                               Script.localize(30860))
    if not r:
        return

    if not xbmcvfs.exists(PROFILE):
        xbmcvfs.mkdirs(PROFILE)

    succes, data = read_log(LOGFILE)
    print_error = False
    error_message = ""
    if succes:
        content = clean_log(data)
        succes, data = post_log(content)
        if succes:
            imagefile = os.path.join(xbmc.translatePath(PROFILE), '%s.png' % str(data.split('/')[-1]))
            message = Script.localize(30861)
            message = message.replace("URL_TO_REPLACE", data)
            mail_url = 'mailto:catch.up.tv.and.more@gmail.com?subject=Kodi%20log&body=' + data
            qrIMG = pyqrcode.create(mail_url)
            qrIMG.png(imagefile, scale=10)

            qr = QRCode("script-loguploader-main.xml", CWD, "default", image=imagefile, text=message)
            qr.doModal()
            del qr
            xbmcvfs.delete(imagefile)
        else:
            print_error = True
            error_message = data
    else:
        print_error = True
        error_message = data

    if print_error:
        xbmcgui.Dialog().ok(
            Script.localize(30600),
            Script.localize(30862) + ': ' + error_message)

    return
