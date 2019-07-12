#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

from datetime import datetime

from logger import Logger
from urihandler import UriHandler
from addonsettings import AddonSettings
from helpers.htmlentityhelper import HtmlEntityHelper
from retroconfig import Config


class Statistics(object):
    __STATISTICS = "Statistics"
    __ERRORS = "Errors"
    __ACTION_PLAY = "Play"
    __ACTION_LIST = "List"
    __ACTION_CHANNEL = "Channel"

    def __init__(self):
        """
        Category    Action          Label               Value           Referer
        ================================================================================
        Statistics  CDN             <cdn-url>           <bytes>         -
        Statistics  <channelname>   Channel             1               -
        Statistics  <channelname>   Play: <name>        1               <url>
        Errors      <channelname>   List: <name>        1               <url>
        Errors      <channelname>   Play: <name>        1               <url>
        """
        raise ValueError("Cannot and should not create an instance")

    @staticmethod
    def register_cdn_bytes(total_bytes):
        """ Register the bytes transfered via CDN

        @param total_bytes: int - The total bytes transfered
        """

        Statistics.__register_hit(Statistics.__STATISTICS,
                                  "CDN", Config.textureUrl, value=total_bytes)

    @staticmethod
    def register_error(channel, title="Channel", item=None):
        """ Register an empty list for a specific Channel and Title

        @param channel: Channel : The channel that had the error
        """

        referer = None

        if item is None:
            item = channel.parentItem

        if item is not None:
            if item.isPaid or item.isDrmProtected:
                Logger.debug("Not registering error of item which is Paid or DRM Protected.")
                return

            title = item.name
            referer = item.url
            if item.is_playable():
                title = "%s: %s" % (Statistics.__ACTION_PLAY, title)
            else:
                title = "%s: %s" % (Statistics.__ACTION_LIST, title)

        Statistics.__register_hit(Statistics.__ERRORS, channel.channelName, title,
                                  value=1, referer=referer,
                                  app_version=channel.version, app_id=channel.id)

    @staticmethod
    def register_channel_open(channel, start_time=None):
        """ Register a Channel loading

        Arguments:
        channel  : String   - Name of the channel

        Keyword Arguments:
        starTime : datetime - The start time of the add-on
        """

        duration = None
        if start_time:
            time_delta = (datetime.now() - start_time)
            duration = time_delta.seconds * 1000 + (time_delta.microseconds // (10 ** 3))

        Statistics.__register_hit(Statistics.__STATISTICS, channel.channelName,
                                  Statistics.__ACTION_CHANNEL,
                                  value=duration,
                                  app_version=channel.version, app_id=channel.id)

    @staticmethod
    def register_playback(channel, item, start_time=None, offset=0):
        """ Register a video playback

        Arguments:
        channel  : String    - Name of the channel
        item :     MediaItem - The item that is playing


        Keyword Arguments:
        starTime : datetime - The start time of the add-on
        offSet   : int      - Milli seconds to substract due to downloading

        """

        duration = offset
        time_delta = None
        if start_time:
            time_delta = (datetime.now() - start_time)
            duration = time_delta.seconds * 1000 + (time_delta.microseconds // (10 ** 3)) + offset
        Logger.trace("Duration set to: %s (%s, offset=%s)", duration, time_delta or "None", offset)

        action = "%s: %s" % (Statistics.__ACTION_PLAY, item.name)
        Statistics.__register_hit(Statistics.__STATISTICS, channel.channelName, action,
                                  value=duration, referer=item.url,
                                  app_version=channel.version, app_id=channel.id)

    @staticmethod
    def __register_hit(category, action, label,
                       value=None, referer=None, app_version=None, app_id=None):
        """ Register an event with Google Analytics

        @param category:    String - Name of category to register
        @param action:      String - Name of action to register
        @param value:       String - Value of action to register
        @param label:       String - The label for the event
        @param value:       int    - The value for the event (Defaults to None)
        @param referer:     String - The referer (Defaults to None)
        @param app_version:  String - Version of the channel
        @param app_id:       String - ID of the channel

        See: https://ga-dev-tools.appspot.com/hit-builder/
        v=1&t=event&tid=UA-3902785-1&cid=3c8961be-6a53-48f6-bded-d136760ab55f&ec=Test&ea=Test%20Action&el=Test%20%5Blabel)&ev=100

        """

        return

        # No statistics logging allowed for the Kodi repository
        # try:
        #     if not AddonSettings.send_usage_statistics():
        #         Logger.debug("Not sending statistics because the configuration does not allow this.")
        #         return
        #
        #     post_data = {
        #         "v": 1,
        #         "t": "event",
        #         "tid": Config.googleAnalyticsId,
        #         "cid": AddonSettings.get_client_id(),
        #         "ec": HtmlEntityHelper.url_encode(category),
        #         # "ec": HtmlEntityHelper.url_encode("Test"),
        #         "ea": HtmlEntityHelper.url_encode(HtmlEntityHelper.convert_html_entities(action)),
        #         "el": HtmlEntityHelper.url_encode(HtmlEntityHelper.convert_html_entities(label)),
        #         "an": Config.appName
        #     }
        #
        #     if value is not None:
        #         post_data["ev"] = value
        #     if app_version is not None and app_id is not None:
        #         post_data["av"] = app_version
        #         post_data["aid"] = app_id
        #
        #     if referer is not None:
        #         if "://" not in referer:
        #             referer = "http://%s" % (referer,)
        #         post_data["dr"] = HtmlEntityHelper.url_encode(referer)
        #
        #     url = "https://www.google-analytics.com/collect"
        #     data = ""
        #     for k, v in post_data.items():
        #         data += "%s=%s&" % (k, v)
        #     data = data.rstrip("&")
        #
        #     Logger.debug("Sending statistics: %s", data)
        #
        #     # now we need something async without caching
        #     user_agent = AddonSettings.get_user_agent()
        #     if user_agent:
        #         result = UriHandler.open(url, additional_headers={"User-Agent": user_agent}, params=data, no_cache=True)
        #     else:
        #         result = UriHandler.open(url, params=data, no_cache=True)
        #     if len(result) > 0:
        #         Logger.debug("Statistics were successfully sent. Content Length: %d", len(result))
        #     else:
        #         Logger.warning("Statistics were not successfully sent")
        # except:
        #     # we should never ever fail here
        #     Logger.warning("Cannot send statistics", exc_info=True)
        #     return
