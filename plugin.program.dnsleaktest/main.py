# -*- coding: utf-8 -*-

import json
import requests
import sys
import xbmcgui
import xbmcplugin

from platform import system as system_name
from random import randint
from subprocess import call as system_call

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]

# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])


def ping(host):
    param = '-n' if system_name().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    if system_name().lower() == 'windows':
        retcode = system_call(command, creationflags=0x00000008)
        return retcode == 0
    else:
        retcode = system_call(command)


def set_label(label):
    list_item = xbmcgui.ListItem(label=label)
    xbmcplugin.addDirectoryItem(_handle, 'plugin://', list_item, False)


def list_data(parsed_data, d_type):
    for dns_server in parsed_data:
        if dns_server['type'] == d_type:
            if dns_server['country_name']:
                if dns_server['asn']:
                    set_label(dns_server['ip']
                              + " [" + dns_server['country_name']
                              + ", " + dns_server['asn']
                              + "]")

                else:
                    set_label(dns_server['ip']
                              + " [" + dns_server['country_name']
                              + "]")

            else:
                set_label(str(dns_server['ip']))


if __name__ == '__main__':

    xbmcplugin.setPluginCategory(_handle, 'APP')
    xbmcplugin.setContent(_handle, 'files')

    leak_id = randint(1000000, 9999999)
    for x in range(0, 10):
        ping('.'.join([str(x), str(leak_id), "bash.ws"]))

    url = "https://bash.ws/dnsleak/test/" + str(leak_id) + "?json"

    response = requests.get(url)
    parsed_data = json.loads(response.content)

    set_label('Your IP:')
    list_data(parsed_data, "ip")

    servers = 0

    for dns_server in parsed_data:
        if dns_server['type'] == "dns":
            servers = servers + 1

    if servers == 0:
        set_label("No DNS servers found")

    else:
        set_label("You use " + str(servers) + " DNS servers:")
        list_data(parsed_data, "dns")

    set_label("Conclusion:")

    for dns_server in parsed_data:
        if dns_server['type'] == "conclusion":
            if dns_server['ip']:
                set_label(str(dns_server['ip']))

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)
