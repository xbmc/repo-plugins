# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# Inspired by https://gitlab.com/ronie/script.kodi.loguploader/blob/master/default.py

from builtins import str
import os
import re

from kodi_six import xbmc
from kodi_six import xbmcvfs
from kodi_six import xbmcgui
import pyqrcode

from resources.lib.codequick import Script
from resources.lib import urlquick

from resources.lib.labels import LABELS

PROFILE = Script.get_info('profile')
CWD = Script.get_info('path')
URL = 'https://paste.kodi.tv/'
LOGPATH = xbmc.translatePath('special://logpath')
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
        if content:
            return True, content
        else:
            return False, "Log file is empty"
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
        elif 'message' in response.json():
            return False, "Unable to upload log file: " + response.json()['message']
        else:
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
    r = xbmcgui.Dialog().yesno(Script.localize(LABELS['Information']),
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
            Script.localize(LABELS['Information']),
            Script.localize(30862) + ': ' + error_message)

    return
