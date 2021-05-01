# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============

        if self.channelCode == "ketnet":
            self.noImage = "ketnetimage.jpg"
            self.mainListUri = self.__get_graph_url("content/ketnet/nl/kijken.model.json")
            self.baseUrl = "https://www.ketnet.be"
            self.mediaUrlRegex = r'playerConfig\W*=\W*(\{[\w\W]{0,2000}?);(?:.vamp|playerConfig)'

        else:
            raise IndexError("Unknow channel code {}".format(self.channelCode))

        self._add_data_parser(
            self.mainListUri, json=True, name="MainList Parser for GraphQL",
            parser=["data", "page", "pagecontent",
                    ("id", "/content/ketnet/nl/kijken/jcr:content/root/swimlane_64598007", 0),
                    "items"], creator=self.create_typed_item)

        self._add_data_parser("https://senior-bff.ketnet.be/graphql?query=query%20GetPage%28",
                              name="Generic GraphQL Parser", json=True,
                              parser=["data", "page", "tabs", ("type", "playlists", 0), "playlists"],
                              creator=self.create_typed_item, updater=self.update_video_item,
                              postprocessor=self.check_single_folder)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # noinspection PyUnusedLocal
    def check_single_folder(self, data, items):
        """ Performs post-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str|JsonHelper data:     The retrieve data that was loaded for the
                                         current item and URL.
        :param list[MediaItem] items:   The currently available items

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: list[MediaItem]

        """

        Logger.info("Performing Post-Processing")
        if len(items) == 1:
            item = items[0]
            if item.is_folder and item.items:
                return item.items

        Logger.debug("Post-Processing finished")
        return items

    def create_typed_item(self, result_set):
        """ Creates a new MediaItem for a typed item.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        type_id = result_set["__typename"]
        if type_id == "Program":
            return self.create_program_item(result_set)
        elif type_id == "Playlist":
            return self.create_playlist_item(result_set)
        elif type_id == "Video":
            return self.create_video_item(result_set)
        else:
            Logger.warning("Unknown Graph Type: %s", type_id)

        return None

    def create_program_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        url = self.__get_graph_url(result_set["id"])
        item = MediaItem(result_set["title"], url)
        item.poster = result_set["posterUrl"]
        return item

    def create_playlist_item(self, result_set):
        """ Creates a new MediaItem for a playlist of seasons.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["title"]
        url = "{}/{}".format(self.parentItem.url, title)
        item = MediaItem(result_set["title"], url)
        item.poster = result_set.get("imageUrl")
        items = result_set["items"]
        for sub_item in items:
            video_item = self.create_typed_item(sub_item)
            if video_item:
                item.items.append(video_item)
        return item

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        video_id = result_set["id"]
        item = MediaItem(result_set["titlePlaylist"], self.__get_graph_url(video_id))
        item.media_type = mediatype.EPISODE
        item.description = result_set.get("description")
        item.thumb = result_set.get("imageUrl")

        duration = int(result_set.get("duration", 0) / 1000)
        if duration:
            item.set_info_label("duration", duration)

        allowed_region = result_set.get("allowedRegion", "").lower()
        item.isGeoLocked = allowed_region != "world"
        return item

    def update_video_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)
        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)
        player_info = json_data.get_value("data", "page", "vrtPlayer")
        client_code = player_info["clientCode"]
        media_refernce_pbs = player_info["mediaReference"]

        hls_over_dash = self._get_setting("hls_over_dash", 'false') == 'true'

        from resources.lib.streams.vualto import Vualto
        v = Vualto(self, client_code)
        item = v.get_stream_info(item, media_refernce_pbs, hls_over_dash=hls_over_dash)
        return item

    def __get_graph_url(self, id):
        graph_query = "query GetPage($id: String!) { page(id: $id) { ... on Program { pageType ...program __typename } ... on Video { pageType ...video __typename } ... on Pagecontent { pageType ...pagecontent __typename } __typename } }  fragment program on Program { id title header { ...header __typename } activeTab tabs { name title type playlists { ...seasonOverviewTabItem __typename } pagecontent { ...pagecontentItem __typename } __typename } __typename }  fragment seasonOverviewTabItem on Playlist { name title type imageUrl items { id titlePlaylist subtitlePlaylist scaledPoster { ...scaledImage __typename } allowedRegion duration episodeNr seasonTitle imageUrl availableUntilDate publicationDate description __typename } __typename }  fragment video on Video { id videoType titleVideodetail subtitleVideodetail scaledPoster { ...scaledImage __typename } description availableUntilDate publicationDate duration episodeNr vrtPlayer { ...vrtPlayerFragment __typename } suggestions { id titleSuggestion subtitleSuggestion scaledPoster { ...scaledImage __typename } __typename } playlists { name title items { id titlePlaylist subtitlePlaylist scaledPoster { ...scaledImage __typename } description __typename } __typename } activePlaylist trackingData { programName seasonName episodeName episodeNr episodeBroadcastDate __typename } __typename }  fragment pagecontent on Pagecontent { pagecontent { ...pagecontentItem __typename } __typename }  fragment pagecontentItem on PagecontentItem { ... on Header { ...header __typename } ... on Highlight { ...highlight __typename } ... on Swimlane { ...swimlane __typename } __typename }  fragment highlight on Highlight { type title description link linkItem { ... on Game { id __typename } ... on Program { id __typename } ... on Story { id __typename } ... on Theme { id __typename } ... on Video { id __typename } __typename } buttonText imageUrl size __typename }  fragment swimlane on Swimlane { id type title style items { ... on Video { ...swimlaneVideo __typename } ... on Program { ...swimlaneProgram __typename } __typename } __typename }  fragment swimlaneVideo on Video { id type title imageUrl titleSwimlane subtitleSwimlane duration __typename }  fragment swimlaneProgram on Program { id type title accentColor imageUrl logoUrl posterUrl __typename }  fragment scaledImage on ScaledImage { small medium large __typename }  fragment vrtPlayerFragment on VrtPlayerConfig { mediaReference aggregatorUrl clientCode __typename }  fragment header on Header { type title description imageUrl logoUrl __typename }"
        graph_id = "{{\"id\": \"{}\"}}".format(id)
        graph_url = "https://senior-bff.ketnet.be/graphql?query={}&variables={}".format(
            HtmlEntityHelper.url_encode(graph_query),
            HtmlEntityHelper.url_encode(graph_id)
        )
        return graph_url
