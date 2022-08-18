from __future__ import division

from builtins import object
import re
import xbmc
import urllib.parse
from bs4 import BeautifulSoup


from resources.lib.tv3cat import DirAZemisio
from resources.lib.tv3cat import DirAZtots
from resources.lib.tv3cat import Home
from resources.lib.tv3cat.Images import Images
from resources.lib.tv3cat import Sections
from resources.lib.utils import Urls
from resources.lib.video.FolderVideo import FolderVideo
from resources.lib.video.Video import Video
from resources.lib.tv3cat.TV3Strings import TV3Strings
from resources.lib.utils.Utils import *


class TV3cat(object):
    def __init__(self, addon_path, addon):
        self.strs = TV3Strings(addon)
        self.images = Images(addon_path)
        self.addon_path = addon_path

        xbmc.log("plugin.video.tv3.cat classe TV3cat - init() ")

    # mode = None
    def listHome(self):
        xbmc.log("plugin.video.tv3.cat classe Tv3cat - listHome() ")

        return Home.getList(self.strs)

    # mode = destaquem
    def listDestaquem(self):
        xbmc.log("plugin.video.tv3.cat classe Tv3cat - listDestaquem() ")
        html_destacats = getHtml(Urls.url_alacarta)

        lVideos = []

        if html_destacats:

            soup = BeautifulSoup(html_destacats, "html.parser")
            dest = None

            try:

                destacats = soup.findAll("article", {"class": re.compile("M-destacat")})


                destacats2 = soup.findAll("div", {"class": re.compile("swiper-slide")})

                destacats.extend(destacats2)

                for c in destacats:
                    a = c.a["href"]
                    code = a[-8:-1]


                    html_data = getHtml(Urls.url_datavideos + code + '&profile=pc')

                    html_data = html_data.decode("ISO-8859-1")
                    data = json.loads(html_data)

                    if len(data) > 0:
                        video = self.getVideo(data)
                        lVideos.append(video)

            except AttributeError as e:
                xbmc.log("Exception AtributeError Altres items: " + str(e))
            except KeyError as e:
                xbmc.log("Exception KeyError Altres items: " + str(e))
            except Exception as e:
                xbmc.log("Exception Item destacat: " + str(e))

        xbmc.log("listDestaquem len: " + str(len(lVideos)))

        result = [None] * 2
        result[0] = lVideos
        return result


    # mode = noperdis
    def listNoPerdis(self):
        xbmc.log("--------------listNoPerdis----------")

        lVideos = []

        link = getHtml(Urls.url_coleccions)

        if link:

            soup = BeautifulSoup(link, "html.parser")

            try:
                links = soup.findAll("li", {"class": "sensePunt R-elementLlistat  C-llistatVideo"})

                if not links:
                    links = soup.findAll("li", {"class": "sensePunt R-elementLlistat  C-llistatVideo "})

                if not links:
                    links = soup.findAll("li", {"class": "sensePunt R-elementLlistat  C-llistatVideo  "})

                for i in links:
                    a = i.a["href"]
                    code = a[-8:-1]

                    link = getHtml(Urls.url_datavideos + code + '&profile=pc')

                    link = link.decode("ISO-8859-1")
                    data = json.loads(link)

                    if len(data) > 0:
                        video = self.getVideo(data)
                        lVideos.append(video)

            except AttributeError as e:
                xbmc.log("Exception AtributeError NoPerdis: " + str(e))
            except KeyError as e:
                xbmc.log("Exception KeyError NoPerdis: " + str(e))
            except Exception as e:
                xbmc.log("Exception Item destacat: " + str(e))

        result = [None] * 2
        result[0] = lVideos
        return result


    # mode = mesvist
    def listMesVist(self):
        xbmc.log("--------------listMesVist----------")

        lVideos = []

        link = getHtml(Urls.url_mesvist)

        if link:

            soup = BeautifulSoup(link, "html.parser")

            try:
                links = soup.findAll("li", {"class": re.compile("C-llistatVideo")})

                for i in links:
                    a = i.a["href"]
                    code = a[-8:-1]

                    link = getHtml(Urls.url_datavideos + code + '&profile=pc')

                    link = link.decode("ISO-8859-1")
                    data = json.loads(link)



                    if len(data) > 0:
                        video = self.getVideo(data)
                        lVideos.append(video)

            except AttributeError as e:
                xbmc.log("Exception AtributeError listMesVist: " + str(e))
            except KeyError as e:
                xbmc.log("Exception KeyError listMesVist: " + str(e))
            except Exception as e:
                xbmc.log("Exception listMesVist: " + str(e))

        result = [None] * 2
        result[0] = lVideos
        return result



    # mode = coleccions
    def listColeccions(self):
        xbmc.log("--------------listColeccions----------")

        lFolderVideos = []

        link = getHtml(Urls.url_coleccions)

        if link:

            soup = BeautifulSoup(link, "html.parser")

            try:

                colecc = soup.findAll("div", {"class": re.compile("M-destacat")})


                for el in colecc:

                    url = el.a["href"]
                    url = Urls.url_base + url
                    t = el.div.h2.a.string

                    titol = t.encode("utf-8")


                    img = el.figure.img["src"]


                    foldVideo = FolderVideo(titol,url, 'getlistvideos', img, img)
                    lFolderVideos.append(foldVideo)

            except AttributeError as e:
                xbmc.log("Exception AtributeError listColeccions: " + str(e))
            except KeyError as e:
                xbmc.log("Exception KeyError listColeccions: " + str(e))
            except Exception as e:
                xbmc.log("Exception listColeccions: " + str(e))


        return lFolderVideos


    # mode = programes
    def dirSections(self):

        return Sections.getList(self.strs)

    # mode = dirAZemisio
    def dirAZemisio(self):

        return DirAZemisio.getList()

    #mode = dirAZtots
    def dirAZtots(self):

        return DirAZtots.getList()

    # mode = sections
    def programsSections(self, url):
        xbmc.log("-------------------------programsSections----------------------")
        lFolderVideos = []

        link = getHtml(Urls.url_programes_emisio + url)

        if link:
            soup = BeautifulSoup(link)

            try:
                # Grups programes de cada lletra
                links = soup.findAll("ul", {"class": "R-abcProgrames"})

                for i in links:
                    ls = i.findAll("li")

                    for li in ls:
                        url = li.a["href"]
                        t = str(li.a.string)
                        titol = re.sub('^[\n\r\s]+', '', t)

                        # test url
                        urlProg = Urls.url_base + url
                        if urlProg == Urls.urlApm or urlProg == Urls.urlZonaZaping:
                            url_final = urlProg + 'clips/'

                        elif 'super3' in url:
                            if 'https:' not in url:
                                url_final = 'https:' + url
                            else:
                                url_final = url


                        else:
                            match = re.compile('(http://www.ccma.cat/tv3/alacarta/.+?/fitxa-programa/)(\d+/)').findall(
                                urlProg)
                            if len(match) != 0:
                                url1 = match[0][0]
                                urlcode = match[0][1]

                                url_final = url1 + 'capitols/' + urlcode
                            else:
                                url_final = urlProg + 'capitols/'


                        foldVideo = FolderVideo(titol, url_final, 'getlistvideos', "", "")
                        lFolderVideos.append(foldVideo)

            except AttributeError as e:
                xbmc.log("Exception AtributeError listSections: " + str(e))
            except KeyError as e:
                xbmc.log("Exception KeyError listSections: " + str(e))
            except Exception as e:
                xbmc.log("Exception listSections: " + str(e))

        return lFolderVideos


    # mode = directe
    def listDirecte(self):
        xbmc.log("-----------------listDirecte--------------------")
        lVideos = []

        data = getDataVideo(Urls.url_arafem)

        if data:
            c = data.get('canal', None)

            if c:

                arafemtv3 = ''
                arafem33 = ''
                arafemesp3 = ''
                arafem324 = ''
                arafemtv3_sinop = ''
                arafem33_sinop = ''
                arafemesp3_sinop = ''
                arafem324_sinop = ''

                i = 0
                while i < 5:
                    nameChannel = c[i].get('ara_fem', {}).get('codi_canal', None)

                    if nameChannel == 'tv3':
                        arafemtv3 = c[i].get('ara_fem', {}).get('titol_programa', None)
                        arafemtv3_sinop = c[i].get('ara_fem', {}).get('sinopsi', None)
                    if nameChannel == 'cs3' or nameChannel == '33d':
                        arafem33 = c[i].get('ara_fem', {}).get('titol_programa', None)
                        arafem33_sinop = c[i].get('ara_fem', {}).get('sinopsi', None)
                    if nameChannel == 'esport3':
                        arafemesp3 = c[i].get('ara_fem', {}).get('titol_programa', None)
                        arafemesp3_sinop = c[i].get('ara_fem', {}).get('sinopsi', None)
                    if nameChannel == '324':
                        arafem324 = c[i].get('ara_fem', {}).get('titol_programa', None)
                        arafem324_sinop = c[i].get('ara_fem', {}).get('sinopsi', None)

                    i = i + 1

            infolabelstv3 = {}
            infolabels324 = {}
            infolabels33 = {}
            infolabelsesp3 = {}

            if arafemtv3:
                infolabelstv3['title'] = arafemtv3
                infotv3 = '[B]' + arafemtv3 + '[/B]' + '[CR]'
            if arafemtv3_sinop:
                if type(arafemtv3) is int or type(arafemtv3) is float:
                    arafemtv3 = str(arafemtv3)
                infotv3 = infotv3 + arafemtv3_sinop

            infolabelstv3['plot'] = infotv3

            if arafem33:
                infolabels33['title'] = arafem33
                info33 = '[B]' + arafem33 + '[/B]' + '[CR]'
            if arafem33_sinop:
                if type(arafem33) is int or type(arafem33) is float:
                    arafem33 = str(arafem33)
                info33 = info33 + arafem33_sinop

            infolabels33['plot'] = info33

            if arafemesp3:
                infolabelsesp3['title'] = arafemesp3
                infoesp3 = '[B]' + arafemesp3 + '[/B]' + '[CR]'
            if arafemesp3_sinop:
                if type(arafemesp3) is int or type(arafemesp3) is float:
                    arafemesp3 = str(arafemesp3)
                infoesp3 = infoesp3 + arafemesp3_sinop

            infolabelsesp3['plot'] = infoesp3

            if arafem324:
                infolabels324['title'] = arafem324
                info324 = '[B]' + arafem324 + '[/B]' + '[CR]'
            if arafem324_sinop:
                if type(arafem324) is int or type(arafem324) is float:
                    arafem324 = str(arafem324)
                info324 = info324 + arafem324_sinop

            infolabels324['plot'] = info324

        tv3Directe = Video(self.strs.get('tv3'), self.images.thumb_tv3, self.images.thumb_tv3, infolabelstv3, Urls.url_directe_tv3, "")
        c324Directe = Video(self.strs.get('canal324'), self.images.thumb_tv3, self.images.thumb_tv3, infolabels324, Urls.url_directe_324, "")
        c33s3Directe = Video(self.strs.get('c33super3'), self.images.thumb_tv3, self.images.thumb_tv3, infolabels33, Urls.url_directe_c33s3, "")
        sps3Directe = Video(self.strs.get('esport3'), self.images.thumb_tv3, self.images.thumb_tv3, infolabelsesp3, Urls.url_directe_esport3, "")

        tv3DirecteInt = Video(self.strs.get('tv3_int'), self.images.thumb_tv3, self.images.thumb_tv3, infolabelstv3, Urls.url_directe_tv3_int, "")
        c324DirecteInt = Video(self.strs.get('canal324_int'), self.images.thumb_tv3, self.images.thumb_tv3, infolabels324, Urls.url_directe_324_int, "")
        c33s3DirecteInt = Video(self.strs.get('c33super3_int'), self.images.thumb_tv3, self.images.thumb_tv3, infolabels33, Urls.url_directe_c33s3_int, "")
        sps3DirecteInt = Video(self.strs.get('esport3_int'), self.images.thumb_tv3, self.images.thumb_tv3, infolabelsesp3, Urls.url_directe_esport3_int, "")

        lVideos = [tv3Directe, c33s3Directe, c324Directe, sps3Directe, tv3DirecteInt, c33s3DirecteInt, c324DirecteInt, sps3DirecteInt]

        result = [None] * 2
        result[0] = lVideos
        return result


    # mode = progAZ
    def programesAZ(self, paramUrl, letters):
        xbmc.log("--------------------programesAZ------------------")
        letters = urllib.parse.unquote(letters)
        lFolderVideos = []
        url = ""

        if paramUrl == "emisio":
            url = Urls.url_programes_emisio
        else:
            url = Urls.url_programes_tots

        html = getHtml(url)


        if html:

            soup = BeautifulSoup(html.decode('utf-8', 'ignore'), "html.parser")

            elements = soup.findAll("ul", {"class": "R-abcProgrames"})

            li = None


            if len(elements) > 0:

                if letters == "#A-C":

                    li = elements[0:4]

                elif letters == "D-E":

                    li = elements[4:6]

                elif letters == "F-I":

                    li = elements[6:10]

                elif letters == "J-L":

                    li = elements[10:13]

                elif letters == "M-P":

                    li = elements[13:17]

                elif letters == "Q-S":

                    li = elements[17:20]

                elif letters == "T-V":

                    li = elements[20:23]

                elif letters == "X-Z":

                    li = elements[23:]

                if li != None and len(li) > 0:

                    for l in li:

                        links = l.findAll("li")

                        if len(links) > 0:

                            for i in links:
                                #xbmc.log("progsAZ - li: " + str(i).encode('utf-8'))

                                url = i.a["href"]
                                titol = i.a.string.strip().encode("utf-8")

                                # test url
                                urlProg = Urls.url_base + url
                                if urlProg == Urls.urlApm or urlProg == Urls.urlZonaZaping:
                                    url_final = urlProg + 'clips/'

                                elif 'super3' in url:
                                    if 'https:' not in url:
                                        url_final = 'https:' + url
                                    else:
                                        url_final = url

                                else:
                                    match = re.compile(
                                        '(http://www.ccma.cat/tv3/alacarta/.+?/fitxa-programa/)(\d+/)').findall(urlProg)
                                    if len(match) != 0:
                                        url1 = match[0][0]
                                        urlcode = match[0][1]
                                        
                                        url_final = url1 + 'capitols/' + urlcode
                                    else:
                                        url_final = urlProg + 'capitols/'


                                folderVideo = FolderVideo(titol, url_final, 'getlistvideos', "", "")
                                lFolderVideos.append(folderVideo)
                                #xbmc.log("progsAZ - Titol: " + titol)
                                #xbmc.log("progsAZ - url: " + url_final)


        return  lFolderVideos

    # mode = getlistvideos
    def getListVideos(self, url, cercar):
        xbmc.log("---------------getListVideos------------------------------")
        result = [None] * 2
        lVideos = []

        xbmc.log('getListVideos--Url listvideos: ' + url)

        link = getHtml(url)

        if link:

            soup = BeautifulSoup(link.decode('utf-8', 'ignore'), "html.parser")

            links = None
            try:
                links = soup.findAll("div", {"class": "F-itemContenidorIntern C-destacatVideo"})

                if not links:
                    links = soup.findAll("li", {"class": "F-llistat-item"})

                # Coleccions
                if not links:
                    links = soup.findAll("div", {"class": re.compile("M-destacat")})

                # Zona Zapping
                if not links:
                    links = soup.findAll("article", {"class": "M-destacat  C-destacatVideo T-alacartaTema C-3linies "})

                # Super 3
                if not links:
                  
                    links = soup.findAll("div",
                                         {"class": "M-destacat super3 T-video  ombres-laterals"})
                    links2 = soup.findAll("div",
                                         {"class": "M-destacat super3 noGapAfter T-video  ombres-laterals"})
                    links = links + links2

                # Super 3
                if not links:
                    links = soup.findAll("article",
                                         {"class": "M-destacat super3 noGapAfter T-video  ombres-laterals"})


            except AttributeError as e:
                xbmc.log("getListVideos--getLinks--Exception AtributeError listVideos: " + str(e))
            except KeyError as e:
                xbmc.log("getListVideos--getLinks--Exception KeyError  listVideos: " + str(e))
            except Exception as e:
                xbmc.log("getListVideos--getLinks--Exception listVideos: " + str(e))

            if links:

                for l in links:

                    try:

                        urlvideo = l.a["href"]

                        code = urlvideo.split('/')[-1]

                        if len(code) == 0:
                            code = urlvideo.split('/')[-2]


                        html_data = getHtml(Urls.url_datavideos + code + '&profile=pc')

                        html_data = html_data.decode("ISO-8859-1")
                        data = json.loads(html_data)

                        if len(data) > 0:
                            video = self.getVideo(data)
                            lVideos.append(video)




                    except AttributeError as e:
                        xbmc.log("getListVideos--bucle addVideo--Exception AtributeError: " + str(e))

                    except KeyError as e:
                        xbmc.log("getListVideos--bucle addVideo--Exception KeyError: " + str(e))

                    except Exception as e:
                        xbmc.log("getListVideos--bucle addVideo--Exception: " + str(e))

                result[0] = lVideos

                ###############################################################################

                # Pagination
                ht = rb'<p class="numeracio">P\xc3\xa0gina (\d+) de (\d+)</p>'

                match = re.compile(ht).findall(link)
                if len(match) != 0:
                    actualPage = int(match[0][0])
                    totalPages = int(match[0][1])

                    if actualPage < totalPages:
                        ntPage = str(actualPage + 1)
                        nextPage = '&pagina=' + ntPage
                        if cercar:
                            if actualPage == 1:
                                url_next = url + nextPage
                            else:
                                url_next = re.sub('&pagina=[\d]+', nextPage, url)
                        else:
                            url_next = url + '?text=&profile=&items_pagina=15' + nextPage
                            foldNext = FolderVideo(self.strs.get('seguent'), url_next, "getlistvideos", "","")
                            foldNext.hasNextPage = True
                            result[1] = foldNext

        return result


    def getVideo(self, data):
        linkvideo = None
        media = data.get('media', {})

        if type(media) is list and len(media) > 0:
            media_dict = media[0]
            linkvideo = media_dict.get('url', None)
        else:
            linkvideo = media.get('url', None)

        if linkvideo != None:
            if type(linkvideo) is list and len(linkvideo) > 0:
                linkvideo_item = linkvideo[0]
                urlVideo = linkvideo_item.get('file', None)

            titol = data.get('informacio', {}).get('titol', None)
            image = data.get('imatges', {}).get('url', None)
            descripcio = data.get('informacio', {}).get('descripcio', None)
            programa = data.get('informacio', {}).get('programa', None)
            capitol = data.get('informacio', {}).get('capitol', None)
            tematica = data.get('informacio', {}).get('tematica', {}).get('text', None)
            data_emisio = data.get('informacio', {}).get('data_emissio', {}).get('text', None)
            milisec = data.get('informacio', {}).get('durada', {}).get('milisegons', None)
            durada = ""

            if milisec != None:
                durada = milisec // 1000


            if descripcio == None:
                descripcio = ''
            else:
                descripcio = descripcio.replace('<br />', '')

            header = ""
            if programa != None:
                if type(programa) is int or type(programa) is float:
                    programa = str(programa)
                header = '[B]' + programa + '[/B]' + '[CR]'

            infolabels = {}
            if data_emisio != None:
                dt = data_emisio[0:10]
                year = data_emisio[6:10]
                infolabels['aired'] = dt
                infolabels['year'] = year
                header = header + dt + '[CR]'

            descripcio = header + descripcio

            if titol != None:
                infolabels['title'] = titol


            if capitol != None:
                infolabels['episode'] = capitol


            if descripcio != None:
                infolabels['plot'] = descripcio

            if tematica != None:
                infolabels['genre'] = tematica

            video = Video(titol, image, image, infolabels, urlVideo, durada )

            return video

        else:
            return None

    #mode = cercar
    def search(self):

        keyboard = xbmc.Keyboard('', self.strs.get('cercar'))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            search_string = keyboard.getText().replace(" ", "+")
            url = "http://www.ccma.cat/tv3/alacarta/cercador/?items_pagina=15&profile=videos&text=" + search_string

            lVideos = self.getListVideos(url, True)

        return lVideos

