# SPDX-License-Identifier: GPL-3.0-or-later

import json
import socket

from resources.lib.actions.addonaction import AddonAction
from resources.lib.logger import Logger
from resources.lib.helpers.channelimporter import ChannelIndex


class IPTVManagerAction(AddonAction):
    def __init__(self, parameter_parser, request, port):
        """ Sending steam and EPG data to IPTV Manager

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        :param string request:          The data to query [channels, epg]
        :param integer port:            The port number to communicate with IPTV Manager

        """

        super(IPTVManagerAction, self).__init__(parameter_parser)

        self.__request = request
        self.__port = port
        self.__parameter_parser = parameter_parser

    def execute(self):
        """ Send the output of the wrappers to socket """

        Logger.debug("Execute IPTVManagerAction")
        if self.__request == "streams":
            self.send_streams()
        if self.__request == "epg":
            self.send_epg()


    def via_socket(func):
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.__port))
            try:
                sock.sendall(json.dumps(func(self)).encode())
            finally:
                sock.close()

        return send

    @via_socket
    def send_streams(self):
        """Return JSON-STREAMS formatted python datastructure to IPTV Manager"""
        streams = [] 
        channels = ChannelIndex.get_register().get_channels()
        for channel in channels:
            if channel.has_iptv:
                Logger.debug("Create IPTV streams for '%s'", channel.channelName)
                fetched_channel = channel.get_channel();
                streams += fetched_channel.create_iptv_streams(self.__parameter_parser)
                
        return dict(version=1, streams=streams)

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        epg = dict()
        channels = ChannelIndex.get_register().get_channels()
        for channel in channels:
            if channel.has_iptv:
                Logger.debug("Create EPG for '%s'", channel.channelName)
                fetched_channel = channel.get_channel()
                epg.update(fetched_channel.create_iptv_epg(self.__parameter_parser))

        return dict(version=1, epg=epg)
