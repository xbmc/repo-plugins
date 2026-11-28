import json
import urllib.parse

import xbmc
import xbmcvfs
from bs4 import BeautifulSoup

from resources.lib.tv3cat import Home
from resources.lib.tv3cat.Images import Images
from resources.lib.tv3cat.TV3Strings import TV3Strings
from resources.lib.utils import Urls
from resources.lib.utils.Cache import Cache
from resources.lib.utils.Utils import cleanText, getHtml, getJson, parseDate
from resources.lib.video.FolderVideo import FolderVideo
from resources.lib.video.Video import Video

# The A-Z catalogue page is 1.5 MB, so keep it for a few hours instead of downloading
# it on every click. Programme ids never change, so they are kept for good.
CATALOGUE_MAX_AGE = 6 * 3600


class TV3cat:
    ITEMS_PAGINA = 18

    def __init__(self, addon_path, addon):
        xbmc.log("plugin.video.3cat classe TV3cat - init() ")
        self.strs = TV3Strings(addon)
        self.images = Images(addon_path)
        self.addon_path = addon_path
        self.cache = Cache(xbmcvfs.translatePath(addon.getAddonInfo('profile')))

    # mode = None
    def listHome(self):
        xbmc.log("plugin.video.3cat classe Tv3cat - listHome() ")

        return Home.getList(self.strs)

    def getJsonDataNextData(self, url):
        html = getHtml(url)
        if not html:
            return None

        script_tag = BeautifulSoup(html, "html.parser").find('script', id='__NEXT_DATA__')
        if not script_tag or not script_tag.string:
            xbmc.log("plugin.video.3cat - no __NEXT_DATA__ in " + url, xbmc.LOGWARNING)
            return None

        try:
            return json.loads(script_tag.string)
        except ValueError as e:
            xbmc.log("plugin.video.3cat - invalid __NEXT_DATA__ in " + url + ": " + str(e), xbmc.LOGWARNING)
            return None

    def findFinalProps(self, data, key, name=None):
        # 3cat pages describe their layout as a tree of components. Their position in the
        # tree changes when 3cat adds or removes blocks, so look the component up instead
        # of using fixed indexes.
        try:
            nodes = list(data['props']['pageProps']['layout']['structure'])
        except (KeyError, TypeError):
            return None

        while nodes:
            node = nodes.pop(0)
            if not isinstance(node, dict):
                continue
            props = node.get('finalProps')
            if isinstance(props, dict) and key in props and (name is None or node.get('name') == name):
                return props
            nodes[0:0] = node.get('children') or []

        return None

    def getTotsProgrames(self):
        categories = self.cache.get('catalogue', CATALOGUE_MAX_AGE)
        if categories is not None:
            return categories

        data = self.getJsonDataNextData(Urls.url_coleccions)
        props = self.findFinalProps(data, 'items', 'Az') if data else None
        if not props:
            # 3cat is down or changed the page: an old catalogue beats an empty one
            xbmc.log("plugin.video.3cat - catalogue not available, using the cached copy", xbmc.LOGWARNING)
            return self.cache.get('catalogue') or []

        categories = []
        programaIds = {}
        for categoria in props['items']:
            items = []
            for item in categoria.get('item') or []:
                if 'titol' not in item or 'nombonic' not in item:
                    continue
                # Keep only what the listings use, so the cache stays small
                items.append({
                    'titol': item['titol'],
                    'nombonic': item['nombonic'],
                    'id': item.get('id'),
                    'entradeta': item.get('entradeta'),
                    'imatges': [img for img in item.get('imatges') or []
                                if str(img.get('rel_name', '')).upper() in ('IMG_POSTER', 'IMATGE_169')],
                })
                if item.get('id'):
                    programaIds[item['nombonic']] = item['id']
            categories.append({'valor': categoria.get('valor'), 'item': items})

        self.cache.set('catalogue', categories)
        self.rememberProgramaIds(programaIds)
        return categories

    def programaFolder(self, item):
        poster = self.extractImageIfAvailable(item, "IMG_POSTER")
        fanart = self.extractImageIfAvailable(item, "IMATGE_169")
        return FolderVideo(item['titol'], item['nombonic'], 'getTemporades', poster, poster,
                           cleanText(item.get('entradeta')), fanart)

    # mode = getProgrames
    def listProgrames(self, nomCategoria):
        xbmc.log("plugin.video.3cat - programes per categoria " + nomCategoria)
        for categoria in self.getTotsProgrames():
            if nomCategoria == categoria['valor']:
                return [self.programaFolder(item) for item in categoria['item']]

        return []

    def getMovieCategories(self):
        xbmc.log("plugin.video.3cat - get movie categories")
        html = getHtml(Urls.url_pellicules)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        folders = []
        seen = set()
        for anchor in soup.find_all('a', href=True):
            href = anchor.get('href', '')
            label = anchor.get_text(" ", strip=True).lstrip("+").strip()
            if '/3cat/coleccio/' not in href or not label or label.lower() in seen:
                continue
            if href.startswith('/'):
                href = 'https://www.3cat.cat' + href
            folders.append(FolderVideo(label, href, 'pellicules_categoria'))
            seen.add(label.lower())
        return folders

    def getMovies(self, section):
        xbmc.log("plugin.video.3cat - get movies " + str(section))
        if section == 'novetats':
            page_url = Urls.url_pellicules_novetats
        elif section == 'cataleg':
            page_url = Urls.url_pellicules_cataleg
        else:
            page_url = section
        data = self.getJsonDataNextData(page_url)
        if not data:
            return []

        videos = []
        seen = set()
        def walk(value):
            if isinstance(value, dict):
                title = value.get('titol') or value.get('title')
                video_id = value.get('id')
                if title and video_id and str(video_id) not in seen:
                    # Only videos: the page also holds the collection itself and the
                    # programmes (PTVC_PROGRAMA) a film belongs to, which cannot be played.
                    tipologia = value.get('tipologia')
                    if tipologia == 'DTY_VIDEO_MM' or (tipologia is None and 'durada' in value):
                        seen.add(str(video_id))
                        image = self.extractImageIfAvailable(value, 'IMG_POSTER')
                        if not image:
                            image = self.extractImageIfAvailable(value, 'KEYVIDEO')
                        description = value.get('entradeta') or value.get('descripcio') or value.get('sinopsi') or ''
                        videos.append(Video(title, image or '', image or '', cleanText(description), video_id,
                                            value.get('durada') or '',
                                            fanart=self.extractImageIfAvailable(value, 'KEYVIDEO'),
                                            mediatype='movie'))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(data)
        return videos

    # mode = coleccions
    def listColeccions(self):
        xbmc.log("plugin.video.3cat - listColeccions")
        lFolderVideos = []

        for categoria in self.getTotsProgrames():
            nom_categoria = categoria['valor']
            xbmc.log("plugin.video.3cat - Found categoria " + nom_categoria)
            foldVideo = FolderVideo(nom_categoria, nom_categoria, 'getProgrames')
            lFolderVideos.append(foldVideo)

        return lFolderVideos

    # mode = directe
    def listDirecte(self):
        xbmc.log("plugin.video.3cat listDirecte")

        tv3Directe = Video(self.strs.get('tv3'), self.images.thumb_tv3, self.images.thumb_tv3, "TV3", Urls.url_directe_tv3, "")
        c324Directe = Video(self.strs.get('canal324'), self.images.thumb_324, self.images.thumb_324, "324", Urls.url_directe_324, "")
        sx3Directe = Video(self.strs.get('sx3'), self.images.thumb_sx3, self.images.thumb_sx3, "SX3", Urls.url_directe_sx3, "")
        sps3Directe = Video(self.strs.get('esport3'), self.images.thumb_esp3, self.images.thumb_esp3, "E3", Urls.url_directe_esport3, "")
        c33Directe = Video("C33", self.images.thumb_c33, self.images.thumb_c33, "C33", Urls.url_directe_c33, "")

        return [tv3Directe, sx3Directe, c324Directe, sps3Directe, c33Directe]

    #mode getTemporades
    def getListTemporades(self, programaTitol):
        xbmc.log("plugin.video.3cat llista temporades " + programaTitol)
        lFolderVideos = []

        data = self.getJsonDataNextData(Urls.url_capitols.format(programaTitol))
        if not data:
            return []

        # Look for the seasons filter
        props = self.findFinalProps(data, 'isTemporades')
        if not props:
            return []
        if props.get('programaId'):
            self.rememberProgramaIds({programaTitol: props['programaId']})
        if not props['isTemporades']:
            return []

        try:
            num_temporades = int(str(props['temporada']).replace('PUTEMP_', ''))
        except (KeyError, ValueError):
            return []

        # The 3cat website also lists seasons 1..N from the latest one
        for i in range(1, num_temporades + 1):
            temporada = f"{self.strs.get('temporada')} {i}"
            foldVideo = FolderVideo(temporada, str(programaTitol) + "_1_" + str(self.ITEMS_PAGINA) + "_" + str(i), 'getlistvideos', '', '')
            lFolderVideos.append(foldVideo)

        return lFolderVideos

    def rememberProgramaIds(self, programaIds):
        if not programaIds:
            return
        known = self.cache.get('programaIds') or {}
        if all(known.get(k) == v for k, v in programaIds.items()):
            return
        known.update(programaIds)
        self.cache.set('programaIds', known)

    def getProgramaId(self, titolPrograma):
        known = self.cache.get('programaIds') or {}
        if known.get(titolPrograma):
            return known[titolPrograma]

        for url in (Urls.url_base + titolPrograma + '/', Urls.url_capitols.format(titolPrograma)):
            data = self.getJsonDataNextData(url)
            props = self.findFinalProps(data, 'programaId') if data else None
            if props and props['programaId']:
                self.rememberProgramaIds({titolPrograma: props['programaId']})
                return props['programaId']

        xbmc.log("plugin.video.3cat - programaId not found for " + str(titolPrograma), xbmc.LOGWARNING)
        return None

    def parseListVideosUrl(self, url):
        # url is "<nombonic>" or "<nombonic>_<pagina>_<itemsPagina>[_<temporada>]".
        # Some nombonics contain "_" (e.g. "de_professio_api"), so take the numeric
        # parameters from the end instead of splitting from the start.
        parts = str(url).split('_')
        params = []
        while len(parts) > 1 and len(params) < 3 and parts[-1].isdigit():
            params.insert(0, parts.pop())
        if len(params) < 2:
            parts += params
            params = []

        programaTitol = '_'.join(parts)
        pagina = params[0] if len(params) > 0 else 1
        itemsPagina = params[1] if len(params) > 1 else self.ITEMS_PAGINA
        temporada = params[2] if len(params) > 2 else None
        return programaTitol, pagina, itemsPagina, temporada

    def getProgramaData(self, programaId, pagina, itemsPagina, temporada):
        if temporada:
            apiUrl = Urls.url_api_videos_temporada.format( programaId, pagina, itemsPagina, temporada)
        else:
            apiUrl = Urls.url_api_videos.format(programaId, pagina, itemsPagina)

        resposta = getJson(apiUrl)['resposta']
        return [(resposta.get('items') or {}).get('item') or [], resposta.get('paginacio') or {}]

    def videoFromItem(self, item):
        img = self.extractImageIfAvailable(item, "KEYVIDEO")

        season = episode = None
        for temporada in item.get('temporades') or []:
            num = str(temporada.get('id', '')).replace('PUTEMP_', '')
            if num.isdigit() and str(item.get('capitol_temporada', '')).isdigit():
                season, episode = int(num), int(item['capitol_temporada'])
                break

        show = item.get('programa')
        if not show:
            for programa in item.get('programes_tv') or []:
                show = programa.get('titol') or programa.get('desc')
                if show:
                    break

        return Video(item['titol'], img, img, cleanText(item.get('entradeta')), item['id'], item.get('durada'),
                     fanart=img, mediatype='episode' if season else 'video', show=show,
                     season=season, episode=episode,
                     aired=parseDate(item.get('data_emissio') or item.get('data_publicacio')))

    def nextPageFolder(self, pagina, url, mode):
        return FolderVideo(f"{self.strs.get('seguent')}: {pagina}", url, mode, '', '')

    # mode = getlistvideos
    def getListVideos(self, url):
        xbmc.log("plugin.video.3cat - get list videos " + str(url))
        programaTitol, pagina, itemsPagina, temporada = self.parseListVideosUrl(url)
        lVideos = []

        programaId = self.getProgramaId(programaTitol)
        if not programaId:
            return lVideos
        (items, paginacio) = self.getProgramaData(programaId, pagina, itemsPagina, temporada)

        for item in items:
            if 'titol' in item and 'id' in item:
                lVideos.append(self.videoFromItem(item))

        if int(pagina) < int(paginacio.get('total_pagines') or 0):
            pagSeguent = int(pagina) + 1
            lVideos.append(self.nextPageFolder(pagSeguent,
                                               str(programaTitol) + "_" + str(pagSeguent) + "_" + str(itemsPagina)
                                               + ("_" + str(temporada) if temporada else ""), 'getlistvideos'))

        return lVideos

    def extractImageIfAvailable(self, item, keyimatge):
        # 3cat lists the same image in several sizes. Take the largest sized one, and the
        # MASTER original (which can be huge) only when there is nothing else.
        best = None
        best_rank = None
        for image in item.get('imatges') or []:
            if not isinstance(image, dict):
                continue
            url = image.get('text') or ''
            if not url.startswith('http') or str(image.get('rel_name', '')).upper() != keyimatge.upper():
                continue
            width, _, height = str(image.get('mida', '')).partition('x')
            area = int(width) * int(height) if width.isdigit() and height.isdigit() else 0
            rank = (area > 0, area)
            if best_rank is None or rank > best_rank:
                best, best_rank = url, rank
        return best

    # mode = cerca
    def search(self, text, pagina=1):
        xbmc.log("plugin.video.3cat - search " + text + " page " + str(pagina))
        pagina = int(pagina)
        query = urllib.parse.quote(text)
        results = []

        if pagina == 1:
            # Matching programmes first, so the whole series is one click away
            try:
                resposta = getJson(Urls.url_api_cercador.format(query, 'PTVC_PROGRAMA', 1, 50))['resposta']
                programaIds = {}
                for item in (resposta.get('items') or {}).get('item') or []:
                    if item.get('titol') and item.get('nombonic'):
                        results.append(self.programaFolder(item))
                        if item.get('id'):
                            programaIds[item['nombonic']] = item['id']
                self.rememberProgramaIds(programaIds)
            except Exception as e:
                xbmc.log("plugin.video.3cat - programme search failed: " + str(e), xbmc.LOGWARNING)

        resposta = getJson(Urls.url_api_cercador.format(query, 'DTY_VIDEO_MM', pagina, self.ITEMS_PAGINA))['resposta']
        for item in (resposta.get('items') or {}).get('item') or []:
            if 'titol' in item and 'id' in item:
                results.append(self.videoFromItem(item))

        if pagina < int((resposta.get('paginacio') or {}).get('total_pagines') or 0):
            results.append(self.nextPageFolder(pagina + 1, str(pagina + 1) + "|" + text, 'cerca'))

        return results
