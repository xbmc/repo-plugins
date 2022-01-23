from resources.lib import addonutils
from resources.lib.comedycentral import CC


class ComedyCentral(object):

    def __init__(self):
        self.cc = CC()
        self._ISA = addonutils.getSettingAsBool('UseInputStream')
        self._FISA = addonutils.getSettingAsBool('ForceInputstream')

    def addItems(self, items):
        media_type = []
        for item in items or []:
            if item.get('videoInfo'):
                media_type.append(item['videoInfo'].get('mediatype'))
            addonutils.addListItem(
                label=item.get('label'),
                label2=item.get('label2'),
                params=item.get('params'),
                arts=item.get('arts'),
                videoInfo=item.get('videoInfo'),
                isFolder=False if item.get('playable') else True,
            )

        media_type = list(set(media_type))
        if len(media_type) == 1:
            addonutils.setContent(f"{media_type[0]}s")


    def main(self):
        params = addonutils.getParams()
        if 'mode' in params:
            if params['mode'] == 'SHOWS':
                shows = self.cc.showsList(params['url'])
                self.addItems(shows)
                addonutils.setContent('tvshows')

            elif params['mode'] == 'GENERIC':
                generic = self.cc.genericList(params.get('name'), params['url'])
                self.addItems(generic)

            elif params['mode'] == 'SEASON':
                show = self.cc.loadShows(params.get('name'), params['url'], True)
                self.addItems(show)

            elif params['mode'] == 'EPISODES':
                episodes = self.cc.loadItems(params.get('name'), params['url'])
                self.addItems(episodes)
                addonutils.setContent('episodes')

            elif params['mode'] == 'PLAY':
                select_quality = not self._ISA or (self._ISA and self._FISA)
                playItems = self.cc.getMediaUrl(
                    params['name'], params['url'],
                    params.get('mgid'), select_quality)
                plst = addonutils.getPlaylist()

                for item in playItems:
                    vidIDX = item['idx']
                    liz = addonutils.createListItem(
                        label=item['label'], path=item['url'],
                        videoInfo=item['videoInfo'], subs=item.get('subs'),
                        arts=item.get('arts'), isFolder=False)
                    if self._ISA:
                        import inputstreamhelper
                        is_helper = inputstreamhelper.Helper('hls')
                        if is_helper.check_inputstream():
                            liz.setContentLookup(False)
                            liz.setMimeType('application/vnd.apple.mpegurl')
                            liz.setProperty('inputstream', is_helper.inputstream_addon)
                            liz.setProperty('inputstream.adaptive.manifest_type', 'hls')
                    if vidIDX == 0:
                        addonutils.setResolvedUrl(item=liz, exit=False)
                    plst.add(item['url'], liz, vidIDX)
                plst.unshuffle()

        else:
            menu = self.cc.getMainMenu()
            self.addItems(menu)

        self.cc = None
        addonutils.endScript(exit=False)
