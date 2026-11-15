
from collections import defaultdict

from bs4 import BeautifulSoup


from resources.lib.tv3cat import DirAZemisio
from resources.lib.tv3cat import DirAZtots
from resources.lib.tv3cat import Home
from resources.lib.tv3cat.Images import Images
from resources.lib.tv3cat import Sections
from resources.lib.utils import Urls
from resources.lib.utils.Urls import url_base
from resources.lib.video.FolderVideo import FolderVideo
from resources.lib.video.Video import Video
from resources.lib.tv3cat.TV3Strings import TV3Strings
from resources.lib.utils.Utils import *


class TV3cat:
    ITEMS_PAGINA = 18

    def __init__(self, addon_path, addon):
        xbmc.log("plugin.video.3cat classe TV3cat - init() ")
        self.strs = TV3Strings(addon)
        self.images = Images(addon_path)
        self.addon_path = addon_path

    # mode = None
    def listHome(self):
        xbmc.log("plugin.video.3cat classe Tv3cat - listHome() ")

        return Home.getList(self.strs)

    def getJsonDataNextData(self, url):
        link = getHtml(url)

        if link:
            soup = BeautifulSoup(link, "html.parser")

            script_tag = soup.find('script', id='__NEXT_DATA__')
            if script_tag:
                xbmc.log("plugin.video.3cat - found script")

                # Find all items with 'titol' and 'id'
                # Extract the JSON content from the script tag
                json_content = script_tag.string
                # print(json_content)
                # Extract the data from the JSON content
                data = json.loads(json_content)

                # Extract the required information
                return data

        return []

    def getTotsProgrames(self):
        data = self.getJsonDataNextData(Urls.url_coleccions)
        if not data:
            return []
        # Extract the required information
        return data['props']['pageProps']['layout']['structure'][4]['children'][0]['finalProps']['items']

    # mode = coleccions
    def listProgrames(self, nomCategoria):
        xbmc.log("plugin.video.3cat - programes per categoria " + nomCategoria)
        lFolderVideos = []
        categories = self.getTotsProgrames()
        for categoria in categories:
            if nomCategoria == categoria['valor']:
                xbmc.log("plugin.video.3cat - Found categoria " + nomCategoria)
                items = categoria['item']
                for item in items:
                    if 'titol' in item and 'id' in item:
                        xbmc.log("plugin.video.3cat - element " + str(item))
                        titol = item['titol']
                        nombonic = item['nombonic']
                        img = self.extractImageIfAvailable(item, "IMG_POSTER")
                        foldVideo = FolderVideo(titol, nombonic, 'getTemporades', img, img)
                        lFolderVideos.append(foldVideo)

                return lFolderVideos

        return lFolderVideos


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
                    # Ignore non-video containers; movie records expose image or duration metadata.
                    if any(k in value for k in ('durada', 'entradeta', 'imatges', 'descripcio')):
                        seen.add(str(video_id))
                        image = self.extractImageIfAvailable(value, 'IMG_POSTER')
                        if not image:
                            image = self.extractImageIfAvailable(value, 'KEYVIDEO')
                        description = value.get('entradeta') or value.get('descripcio') or value.get('sinopsi') or ''
                        videos.append(Video(title, image or '', image or '', description, video_id,
                                            value.get('durada') or ''))
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
            print(categoria)
            nom_categoria = categoria['valor']
            xbmc.log("plugin.video.3cat - Found categoria " + nom_categoria)
            foldVideo = FolderVideo(nom_categoria, nom_categoria, 'getProgrames')
            lFolderVideos.append(foldVideo)

        return lFolderVideos


    # mode = programes
    def dirSections(self):
        return Sections.getList(self.strs)

    # mode = directe
    def listDirecte(self):
        xbmc.log("plugin.video.3cat listDirecte")

        tv3Directe = Video(self.strs.get('tv3'), self.images.thumb_tv3, self.images.thumb_tv3, "TV3", Urls.url_directe_tv3, "")
        c324Directe = Video(self.strs.get('canal324'), self.images.thumb_324, self.images.thumb_324, "324", Urls.url_directe_324, "")
        sx3Directe = Video(self.strs.get('sx3'), self.images.thumb_sx3, self.images.thumb_sx3, "SX3", Urls.url_directe_sx3, "")
        sps3Directe = Video(self.strs.get('esport3'), self.images.thumb_esp3, self.images.thumb_esp3, "E3", Urls.url_directe_esport3, "")
        c33Directe = Video("C33", self.images.thumb_c33, self.images.thumb_c33, "E3", Urls.url_directe_c33, "")

        return [tv3Directe, sx3Directe, c324Directe, sps3Directe, c33Directe]

    #mode getTemporades
    def getListTemporades(self, programaTitol):
        xbmc.log("plugin.video.3cat llista temporades " + programaTitol)
        lFolderVideos = []

        data = self.getJsonDataNextData(Urls.url_capitols.format(programaTitol))
        if not data:
            return []

        # Look for the seasons filer
        try:
            temporada_filter = data['props']['pageProps']['layout']['structure'][3]['children'][0]['children'][0]['finalProps']['isTemporades']

            if not temporada_filter:
                return []
        except (KeyError, IndexError):
            return []

        temporada_value = data['props']['pageProps']['layout']['structure'][3]['children'][0]['children'][0]['finalProps']['temporada']
        num_temporades = int(temporada_value.replace('PUTEMP_', ''))

        for i in range(1, num_temporades + 1):
            temporada = f"{self.strs.get('temporada')} {i}"
            foldVideo = FolderVideo(temporada, str(programaTitol) + "_1_" + str(self.ITEMS_PAGINA) + "_" + str(i), 'getlistvideos', '', '')
            lFolderVideos.append(foldVideo)

        return lFolderVideos

    def getProgramaId(self, titolPrograma):
        data = self.getJsonDataNextData(Urls.url_base + titolPrograma)
        if not data:
            return []

        return data['props']['pageProps']['layout']['structure'][3]['children'][0]['finalProps']['programaId']

    def getProgramaData(self, programaId, pagina, itemsPagina, temporada):
        if temporada:
            apiUrl = Urls.url_api_videos_temporada.format( programaId, pagina, itemsPagina, temporada)
        else:
            apiUrl = Urls.url_api_videos.format(programaId, pagina, itemsPagina)

        with urllib.request.urlopen(apiUrl) as response:
            data = response.read()
            json_data = json.loads(data)
            return [json_data['resposta']['items']['item'], json_data['resposta']['paginacio']]

    # mode = getlistvideos
    def getListVideos(self, url):
        xbmc.log("plugin.video.3cat - get list videos " + str(url))
        url_parts = url.split('_')
        programaTitol = url_parts[0]
        pagina = url_parts[1] if len(url_parts) > 1 else 1
        itemsPagina = url_parts[2] if len(url_parts) > 2 else self.ITEMS_PAGINA
        temporada = url_parts[3] if len(url_parts) > 3 else None
        lVideos = []

        programaId = self.getProgramaId(programaTitol)
        (items, paginacio) = self.getProgramaData(programaId, pagina, itemsPagina, temporada)

        for item in items:
            img = self.extractImageIfAvailable(item, "KEYVIDEO")
            video = Video(item['titol'], img, img, item.get('entradeta'), item['id'], item['durada'])
            lVideos.append(video)

        if int(pagina) < int(paginacio['total_pagines']):
            pagSeguent = int(pagina) + 1
            foldVideo = FolderVideo(f"{self.strs.get('seguent')}: {pagSeguent}",
                                    str(programaTitol) + "_" + str(pagSeguent) + "_" + str(itemsPagina)
                                    + ("_" + str(temporada) if temporada else ""), 'getlistvideos','', '')
            lVideos.append(foldVideo)

        return lVideos

    def extractImageIfAvailable(self, item, keyimatge):
        # Extract image links if available
        if 'imatges' in item and isinstance(item['imatges'], list):
            for image in item['imatges']:
                if 'text' in image and image['text'].startswith('http') \
                        and image['rel_name'] == keyimatge:
                    return image['text']

    #mode = cercar
    def search(self):

        keyboard = xbmc.Keyboard('', self.strs.get('cercar'))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            search_string = keyboard.getText().replace(" ", "+")
            url = "http://www.ccma.cat/tv3/alacarta/cercador/?items_pagina=15&profile=videos&text=" + search_string

            lVideos = self.getListVideos(url, True)

        return lVideos

