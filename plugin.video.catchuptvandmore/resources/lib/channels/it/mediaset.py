# -*- coding: utf-8 -*-
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import urlquick

from codequick import Resolver

URL_CHANNELS = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_CHANNELS)
    data = json.loads(resp.text)["entries"]
    for item in data:
        if item["callSign"] == item_id:
            for source in item["tuningInstruction"]["urn:theplatform:tv:location:any"]:
                if source["format"] == "application/x-mpegURL" and "geoIT" in source["assetTypes"]:
                    return source["publicUrls"][0]
    return False
