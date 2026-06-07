from resources.lib.skyitalia import SkyItalia
from resources.lib import addonutils
from resources.lib.translate import translatedString as T


class SkyVideoItalia(object):
    def __init__(self):
        self.ISA = addonutils.getSettingAsBool('UseInputStream')
        self.QUALITY = addonutils.getSettingAsInt('Quality')
        self.DEVMODE = addonutils.getSettingAsBool('DevMode')
        self.skyit = SkyItalia(self.DEVMODE)

    def addItems(self, items):
        video = False
        for item in items:
            if item.get('videoInfo'):
                video = any([item['videoInfo'].get(
                    'mediatype') == 'video', video])
            addonutils.addListItem(
                label=item.get('label'),
                label2=item.get('label2'),
                params=item.get('params'),
                videoInfo=item.get('videoInfo'),
                arts=item.get('arts'),
                isFolder=False if item.get('isPlayable') else True,
            )
        if video:
            addonutils.setContent('videos')

    def main(self):
        params = addonutils.getParams()
        self.skyit._log(f"main, Params = {params}")
        if 'asset_id' in params:
            # PLAY VIDEO
            video = self.skyit.getVideo(
                params['asset_id'], self.ISA, self.QUALITY)
            if video:
                vid_path = video.get('path')
                self.skyit._log(f"main, Media URL = {vid_path}", 1)
                item = addonutils.createListItem(
                    path=vid_path,
                    videoInfo=video.get('videoInfo'),
                    arts=video.get('arts'),
                    isFolder=False)
                if self.ISA:
                    import inputstreamhelper
                    is_helper = inputstreamhelper.Helper('hls')
                    if is_helper.check_inputstream():
                        item.setContentLookup(False)
                        item.setMimeType('application/x-mpegURL')
                        item.setProperty(
                            'inputstream', is_helper.inputstream_addon)
                        item.setProperty(
                            'inputstream.adaptive.manifest_type', 'hls')
                addonutils.setResolvedUrl(item=item, exit=False)
            else:
                self.skyit._log(
                    f"main, Media URL not found, asset_id = {params['asset_id']}", 3)
                addonutils.notify(T('media.not.found'))
                addonutils.setResolvedUrl(solved=False)

        elif 'playlist_id' in params:
            # PLAYLIST CONTENT
            playlist_content = self.skyit.getPlaylistContent(
                params['playlist_id'])
            self.addItems(playlist_content)

        elif all(x in params for x in ['playlist', 'section', 'subsection']):
            # PLAYLIST SECTION
            playlist = self.skyit.getPlaylists(
                params['section'], params['subsection'])
            self.addItems(playlist)

        elif all(x in params for x in ['title', 'section', 'subsection']):
            # SUBSECTION MENU
            subsection_content = self.skyit.getSubSection(
                params['section'], params['subsection'], params['title'])
            self.addItems(subsection_content)

        elif 'section' in params:
            # SECTION MENU
            section_content = self.skyit.getSection(params['section'])
            self.addItems(section_content)

        elif 'livestream_id' in params:
            # LIVESTREAM PLAY SECTION
            live_content = self.skyit.getLiveStream(params['livestream_id'])
            if live_content:
                item = addonutils.createListItem(
                    path=live_content.get('path'),
                    label=live_content.get('label'),
                    videoInfo=live_content.get('videoInfo'),
                    arts=live_content.get('arts'),
                    isFolder=False
                )
                if self.ISA and params.get('no_isa') != 'True':
                    import inputstreamhelper
                    is_helper = inputstreamhelper.Helper('hls')
                    if is_helper.check_inputstream():
                        item.setContentLookup(False)
                        item.setMimeType('application/x-mpegURL')
                        item.setProperty(
                            'inputstream', is_helper.inputstream_addon)
                        item.setProperty(
                            'inputstream.adaptive.manifest_type', 'hls')

                addonutils.setResolvedUrl(item=item, exit=False)
            else:
                self.skyit._log(
                    f"main, Livestream URL not found, id = {params['livestream_id']}", 3)
                addonutils.notify(T('live.not.found'))
                addonutils.setResolvedUrl(solved=False)

        elif 'live' in params:
            # LIVESTREAM SECTION
            live_content = self.skyit.getLiveStreams()
            self.addItems(live_content)

        else:
            # MAIN MENU
            menu = self.skyit.getMainMenu()
            self.addItems(menu)

        self.skyit = None
        addonutils.endScript(exit=False)
