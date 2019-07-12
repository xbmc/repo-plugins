import chn_class
from mediaitem import MediaItem
from helpers import datehelper


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
        """Initialisation of the class.

        WindowXMLDialog(self, xmlFilename, scriptPath[, defaultSkin, defaultRes]) -- Create a new WindowXMLDialog script.

        xmlFilename     : string - the name of the xml file to look for.
        scriptPath      : string - path to script. used to fallback to if the xml doesn't exist in the current skin. (eg os.getcwd())
        defaultSkin     : [opt] string - name of the folder in the skins path to look in for the xml. (default='Default')
        defaultRes      : [opt] string - default skins resolution. (default='720p')

        *Note, skin folder structure is eg(resources/skins/Default/720p)

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "gelderlandimage.png"

        # setup the urls
        self.mainListUri = "http://www.omroepgelderland.nl/web/Uitzending-gemist-5/TV-1/Programmas/Actuele-programmas.htm"
        self.baseUrl = "http://www.omroepgelderland.nl"
        self.swfUrl = "%s/design/channel/tv/swf/player.swf" % (self.baseUrl, )

        # setup the main parsing data
        self.episodeItemRegex = r'<a href="(/web/Uitzending-gemist-5/TV-1/Programmas/' \
                                r'Programma.htm\?p=[^"]+)"\W*>\W*<div[^>]+>\W+<img src="([^"]+)' \
                                r'"[^>]+>\W+</div>\W+<div[^>]+>([^<]+)'
        self.videoItemRegex = r"""<div class="videouitzending[^>]+\('([^']+)','[^']+','[^']+','[^']+','([^']+) (\d+) (\w+) (\d+)','([^']+)','([^']+)'"""
        self.mediaUrlRegex = r'<param\W+name="URL"\W+value="([^"]+)"'
        self.pageNavigationRegex = r'(/web/Uitzending-gemist-5/TV-1/Programmas/Programma.htm\?p=' \
                                   r'Debuzz&amp;pagenr=)(\d+)[^>]+><span>'
        self.pageNavigationRegexIndex = 1

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return
    
    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = MediaItem(result_set[2], "%s%s" % (self.baseUrl, result_set[0]))
        item.icon = self.icon
        item.thumb = "%s%s" % (self.baseUrl, result_set[1])
        item.complete = True
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

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        #Logger.Trace(result_set)
        
        thumb_url = "%s%s" % (self.baseUrl, result_set[6])
        url = "%s%s" % (self.baseUrl, result_set[5])
        name = "%s %s %s %s" % (result_set[1], result_set[2], result_set[3], result_set[4])
        
        video_url = result_set[0]
        video_url = video_url.replace(" ", "%20")
        # convert RTMP to HTTP
        #rtmp://media.omroepgelderland.nl         /uitzendingen/video/2012/07/120714 338 Carrie on.mp4
        #http://content.omroep.nl/omroepgelderland/uitzendingen/video/2012/07/120714 338 Carrie on.mp4
        video_url = video_url.replace("rtmp://media.omroepgelderland.nl",
                                      "http://content.omroep.nl/omroepgelderland")
        
        item = MediaItem(name, url)
        item.thumb = thumb_url
        item.icon = self.icon
        item.type = 'video'
        item.append_single_stream(video_url)
        
        # set date
        month = datehelper.DateHelper.get_month_from_name(result_set[3], "nl", False)
        day = result_set[2]
        year = result_set[4]
        item.set_date(year, month, day)
        
        item.complete = True
        return item
