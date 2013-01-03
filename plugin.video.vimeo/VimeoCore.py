'''
   Vimeo plugin for XBMC
   Copyright (C) 2010-2012 Tobias Ussing And Henrik Mosgaard Jensen

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import sys, urllib
import xml.dom.minidom as minidom


class VimeoCore(object):

    def __init__(self):
        self.v = sys.modules["__main__"].client
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg
        self.utils = sys.modules["__main__"].utils
        self.login = sys.modules["__main__"].login
        self.common = sys.modules["__main__"].common

        self.hq_thumbs = self.settings.getSetting("high_quality_thumbs") == "true"

        if len(self.settings.getSetting("oauth_token")) > 0:
            self.oauth_token = self.settings.getSetting("oauth_token")

    def setLike(self, params):
        self.common.log("")
        get = params.get

        if (get("action") == "add_favorite"):
            result = self.v.vimeo_videos_setLike(like="true", video_id=get("videoid"), oauth_token=self.oauth_token)
        else:
            result = self.v.vimeo_videos_setLike(like="false", video_id=get("videoid"), oauth_token=self.oauth_token)

        self.common.log("Done")

        return self._get_return_status(result)

    def updateContact(self, params):
        self.common.log("")
        get = params.get

        if (get("action") == "add_contact"):
            result = self.v.vimeo_people_addContact(user_id=get("contact"), oauth_token=self.oauth_token)
        else:
            result = self.v.vimeo_people_removeContact(user_id=get("contact"), oauth_token=self.oauth_token)

        self.common.log("Done")

        return self._get_return_status(result)

    def addToAlbum(self, params):
        self.common.log("")
        get = params.get

        result = self.v.vimeo_albums_addVideo(album_id=get("album"), video_id=get("videoid"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def removeFromAlbum(self, params):
        self.common.log("")
        get = params.get

        result = self.v.vimeo_albums_removeVideo(album_id=get("album"), video_id=get("videoid"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def deleteAlbum(self, params):
        self.common.log("")
        get = params.get

        result = self.v.vimeo_albums_delete(album_id=get("album"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def createAlbum(self, params):
        self.common.log("")
        get = params.get

        result = self.v.vimeo_albums_create(title=get("title"), video_id=get("videoid"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def addToWatchLater(self, params):
        self.common.log("")
        get = params.get

        result = self.v.vimeo_albums_addToWatchLater(video_id=get("videoid"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def removeWatchLater(self, params):
        self.common.log("")
        get = params.get

        result = self.v.vimeo_albums_removeFromWatchLater(video_id=get("videoid"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def updateGroup(self, params):
        self.common.log("")
        get = params.get

        if (get("action") == "join_group"):
            result = self.v.vimeo_groups_join(group_id=get("group"), oauth_token=self.oauth_token)
        else:
            result = self.v.vimeo_groups_leave(group_id=get("group"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def updateSubscription(self, params):
        self.common.log("")
        get = params.get

        if (get("action") == "add_subscription"):
            result = self.v.vimeo_channels_subscribe(channel_id=get("channel"), oauth_token=self.oauth_token)
        else:
            result = self.v.vimeo_channels_unsubscribe(channel_id=get("channel"), oauth_token=self.oauth_token)

        self.common.log("Done")
        return self._get_return_status(result)

    def list(self, params):
        self.common.log("")
        get = params.get

        user_id = self.settings.getSetting("userid")
        if (get("external") or get("contact")):
            user_id = get("contact")

        page = int(get("page", "0")) + 1
        per_page = (10, 15, 20, 25, 30, 40, 50)[int(self.settings.getSetting("perpage"))]
        
        self.common.log("calling vimeo api for " + get("api","None") + " with user_id: " + repr(user_id) + " page: " + repr(page) + " per_page: " + repr(per_page), 4)

        if (get("channel")):
            result = self.v.vimeo_channels_getVideos(channel_id=get("channel"), page=page, per_page=per_page, full_response="true")
        elif (get("album")):
            result = self.v.vimeo_albums_getVideos(album_id=get("album"), page=page, per_page=per_page, full_response="true")
        elif (get("group")):
            result = self.v.vimeo_groups_getVideos(group_id=get("group"), page=page, per_page=per_page, full_response="true")
        elif (get("api") in ["channels", "groups", "categories"] and not get("category")):
            result = self.v.vimeo_categories_getAll(page=page, per_page=per_page)
        elif (get("api") == "channels" and get("category")):
            result = self.v.vimeo_categories_getRelatedChannels(category=get("category"), per_page=per_page, page=page)
        elif (get("api") == "groups" and get("category")):
            result = self.v.vimeo_categories_getRelatedGroups(category=get("category"), per_page=per_page, page=page)
        elif (get("api") == "categories" and get("category")):
            result = self.v.vimeo_categories_getRelatedVideos(category=get("category"), page=page, per_page=per_page, full_response="true")
        elif (get("api") == "my_videos"):
            result = self.v.vimeo_videos_getAll(user_id=user_id, per_page=per_page, page=page, full_response="true")
        elif(get("api") == "search"):
            query = urllib.unquote_plus(get("search"))
            result = self.v.vimeo_videos_search(query=query, page=page, per_page=per_page, full_response="true")
        elif (get("api") == "my_likes"):
            result = self.v.vimeo_videos_getLikes(user_id=user_id, per_page=per_page, page=page, full_response="true")
        elif (get("api") == "my_watch_later" and not get("external")):
            result = self.v.vimeo_albums_getWatchLater(per_page=per_page, page=page, full_response="true")
        elif (get("api") == "my_newsubscriptions"):
            result = self.v.vimeo_videos_getSubscriptions(user_id=user_id, per_page=per_page, page=page, full_response="true", sort="newest")
        elif (get("api") == "my_albums"):
            result = self.v.vimeo_albums_getAll(user_id=user_id, per_page=per_page, page=page, full_response="true")
        elif (get("api") == "my_groups"):
            result = self.v.vimeo_groups_getAll(user_id=user_id, per_page=per_page, page=page, full_response="true")
        elif (get("api") == "my_channels"):
            result = self.v.vimeo_channels_getAll(user_id=user_id, per_page=per_page, page=page, full_response="true")
        elif (get("api") == "my_contacts"):
            result = self.v.vimeo_contacts_getAll(user_id=user_id, per_page=per_page, page=page, full_response="true")

        if (not result):
            self.common.log("result was empty")
            return (result, 303)
        else:
            result = result.decode("utf-8","ignore")

        if get("folder") == "contact":
            result = self._get_contacts(result)
        elif get("folder") == "category":
            result = self._get_categories(result, params)
        elif get("folder"):
            result = self._get_list(get("folder"), result)
        else:
            result = self._getvideoinfo(result, params)

        self.common.log("Done")

        return (result, 200)

    def _get_return_status(self, result):
        self.common.log("")
        
        stat = self.common.parseDOM(result, "rsp", ret="stat")
        result = []
        if (len(stat) > 0):
            if stat[0] == "ok":
                return (result, 200)
            else:
                self.common.log("Got fail status from vimeo api: " + repr(result))
                return ("", 303)
        else:
            self.common.log("No response from vimeo api :" + repr(result))
        
        return ("No response from Vimeo API", 303)
    
    def _get_list(self, tag, result):
        self.common.log("")

        item = self.common.parseDOM(result, tag)
        item_id = self.common.parseDOM(result, tag, ret="id")

        result = []

        for i in range(0, len(item)):
            group = {}
            title = self.common.parseDOM(item[i], "title")
            if len(title) == 0:
                title = self.common.parseDOM(item[i], "name")

            group['Title'] = self.common.replaceHTMLCodes(title[0])

            group[tag] = item_id[i]

            description = self.common.parseDOM(item[i], "description")
            if len(description) > 0:
                group['Description'] = description[0]

            if (tag == "group"):
                logo_url = self.common.parseDOM(item[i], "logo_url")
                if len(logo_url) > 0:
                    group["thumbnail"] = logo_url[0]
                else:
                    group["thumbnail"] = "default"

            if (tag == "album"):
                group["thumbnail"] = self.getThumbnail(item[i], "default")

            if (tag == "channel"):
                thumbnail = ""
                badge_url = self.common.parseDOM(item[i], "badge_url")
                if len(badge_url) > 0:
                    if badge_url[0].rfind("default") == -1:
                        thumbnail = badge_url[0]

                if not thumbnail:
                    logo_url = self.common.parseDOM(item[i], "logo_url")
                    if len(logo_url) > 0:
                        if logo_url[0].rfind("default") == -1:
                            thumbnail = logo_url[0]
                if not thumbnail:
                    thumbnail = "default"

                group["thumbnail"] = thumbnail

            result.append(group)

        if len(result) == 0:
            self.common.log("Result was empty")

        self.common.log("Done")
        return result

    def _get_contacts(self, result):
        self.common.log("")

        ids = self.common.parseDOM(result, "contact", ret="id")
        titles = self.common.parseDOM(result, "contact", ret="display_name")
        portraits = self.common.parseDOM(result, "portraits")

        result = []

        for i in range(0, len(ids)):
            group = {}
            group['contact'] = ids[i]
            group['Title'] = titles[i]
            group['store'] = "contact_options"
            group['folder'] = "true"

            thumbs_width = self.common.parseDOM(portraits, "portrait", ret="width")
            thumbs_url = self.common.parseDOM(portraits, "portrait")
            for j in range(0, len(thumbs_width)):
                if int(thumbs_width[j]) <= 300:
                    group['thumbnail'] = thumbs_url[j]

            result.append(group)

        if len(result) == 0:
            self.common.log("Result was empty")
            return False

        self.common.log("Done")
        return result

    def _get_categories(self, result, params = {}):
        self.common.log("")
        get = params.get
        objects = []

        categories = self.common.parseDOM(result, "category", ret=True)

        for category in categories:
            id = self.common.parseDOM(category, "category", ret="word")[0]
            title = self.common.parseDOM(category, "name")[0]
            title = self.common.replaceHTMLCodes(title)
            item = {}
            item["category"] = id
            item["api"] = get("api")
            item["Title"] = title

            if get("api") == "channels":
                item["folder"] = "channel"
            elif get("api") == "groups":
                item["folder"] = "group"

            item["thumbnail"] = "explore"
            objects.append(item)

        if len(result) == 0:
            self.common.log("Result was empty")
            return False

        self.common.log("Done")
        return objects

    def checkIfMorePagesExist(self, value):
        next = True
        on_this_page = self.common.parseDOM(value, "videos", ret="on_this_page")
        total = self.common.parseDOM(value, "videos", ret="total")
        per_page = self.common.parseDOM(value, "videos", ret="perpage")
        page = self.common.parseDOM(value, "videos", ret="page")

        if (len(on_this_page) > 0 and len(per_page) > 0):
            if int(on_this_page[0]) < int(per_page[0]):
                next = False
            elif int(on_this_page[0]) == int(per_page[0]) and int(per_page[0]) * int(page[0]) == int(total[0]):
                next = False
        else:
            next = False

        return next

    def _getvideoinfo(self, value, params):
        get = params.get
        self.common.log("")

        vobjects = []

        next = self.checkIfMorePagesExist(value)

        video_list = self.common.parseDOM(value, u"video", ret=True)
        for entry in video_list:
            video = {}
            video['videoid'] = self.common.parseDOM(entry, "video",ret="id")[0]
            video['Title'] = self.common.replaceHTMLCodes(self.common.parseDOM(entry, "title")[0])
            video['Plot'] = self.common.replaceHTMLCodes(self.common.parseDOM(entry, "description")[0])
            video['Studio'] = self.common.parseDOM(entry, "owner", ret="display_name")[0]
            video['contact'] = self.common.parseDOM(entry, "owner", ret="id")[0]
            video['thumbnail'] = self.getThumbnail(entry, "default")

            duration = self.common.parseDOM(entry, "video", ret="duration")

            if len(duration) > 0:
                duration = int(duration[0])
                video['Duration'] = "%02d:%02d" % (duration / 60, duration % 60)

            overlay = self.settings.getSetting("vidstatus-" + video['videoid'])

            if overlay:
                video['Overlay'] = int(overlay)

            vobjects.append(video)

        if next and not get("fetch_all"):
            self.utils.addNextFolder(vobjects, params)

        self.common.log("Done")
        return vobjects
    
    def getThumbnail(self, item, default="default"):
        self.common.log("", 1)
        thumbs_width = self.common.parseDOM(item, "thumbnail", ret="width")
        thumbs_url = self.common.parseDOM(item, "thumbnail")
        
        for i in range(0, len(thumbs_width)):
            if (self.hq_thumbs):

                if (int(thumbs_width[i]) <= 640 and thumbs_url[i].rfind("default") == -1):
                    default = thumbs_url[i]
            else:
                if (int(thumbs_width[i]) <= 200 and thumbs_url[i].rfind("default") == -1):
                    default = thumbs_url[i]

        self.common.log("Done",4)
        return default
