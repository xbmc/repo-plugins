#!/usr/bin/python
import re, sys, xbmcplugin, httplib#, datetime
from neverwise import Util
from pyamf import remoting


class FattoQTV(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    if len(self._params) == 0: # Visualizzazione del menu.

      # Menu.
      lis = Util.getHtml('http://tv.ilfattoquotidiano.it', True)
      if lis != None:
        lis = lis.find('ul', id='menu-videogallery')
        lis = lis.findAll('li', id=re.compile('menu-item-[0-9]+'))
        for li in lis:
          ul = li.find('ul')
          link = li.a['href']
          if ul == None and link.find('servizio-pubblico') == -1:
            title = Util.normalizeText(li.a.text)
            li = Util.createListItem(title, streamtype = 'video', infolabels = { 'title' : title })
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'c', 'page' : link }), li, True)

        # Show items.
        xbmcplugin.endOfDirectory(self._handle)

    else:

      response = Util.getHtml(self._params['page'], True)
      if response != None:

        # Check if exist additional archive.
        archive = response.find('div', 'go-to-archive')
        if archive != None:
          response = Util.getHtml(archive.h1.a['href'], True)

        if response != None:

          # Videos.
          if self._params['id'] == 'c': # Visualizzazione video di una categoria.
            videos = response.findAll('div', 'video-excerpt')
            for video in videos:
              title = Util.normalizeText(video.h2.a.text)
              desc = video.p
              li = Util.createListItem(title, thumbnailImage = self._normalizeImageUrl(video.img['src']), streamtype = 'video', infolabels = { 'title' : title, 'plot' : Util.normalizeText(desc.text if desc != None else '') }, isPlayable = True)
              xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'v', 'page' : video.h2.a['href'] }), li, False)

            # Next page.
            nextPage = response.find('span', 'current')
            if nextPage != None:
              url = Util.formatUrl({ 'id' : 'c', 'page' : nextPage.nextSibling['href'] })
              xbmcplugin.addDirectoryItem(self._handle, url, Util.createItemPage(Util.normalizeText(nextPage.nextSibling.text)), True)

            # Show items.
            xbmcplugin.endOfDirectory(self._handle)

          # Play video.
          elif self._params['id'] == 'v':
            title = Util.normalizeText(response.find('h1', 'entry-title full-title').text)
            img = response.find('link', rel='image_src')['href']
            content = response.find('span', 'content')
            descr = None
            if content != None:
              descr = content.renderContents()
              if len(descr) == 0:
                descr = content.nextSibling.renderContents()
              if len(descr) > 0:
                descr = Util.normalizeText(Util.trimTags(descr))

            # Video del fatto.
            videoId = response.find('param', { 'name' : '@videoPlayer' })
            if videoId != None:
              playerID = 2274739660001
              publisherID = 1328010481001
              const = 'ef59d16acbb13614346264dfe58844284718fb7b'
              conn = httplib.HTTPConnection('c.brightcove.com')
              envelope = remoting.Envelope(amfVersion=3)
              envelope.bodies.append(('/1', remoting.Request(target='com.brightcove.player.runtime.PlayerMediaFacade.findMediaById', body=[const, playerID, videoId['value'], publisherID], envelope=envelope)))
              conn.request('POST', '/services/messagebroker/amf?playerId={0}'.format(str(playerID)), str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
              response = conn.getresponse().read()
              response = remoting.decode(response).bodies[0][1].body

              if response != None:
                item = sorted(response['renditions'], key=lambda item: item['encodingRate'], reverse=True)[0]
                streamUrl = item['defaultURL']

                # Divido url da playpath.
                index = streamUrl.find('&')
                url = streamUrl[:index]
                playpath = streamUrl[index + 1:]

                # Divido url da app.
                index = url.find('/', 7)
                app = url[index + 1:]
                if app[-1:] == '/':
                  app = app[:-1]

                Util.playStream(self._handle, title, img, '{0}:1935 app={1} playpath={2}'.format(url[:index], app, playpath), 'video', { 'title' : title, 'plot' : descr })
              else:
                Util.showVideoNotAvailableDialog()

            # Altri video.
            else:
              responseString = response.renderContents()

              # Video di youtube.
              if responseString.find('www.youtube.com/embed') > -1:
                videoId = re.compile('http://www.youtube.com/embed/(.+?)\?').findall(response.find('iframe')['src'])
                if len(videoId) > 0:
                  Util.playStream(self._handle, title, img, 'plugin://plugin.video.youtube/play/?video_id={0}'.format(videoId[0]), 'video', { 'title' : title, 'plot' : descr })

              # Video servizio pubblico.
              elif responseString.find('meride-video-container') > -1:
                Util.playStream(self._handle, title, img, 'plugin://plugin.video.serviziopubblico/?id=e&page={0}&title={1}&img={2}&descr={3}'.format(self._params['page'], self._stripNonAscii(title), img, self._stripNonAscii(descr)), 'video', { 'title' : title, 'plot' : descr })

              # Video non gestito.
              else:
                Util.showVideoNotAvailableDialog()


  def _normalizeImageUrl(self, img):
    index = img.find('?')
    if index > 0:
      img = img[:index]
    return img


  def _stripNonAscii(self, string):
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


# Entry point.
#startTime = datetime.datetime.now()
fc = FattoQTV()
del fc
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
