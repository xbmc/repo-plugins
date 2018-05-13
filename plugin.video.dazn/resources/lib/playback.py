# -*- coding: utf-8 -*-

import simple_requests as requests

class Playback:

    def __init__(self, plugin, data):
        self.plugin = plugin
        self.ManifestUrl = ''
        self.LaUrl = ''
        self.LaUrlAuthParam = ''
        self.parse_data(data.get('PlaybackDetails', []))

    def parse_data(self, data):
        for i in data:
            r = requests.head(i['ManifestUrl'])
            if r.status_code == 200:
                self.ManifestUrl = i['ManifestUrl']
                self.LaUrl = i['LaUrl']
                self.LaUrlAuthParam = '{0}={1}'.format(i['LaUrlAuthParamName'], self.plugin.get_setting('mpx'))
                break
