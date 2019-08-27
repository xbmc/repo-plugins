# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os

import chn_class

from retroconfig import Config
from mediaitem import MediaItem
from logger import Logger
from urihandler import UriHandler
from helpers.ziphelper import ZipHelper
from xbmcwrapper import XbmcDialogProgressWrapper


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
        """Initializes the channel and will call some post processing stuff.

        This method is called for each add-on call and can be used to do some
        channel initialisation.

        """

        chn_class.Channel.__init__(self, channel_info)

        self.mainListUri = "#mainlist"
        self._add_data_parser(url="#mainlist", preprocessor=self.parse_radio_list)
        self._add_data_parser(url="*", preprocessor=self.parse_sub_list)

        #+==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "radionlimage.png"

        #===========================================================================================
        # non standard items

        # download the stream data
        self.__data_path = os.path.join(Config.cacheDir, "radio_data")
        Logger.debug("Checking '%s' for data", self.__data_path)
        if not os.path.isdir(self.__data_path):
            Logger.info("No data found at '%s', downloading stream data", self.__data_path)
            url = "http://www.rieter.net/repository.retrospect/" \
                  "plugin.video.retrospect.channel.streams/" \
                  "plugin.video.retrospect.channel.streams.radionl.data.zip"

            # give the user feedback
            progress_dialog = XbmcDialogProgressWrapper(
                "Downloading Data",
                "plugin.video.retrospect.channel.streams.radionl.data.zip", url)

            # download the zipfile
            zip_file = UriHandler.download(url, "plugin.video.retrospect.channel.streams.radionl.data.zip",
                                           self.get_default_cache_path(), progress_dialog)

            # and unzip it
            ZipHelper.unzip(zip_file, self.__data_path)

            if os.path.isdir(self.__data_path):
                Logger.info("Data successfully downloaded to: %s", self.__data_path)

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return
      
    def parse_radio_list(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        # read the regional ones
        # noinspection PyUnresolvedReferences
        Logger.info("Radio stations located at: %s", self.__data_path)
        regionals = os.listdir(os.path.join(self.__data_path, "Regionale Omroepen"))
        for regional in regionals:
            path = os.path.join(self.__data_path, "Regionale Omroepen", regional)
            if not os.path.isdir(path):
                continue
            item = MediaItem(regional, path)
            item.complete = True
            items.append(item)

        # add the National ones
        item = MediaItem("Nationale Radiozenders", os.path.join(self.__data_path))
        item.complete = True
        items.insert(0, item)

        item = MediaItem("Webradio", os.path.join(self.__data_path, "Webradio"))
        item.complete = True
        items.insert(0, item)
        return data, items
    
    def parse_sub_list(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        item = self.parentItem
        url = item.url
        items = []
        
        stations = os.listdir(url)
        for station in stations:
            if not station.endswith(".strm"):
                continue
            
            name = station.replace(".strm", "")
            stream = os.path.join(url, station)
            station_item = MediaItem(name, stream)
            station_item.icon = os.path.join(url, "%s%s" % (name, ".tbn"))
            station_item.complete = True
            station_item.description = station_item.name
            station_item.append_single_stream(stream)
            station_item.type = "playlist"
            station_item.thumb = station_item.icon
            items.append(station_item)

        return data, items
