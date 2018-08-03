# -*- coding: utf-8 -*-

import simple_requests as requests

class Playback:

    def __init__(self, plugin, data):
        self.plugin = plugin
        self.ManifestUrl = ''
        self.LaUrl = ''
        self.LaUrlAuthParam = ''
        self.get_detail(data.get('PlaybackPrecision', {}), data.get('PlaybackDetails', []))

    def compatible(self, cdn):
        result = False
        for i in self.plugin.compatibility_list:
            if i in cdn:
                result = True
        return result

    def get_detail(self, precision, details):
        if precision.get('Cdns') and self.plugin.compatibility_mode:
            cdns = precision['Cdns']
            for i in cdns:
                if self.compatible(i):
                    self.parse_detail(details, i)
                    if self.ManifestUrl:
                        break
        if not self.ManifestUrl:
            self.parse_detail(details)

    def parse_detail(self, details, cdn=''):
        for i in details:
            if cdn == i['CdnName'] or not cdn:
                r = requests.head(i['ManifestUrl'])
                if r.status_code == 200:
                    self.ManifestUrl = i['ManifestUrl']
                    self.LaUrl = i['LaUrl']
                    self.LaUrlAuthParam = '{0}={1}'.format(i['LaUrlAuthParamName'], self.plugin.get_setting('mpx'))
                    break
