# -*- coding: utf-8 -*-

from . import simple_requests as requests

class Playback:

    def __init__(self, plugin, data):
        self.plugin = plugin
        self.ManifestUrl = ''
        self.LaUrl = ''
        self.LaUrlAuthParam = ''
        self.Cdns = []
        self.get_detail(data.get('PlaybackPrecision', {}), data.get('PlaybackDetails', []))
    
    def clean_name(self, cdns):
        return [cdn.replace('live', '').replace('vod', '') for cdn in cdns]

    def get_detail(self, precision, details):
        if precision.get('Cdns'):
            self.Cdns = self.clean_name(precision['Cdns'])
        if self.Cdns:
            cdn = self.plugin.get_cdn(self.Cdns)
            if cdn:
                self.parse_detail(details, cdn)
            else:
                for i in self.Cdns:
                    self.parse_detail(details, i)
                    if self.ManifestUrl:
                        break
        if not self.ManifestUrl:
            self.parse_detail(details)

    def parse_detail(self, details, cdn=''):
        for i in details:
            if cdn == self.clean_name([i['CdnName']])[0] or not cdn:
                r = requests.head(i['ManifestUrl'])
                if r.status_code == 200:
                    self.ManifestUrl = i['ManifestUrl']
                    self.LaUrl = i['LaUrl']
                    self.LaUrlAuthParam = '{0}={1}'.format(i['LaUrlAuthParamName'], self.plugin.get_setting('mpx'))
                    break
