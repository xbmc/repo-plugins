# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype, contenttype

from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper


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
            self.mainListUri = "#mainlist"
            self.baseUrl = "https://www.ketnet.be"
            self.mediaUrlRegex = r'playerConfig\W*=\W*(\{[\w\W]{0,2000}?);(?:.vamp|playerConfig)'

        else:
            raise IndexError("Unknow channel code {}".format(self.channelCode))

        self._add_data_parser(
            self.mainListUri, json=True, name="MainList Parser for GraphQL",
            preprocessor=self.get_graphql_post,
            parser=[
                "data", "page", "pagecontent",
                ("id", "/conf/tenants/ketnet/settings/wcm/templates/home-page-template/structure/jcr:content/root/heroes", 0),
                "items"
            ], creator=self.create_typed_item)

        self._add_data_parser("*",
                              name="Generic GraphQL Parser", json=True,
                              preprocessor=self.get_graphql_post,
                              parser=["data", "page", "tabsV2", ("type", "playlists", 0), "playlists"],
                              creator=self.create_typed_item, updater=self.update_video_item,
                              postprocessor=self.check_single_folder)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # noinspection PyUnusedLocal
    def get_graphql_post(self, data=None, item=None):
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

        if self.parentItem:
            json_params = self.__get_graph_post_data("GetPage", self.parentItem.metaData["id"])
        elif item:
            json_params = self.__get_graph_post_data("GetPage", item.metaData["id"])
        else:
            json_params = self.__get_graph_post_data("GetPage", "content/ketnet/nl.model.json")
        data = UriHandler.open("https://senior-bff.ketnet.be/graphql", json=json_params)

        json_data = JsonHelper(data)
        return json_data, []

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
        elif type_id == "Swimlane":
            return self.create_swimlane_item(result_set)
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

        item_id = result_set["id"]
        # Set an #-url style
        url = "#programId={}".format(item_id)
        item = MediaItem(result_set["title"], url)
        item.metaData["id"] = item_id
        item.poster = result_set.get("posterUrl")
        return item

    def create_swimlane_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["title"] or (result_set.get("buttonText") or "").title()
        if not title:
            return None

        swimlane_id = result_set["id"]
        url = "#swimlaneId={}".format(swimlane_id)
        item = FolderItem(title, url, content_type=contenttype.TVSHOWS)
        item.description = result_set.get("description")
        item.metaData["id"] = swimlane_id
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

        url = "#playlist={}".format(result_set["name"])
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
        url = "#videoId={}".format(video_id)
        title = result_set.get("titlePlaylist", result_set.get("titleSwimlane"))

        item = MediaItem(title, url)
        item.media_type = mediatype.EPISODE
        item.metaData["id"] = video_id
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
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        json_data, _ = self.get_graphql_post(item=item)
        player_info = json_data.get_value("data", "page", "vrtPlayer")
        client_code = player_info["clientCode"]
        media_refernce_pbs = player_info["mediaReference"]

        hls_over_dash = self._get_setting("hls_over_dash", 'false') == 'true'

        from resources.lib.streams.vualto import Vualto
        v = Vualto(self, client_code)
        item = v.get_stream_info(item, media_refernce_pbs, None, hls_over_dash=hls_over_dash)
        return item

    def __get_graph_post_data(self, operation, item_id):
        graph_query = "query GetPage($id: String!, $feedPostPageSize: Int!, $feedPostCommentPageSize: Int!) { page(id: $id) { ... on Program { pageType ...program __typename } ... on Theme { pageType ...theme __typename } ... on Video { pageType ...video __typename } ... on Game { pageType ...game __typename } ... on Pagecontent { pageType ...pagecontent __typename } __typename }}fragment game on Game { id title imageUrl orientation gameUrl gameType requiresSdk hideCloseButton permissions __typename} fragment program on Program { id title header { ...header __typename } activeTab tabsV2 { ... on FeedTab { ...feedTab __typename } ... on PlaylistsTab { ...playlistsTab __typename } ... on PageContentTab { ...pageContentTab __typename } ... on LinkTab { ...linkTab __typename } __typename } __typename}fragment feedTab on FeedTab { id name title type disableComments paginatedPosts(first: $feedPostPageSize) { edges { node { ...postFragment ...ctaPostFragment __typename } cursor __typename } totalCount next __typename } characterFiltersTitle filterOnCharacters characters { id imageUrl title characterDisabled __typename } theming { backgroundColor foregroundColor buttonColor loginButtonColor __typename } __typename}fragment playlistsTab on PlaylistsTab { name title type playlists { ...seasonOverviewTabItem __typename } __typename}fragment pageContentTab on PageContentTab { name title type pagecontent { ...pagecontentItem __typename } __typename}fragment linkTab on LinkTab { id name linkItem { ... on Game { id userHasVoted gameType __typename } ... on Program { id __typename } ... on Story { id __typename } ... on Theme { id __typename } ... on Video { id __typename } __typename } title type __typename}fragment seasonOverviewTabItem on Playlist { name title type imageUrl items { id titlePlaylist subtitlePlaylist scaledPoster { ...scaledImage __typename } description duration __typename } __typename}fragment theme on Theme { id title header { ...header __typename } pagecontent { ...pagecontentItem __typename } __typename}fragment video on Video { id videoType titleVideodetail subtitleVideodetail metaTitle scaledPoster { ...scaledImage __typename } description availableUntilDate publicationDate duration episodeNr vrtPlayer { ...vrtPlayerFragment __typename } suggestions { id titleSuggestion subtitleSuggestion scaledPoster { ...scaledImage __typename } duration __typename } playlists { name title items { id titlePlaylist subtitlePlaylist scaledPoster { ...scaledImage __typename } description duration __typename } __typename } activePlaylist trackingData { programName seasonName episodeName episodeNr episodeBroadcastDate __typename } likedByMe likes __typename}fragment pagecontent on Pagecontent { title pagecontent { ...pagecontentItem __typename } __typename}fragment pagecontentItem on PagecontentItem { ... on Header { ...header __typename } ... on Highlight { ...highlight __typename } ... on Jumbotron { ...jumbotron __typename } ... on MultiHighlight { ...multiHighlight __typename } ... on Swimlane { ...swimlane __typename } __typename}fragment highlight on Highlight { type title description link linkItem { ... on Game { id __typename } ... on Program { id __typename } ... on Story { id __typename } ... on Theme { id __typename } ... on Video { id __typename } __typename } buttonText imageUrl size fullWidthEnabled fullWidthImageUrl fullWidthBackgroundUrl __typename}fragment jumbotron on Jumbotron { linkText link backgroundImageUrl showButtonTime onTime offTime type __typename}fragment multiHighlight on MultiHighlight { type highlights { type title description link linkItem { ... on Game { id __typename } ... on Program { id __typename } ... on Story { id __typename } ... on Theme { id __typename } ... on Video { id __typename } __typename } buttonText imageUrl size __typename } __typename}fragment swimlane on Swimlane { id type title style items { ... on Video { ...swimlaneVideo __typename } ... on Theme { ...swimlaneTheme __typename } ... on Game { ...swimlaneGame __typename } ... on Story { ...swimlaneStory __typename } ... on Program { ...swimlaneProgram __typename } ... on Peetie { ...swimlanePeetie __typename } __typename } __typename}fragment swimlaneVideo on Video { id type title imageUrl titleSwimlane subtitleSwimlane duration __typename}fragment swimlaneTheme on Theme { id type title accentColor imageUrl logoUrl animation __typename}fragment swimlaneGame on Game { id type title imageUrl gameType __typename}fragment swimlaneStory on Story { id type title imageUrl topReaction { ...storyReaction __typename } __typename}fragment swimlaneProgram on Program { id type title accentColor imageUrl logoUrl posterUrl __typename}fragment swimlanePeetie on Peetie { id alt type imageUrl imageUrls movies { alt position gifUrl webmUrl mp3Url gifFrames __typename } __typename}fragment scaledImage on ScaledImage { small medium large __typename}fragment vrtPlayerFragment on VrtPlayerConfig { mediaReference aggregatorUrl clientCode aspectRatio __typename}fragment header on Header { type title description imageUrl logoUrl height __typename}fragment postFragment on Post { id postedOn author { name avatarUrl __typename } message media { ... on PostMediaVideo { type vrtPlayer { ...vrtPlayerFragment __typename } scaledPoster { ...scaledImage __typename } __typename } ... on PostMediaPicture { type scaledImage { ...scaledImage __typename } __typename } __typename } paginatedComments(first: $feedPostCommentPageSize) { edges { node { ...postCommentFragment __typename } cursor __typename } totalCount next __typename } reactions { id count __typename } myReaction sticky type __typename}fragment ctaPostFragment on CtaPost { id title description ctaLinkItem { ... on Game { id type __typename } ... on Program { id type __typename } ... on Story { id type __typename } ... on Theme { id type __typename } ... on Video { id type __typename } __typename } ctaText ctaAlt type __typename}fragment postCommentFragment on PostComment { postId commentId author { name avatarUrl __typename } message postedOn mine __typename}fragment storyReaction on StoryReaction { name count __typename}"
        graph_json = {
            "operationName": operation,
            "variables": {
                "id": item_id,
                "feedPostPageSize": 10,
                "feedPostCommentPageSize": 3
            },
            "query": graph_query
        }
        return graph_json
