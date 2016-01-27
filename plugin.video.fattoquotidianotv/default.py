#!/usr/bin/python
import re, sys, os, xbmcplugin#, datetime
from neverwise import Util


class FattoQTV(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    if len(self._params) == 0: # Scelta tra Audio o Video

      Util.createAudioVideoItems(self._handle)

      # Show items.
      xbmcplugin.endOfDirectory(self._handle)

    elif len(self._params) == 1 and self._params['content_type'] == 'video': # Visualizzazione del menu video.

      # Menu.
      response = Util.getResponseBS('http://tv.ilfattoquotidiano.it')

      if response.isSucceeded:

        menuItems = []
        for ul in response.body.findAll('ul', 'nav-list'):
          for li in ul.findAll('li'):
            title = li.a.text
            link = li.a['href']
            li = Util.createListItem(title)
            menuItems.append(( li, link, title ))

        div = response.body.find('div', 'submenu-categories')
        for li in div.findAll('li'):
          link = li.a['href']
          found = False
          for item in menuItems:
            if item[1] == link:
              found = True
              break
          if not found:
            title = li.a.text
            li = Util.createListItem(title)
            menuItems.append(( li, link, title ))

        for item in sorted(menuItems, key = lambda item: item[2]):
          xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'c', 'page' : item[1] }), item[0], True)

        # Show items.
        xbmcplugin.endOfDirectory(self._handle)

    elif len(self._params) == 1 and self._params['content_type'] == 'audio': # Visualizzazione del menu audio.

      img = '{0}/resources/images/fqRadio.png'.format(os.path.dirname(os.path.abspath(__file__)))
      li = Util.createListItem(Util.getTranslation(30000), thumbnailImage = img) # Radio.
      xbmcplugin.addDirectoryItem(self._handle, 'http://fqradio.ns0.it:8000/;audio.mp3', li, False)
      xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'p', 'page' : self._getUrlPodcast() }), Util.createListItem(Util.getTranslation(30001), thumbnailImage = 'DefaultAddonLyrics.png'), True)

      # Show items.
      xbmcplugin.endOfDirectory(self._handle)

    else:

      response = Util.getResponseBS(self._params['page'])
      if response.isSucceeded:

        # Videos.
        if self._params['id'] == 'c': # Visualizzazione video di una categoria.
          videos = response.body.findAll('section', 'article-preview')
          for video in videos:
            divTitle = video.find('div', 'article-wrapper')
            title = divTitle.h3.a.text
            img = None
            if video.picture.img != None:
              img = video.picture.img['src']
            li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title }, isPlayable = True)
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'v', 'page' : divTitle.h3.a['href'] }), li, False)

          # Next page.
          self._nextPage(response.body, 'c', '{0}')

          # Show items.
          xbmcplugin.endOfDirectory(self._handle)

        # Podcast.
        if self._params['id'] == 'p': # Visualizzazione podcast.
          podcasts = response.body.find('section', 'fqRadio fqRadio-palinsesto')
          podcasts = podcasts.findAll('div', 'ungrid-row')
          for podcast in podcasts:
            title = u'{0} ({1})'.format(podcast.find('div', 'ungrid-col program').a.text, podcast.find('div', 'ungrid-col program-date').text)
            url = podcast.find('div', 'ungrid-col dwl-podcast').a['href']
            li = Util.createListItem(title, thumbnailImage = 'DefaultAudio.png', streamtype = 'audio', infolabels = { 'title' : title })
            xbmcplugin.addDirectoryItem(self._handle, url, li, False)

          # Next page.
          self._nextPage(response.body, 'p', '{0}/{1}'.format(self._getUrlPodcast(), '{0}'))

          # Show items.
          xbmcplugin.endOfDirectory(self._handle)

        # Play video.
        elif self._params['id'] == 'v':
          title = response.body.find('meta', { 'property' : 'og:title' })['content']
          img = response.body.find('meta', { 'property' : 'og:image' })['content']
          descr = response.body.find('div', 'tv-desc-body').text

          # Video del fatto.
          video = response.body.find('video', { 'id' : 'bcPlayer' })
          if video != None:
            #playerID = 2274739660001
            #publisherID = 1328010481001
            url = 'https://edge.api.brightcove.com/playback/v1/accounts/{0}/videos/{1}'.format(video['data-account'], video['data-video-id'])
            headers = { 'Accept' : 'application/json;pk=BCpkADawqM0xNxj2Rs11iwmFoNJoG2nXUQs67brI7oR2qm0Dwn__kPcbvLJb7M34IY2ar-WxWvi8wHr6cRbP7nmgilWaDrqZEeQm4O5K6z6B2A3afiPFbv7T4LcsQKN2PqIIgIIr3AXq43vL' }
            response = Util.getResponseJson(url, headers)
            if response.isSucceeded:

              sources = sorted(response.body['sources'], key = lambda item: item['avg_bitrate'] if 'avg_bitrate' in item else 0, reverse = True)
              if 'src' in sources[0]:
                source = sources[0]['src']
              else:
                source = sources[1]['src']

              Util.playStream(self._handle, title, img, source, 'video', { 'title' : title, 'plot' : descr })

          # Altri video.
          else:
            responseString = response.body.renderContents()

            # Video di youtube.
            if responseString.find('www.youtube.com/embed') > -1:
              video = re.search('http://www.youtube.com/embed/(.+?)\?', response.body.find('iframe')['src'])
              if video != None:
                Util.playStream(self._handle, title, img, 'plugin://plugin.video.youtube/play/?video_id={0}'.format(video.group(1)), 'video', { 'title' : title, 'plot' : descr })

            # Video servizio pubblico.
            elif responseString.find('meride-video-container') > -1:
              params = { 'id' : 'e', 'page' : self._params['page'], 'title' : title, 'img' : img, 'descr' : descr }
              url = Util.formatUrl(params, 'plugin://plugin.video.serviziopubblico/')
              Util.playStream(self._handle, title, img, url, 'video', { 'title' : title, 'plot' : descr })

            # Video non gestito.
            else:
              Util.showVideoNotAvailableDialog()


  def _getUrlPodcast(self):
    return 'http://www.ilfattoquotidiano.it/fq-radio/podcast'


  def _nextPage(self, bsSource, paramId, urlStringFormat):
    nextPage = bsSource.find('ul', 'swiper-wrapper jgrid')
    if nextPage != None:
      pages = nextPage.findAll('li')
      index = -1
      for page in pages:
        if page.a['class'] == 'active cc':
          index = pages.index(page) + 1
          break # Stops "for page in pages:".
      if index < len(pages):
        Util.createNextPageItem(self._handle, pages[index].a.text, { 'id' : paramId, 'page' : urlStringFormat.format(pages[index].a['href']) })


# Entry point.
#startTime = datetime.datetime.now()
fq = FattoQTV()
del fq
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
