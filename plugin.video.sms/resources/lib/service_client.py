"""
    Copyright (C) 2020 Scott Ware
    This file is part of Scoot Media Streamer (plugin.video.sms)
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.txt for more information
"""

import requests

class ServiceClient(object):
    settings = None

    def __init__(self, settings):
        self.settings = settings

    def getSession(self):
        try:
            response = requests.get('http://localhost:' + str(self.settings['servicePort']) + '/session')
            data = response.text
            return data
        except requests.exceptions.RequestException:
            return None
            
    def update(self):
        try:
            response = requests.get('http://localhost:' + str(self.settings['servicePort']) + '/update')
            return True
        except requests.exceptions.RequestException:
            return False
