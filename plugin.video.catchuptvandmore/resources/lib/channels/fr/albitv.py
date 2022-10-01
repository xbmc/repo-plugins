# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

import re
import urlquick

from codequick import Listitem, Route

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = "https://www.albi-tv.fr"
URL_CATCHUP = URL_ROOT + "/replay"
URL_LIVE = "https://www.creacast.com/play.php?su=albi-tv-ch1"


@Route.register
def list_videos_emissions(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_CATCHUP, headers={"User-Agent": web_utils.get_random_ua()})
    data = re.compile(r'direction-container.+?name":"([^"]+)".+?:"([^"]+)".+?:"([^"]+)"', re.DOTALL | re.MULTILINE).findall(resp.text)

    for content in data:
        item = Listitem()
        item.label = content[0]
        if "e800" in content[2]:
            item.art['thumb'] = content[1]
        else:
            item.info['plot'] = content[1]
            item.art['thumb'] = content[2]
        item.set_callback(list_videos,
                          item_id=data.index(content))
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, **kwargs):
    headers = {"User-Agent": web_utils.get_random_ua()}

    # Yes, it's ugly but need by the website...
    params = {
        "appDefinitionIdToSiteRevision": '{"13d21c63-b5ec-5912-8397-c3a5ddb27a97":"440","14bcded7-0066-7c35-14d7-466cb3f09103":"222"}',
        "beckyExperiments": "specs.thunderbolt.responsiveAbsoluteChildrenPosition:true,specs.thunderbolt.byRefV2:true,specs.thunderbolt.DatePickerPortal:true,specs.thunderbolt.LinkBarPlaceholderImages:true,specs.thunderbolt.carmi_simple_mode:true,specs.thunderbolt.final_image_auto_encode:true,specs.thunderbolt.premiumDocumentLink:true,specs.thunderbolt.prefetchComponentsShapesInBecky:true,specs.thunderbolt.inflatePresetsWithNoDefaultItems:true,specs.thunderbolt.maskImageCSS:true,specs.thunderbolt.SearchBoxModalSuggestions:true",
        "contentType": "application/json",
        "dfCk": "6",
        "dfVersion": "1.1581.0",
        "excludedSafariOrIOS": "false",
        "experiments": "bv_remove_add_chat_viewer_fixer,dm_enableDefaultA11ySettings,dm_fixStylableButtonProperties,dm_fixVectorImageProperties,dm_linkRelDefaults,dm_migrateToTextTheme",
        "externalBaseUrl": URL_ROOT,
        "fileId": "d6fe5896.bundle.min",
        "hasTPAWorkerOnSite": "false",
        "isHttps": "true",
        "isInSeo": "false",
        "isPremiumDomain": "true",
        "isUrlMigrated": "true",
        "isWixCodeOnPage": "false",
        "isWixCodeOnSite": "false",
        "language": "fr",
        "metaSiteId": "f40dc1b3-7269-48b2-afa8-74d3b20f1f32",
        "module": "thunderbolt-platform",
        "originalLanguage": "en",
        "pageId": "6081ef_49d4ee283307414e0ddcabdb5ee6ea68_363.json",
        "quickActionsMenuEnabled": "false",
        "registryLibrariesTopology": '[{"artifactId":"editor-elements","namespace":"wixui","url":"https://static.parastorage.com/services/editor-elements/1.7884.0"},{"artifactId":"editor-elements","namespace":"dsgnsys","url":"https://static.parastorage.com/services/editor-elements/1.7884.0"}]',
        "remoteWidgetStructureBuilderVersion": "1.229.0",
        "siteId": "af621213-b9a8-4c1b-aba6-9b0458b47ebf",
        "siteRevision": "422",
        "viewMode": "desktop"}
    resp = urlquick.get("https://siteassets.parastorage.com/pages/pages/thunderbolt", params=params, headers=headers).text
    appID = re.search(r'applications":\{"(.+?)"', resp).group(1)
    compID = re.findall(r'compId":"(.+?)"', resp)[int(item_id)]
    channelId = re.findall(compID + '".+?channelId":"(.+?)"', resp)

    if len(channelId) == 1:
        channelId = channelId[0]
    else:
        channelId = channelId[1]

    resp = urlquick.get(URL_ROOT + "/_api/v2/dynamicmodel", headers=headers)
    instance = re.search(appID + '".+?instance":"(.+?)"', resp.text).group(1)

    params = {
        "siteUrl": URL_ROOT,
        "fullSiteUrl": URL_ROOT + "/replay",
        "channelId": channelId,
        "instance": instance,
        "locale": "fr",
        "isV3Api": "false",
    }

    data = urlquick.get(URL_ROOT + "/wix-vod-server/widget-data", params=params, headers=headers).json()["__VIDEOS__"]["items"]

    for content in data:
        item = Listitem()
        item.label = content["title"]
        item.info['plot'] = content["description"]
        if content.get("custom_uploaded_cover_url"):
            item.art['thumb'] = "https://images-vod.wixmp.com/" + content["custom_uploaded_cover_url"]
        else:
            item.art['thumb'] = "https://images-vod.wixmp.com/" + content["cover_url"]
        item.set_callback(get_video_url,
                          item_id="https://vod.wix.com/public/play/" + content["item_id"] + "?instance=" + instance + '&channel_id=' + channelId)
        item_post_treatment(item)
        yield item


@Resolver.register
def get_video_url(plugin, item_id, **kwargs):

    resp = urlquick.get(item_id, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1).json()

    video_url = resp["hls.m3u8"]
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    video_url = re.compile(r'file: "(.*?)[\?\"]').findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
