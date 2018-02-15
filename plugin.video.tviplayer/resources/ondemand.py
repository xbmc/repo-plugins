#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: darksky83

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
 
"""
import xbmc
import xbmcgui
import xbmcplugin
import urllib2

from resources.directory import *
from resources.utilities import *
from resources.webutils import *


def list_tv_shows(name, url):
    try:
        page_source = abrir_url(url)
    except:
        xbmc.log('Unexpected error: {0:s} :{1:s}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        page_source = ''
        msgok(translate(30001), translate(30018))
    if page_source:
        match = re.compile(
            '<div class="item-contents">\s*<a href="(/programa/.+?)" class="item-program-img" style="background-image: url\((http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/[\d\w]+?)\);"></a>\s*<a href="[^"]*" class="item-program-title">([^<]*?)</a>\s*<div class="item-program-description">([^<]*?)</div>').findall(
            page_source)
        totalit = len(match)
        i = 0
        for urlsbase, thumbnail, titulo, sinopse in match:
            i += 1
            titulo = title_clean_up(titulo)
            information = {"Title": name, "plot": title_clean_up(sinopse)}
            addprograma(titulo, base_url + urlsbase, 13, thumbnail, totalit, information)

        if (i == 12):
            addDir(translate(30028), getProximaPagina(url), 15, os.path.join(artfolder, "next.png"), 1)
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
        setview('show-view')
    else:
        sys.exit(0)


def list_tv_shows_info(name, url, thumbnail, plot):
    try:
        page_source = abrir_url(url)
        programaId = getProgramaId(url)
    except:
        xbmc.log('Unexpected error: {0:s} :{1:s}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        page_source = ''
        msgok(translate(30001), translate(30018))
    if page_source:
        temporada_actual = '1'
        outras_temporadas = []
        temporadas = re.search(
            '<ul class="temporadas">(?:\s*<li>\s*</li>\s*)?((?:\s*<li><a href="/programa/[^"]+?/t\d+"\s* class="\w*">[^<]*</a></li>\s*)+)</ul>',
            page_source)
        if temporadas:
            matchTemporada = re.compile(
                '<li><a href="(/programa/[^"]+?/t(\d+))"\s* class="(\w*)">([^<]*)</a></li>').findall(
                temporadas.group(1))
            if matchTemporada:
                for url, temporada, atual, descricao in matchTemporada:
                    xbmc.log(
                        "TVI-KODI-PLAYER Encontrada temporada=" + temporada + ", url=" + url + ", atual=" + atual + ", descricao=" + descricao)
                    if atual == "selected":
                        temporada_actual = temporada
                    else:
                        outras_temporadas.append([url, descricao])

        episodiosMatch = re.search('href="#lista-episodios"><strong>([^<]*)</strong>([^<]*)</a>', page_source)
        if episodiosMatch:
            titulo = title_clean_up(episodiosMatch.group(1) + episodiosMatch.group(2))
            information = {"Title": titulo, "plot": plot}
            addprograma(titulo, getAjaxUrl(programaId, temporada_actual, 'episodios', '1'), 16, thumbnail, 1,
                        information, thumbnail)

        clipsMatch = re.search('href="#lista-clips"><strong>\s*(Clipes)\s*</strong>([^<]*)</a>', page_source)
        if clipsMatch:
            titulo = title_clean_up(clipsMatch.group(1) + clipsMatch.group(2))
            information = {"Title": titulo, "plot": plot}
            addprograma(titulo, getAjaxUrl(programaId, temporada_actual, 'clips', '1'), 16, thumbnail, 1, information,
                        thumbnail)

        popularesMatch = re.search('href="#lista-populares"><strong>([^<]*)</strong>([^<]*)</a>', page_source)
        if popularesMatch:
            titulo = title_clean_up(popularesMatch.group(1) + popularesMatch.group(2))
            information = {"Title": titulo, "plot": plot}
            addprograma(titulo, getAjaxUrl(programaId, temporada_actual, 'populares', '1'), 16, thumbnail, 1,
                        information, thumbnail)
        videosMatch = re.search('href="#lista-clips"><strong>V.deos</strong>([^<]*)</a>', page_source)
        if videosMatch:
            xbmc.log("TVI-KODI-PLAYER encontrado marcador videos")
            parse_episodes(name, page_source, plot, thumbnail, url)

        if len(outras_temporadas) > 0:
            for url, descricao in outras_temporadas:
                information = {"Title": translate(30027) + " " + descricao, "plot": plot}
                addprograma(translate(30027) + " " + descricao, base_url + url, 13, thumbnail, 1, information, thumbnail)
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
        setview('episodes-view')
    else:
        sys.exit(0)


def list_episodes(name, url, thumbnail, plot):
    try:
        page_source = abrir_url(url)
    except:
        xbmc.log('Unexpected error: {0:s} :{1:s}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        page_source = ''
        msgok(translate(30001), translate(30018))
    if page_source:
        parse_episodes(name, page_source, plot, thumbnail, url)
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        setview('episodes-view')
    else:
        sys.exit(0)


def parse_episodes(name, page_source, plot, thumbnail, url):
    match = re.compile(
        '<a href="(/programa/.+?)" class="item " style="background-image: url\((http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/[\d\w]+?)/\d+\);;" target="_top">\s*<div[^>]*>\s*<div class="item-details">.*\s*<br /><span class="item-date">([^<]*?)</span><span class="item-duration">([\d:]*)</span><span class="item-program-title">([^<]*?)</span><span class="item-title">([^<]*?)</span>\s*</div>').findall(
        page_source)
    matched = len(match)
    for urlsbase, icon, data, duration, titulo, sinopse in match:
        xbmc.log("Encontrado urlsbase=" + urlsbase + ", thumbnail=" + thumbnail + ", data=" + format_data(
            data) + ", duration=" + duration + ", titulo=" + titulo + ", sinopse=" + sinopse)
        titulo = title_clean_up(titulo)
        sinopse = title_clean_up(sinopse)
        information = {"Title": titulo, "tvshowtitle": name, "plot": sinopse, "aired": format_data(data),
                       "duration": convert_to_minutes(duration)}
        addepisode(sinopse, base_url + urlsbase, 17, icon, matched, information, thumbnail)
    if (matched >= 18):
        addprograma(translate(30028), getProximaPagina(url), 16, os.path.join(artfolder, "next.png"), 1, plot,
                    thumbnail)



def list_emissoes(urltmp):
    try:
        page_source = abrir_url(urltmp)
    except:
        page_source = ''
        msgok(translate(30001), translate(30018))
    if page_source:
        program_list = re.findall('<section>(.+?)</section>', page_source, re.DOTALL)
        if program_list:
            match = re.findall('href="(.+?)".*?itemprop="name">(.+?)</b', program_list[1], re.DOTALL)
            if match:
                totalit = len(match)
                for urlsbase, titulo in match:
                    if selfAddon.getSetting('icon_plot') == 'true':
                        try:
                            source = abrir_url(base_url + urlsbase)
                            sinopse = re.findall('id="promo">.+?\n.+?<p>(.*?)</p>', source, re.DOTALL)
                            if sinopse: plot = clean_html(title_clean_up(sinopse[0])) # FIXME: clean?
                            information = {"Title": title_clean_up(titulo), "plot": plot}
                            try:
                                thumbnail = img_base_url + re.compile('src=(.+?)&amp').findall(source)[0]
                            except:
                                thumbnail = ''
                        except:
                            information = {"Title": title_clean_up(titulo), "plot": translate(30026)};
                            thumbnail = ''
                    else:
                        information = {"Title": title_clean_up(titulo), "plot": translate(30026)};
                        thumbnail = ''
                    addepisode(title_clean_up(titulo), base_url + urlsbase, 17, thumbnail, totalit, information)
                xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
                setview('episodes-view')
        else:
            msgok(translate(30001), translate(30032));
            sys.exit(0)


def pesquisar():
    keyb = xbmc.Keyboard('', translate(30031))
    keyb.doModal()
    if (keyb.isConfirmed()):
        search = keyb.getText()
        encodeSearch = urllib.quote(search);
        resultadosPesquisa(pesquisa_url + encodeSearch + '/1')


def resultadosPesquisa(url):
    try:
        page_source = abrir_url(url)
    except:
        xbmc.log('Unexpected error: {0:s} :{1:s}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        page_source = ''
        msgok(translate(30001), translate(30018))
    if page_source:
        matchPrograma = re.compile(
            '<li class="resultado-programa">\s*<a href="(/programa/.+?)">\s*<div class="thumb logo" style="background-image: url\((http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/[\d\w]+?)\)"></div>\s*<div class="details">([\d:]*)\s*\|\s*<span>([^<]*?)</span></div>\s*<h3>([^<]*?)</h3>\s*<p>([^<]*?)</p>\s*</a>\s*</li>').findall(
            page_source)

        matchEpisodio = re.compile(
            '<li class="resultado-episodio">\s*<a href="(/programa/.+?)">\s*<div class="thumb" style="background-image: url\((http://www.iol.pt/multimedia/oratvi/multimedia/imagem/id/[\d\w]+?)\)"><span class="duration">([\d:]*)</span>\s*</div>\s*<div class="details">([^<]*?)</div>\s*<h3>([^<]*?)</h3>\s*<p>([^<]*?)</p>\s*</a>\s*</li>').findall(
            page_source)
        totalit = len(matchPrograma) + len(matchEpisodio)
        i = 0
        for urlsbase, thumbnail, ano, tipo, titulo, sinopse in matchPrograma:
            i += 1
            information = {"Title": titulo, "plot": title_clean_up(ano + " " + tipo + " " + sinopse)}
            addprograma(titulo, base_url + urlsbase, 13, thumbnail, totalit, information)

        for urlsbase, thumbnail, duracao, nomeSerie, titulo, sinopse in matchEpisodio:
            i += 1
            titulo = title_clean_up(titulo)
            sinopse = title_clean_up(sinopse)
            information = {"Title": titulo, "tvshowtitle": nomeSerie, "plot": sinopse,
                           "duration": convert_to_minutes(duracao)}

            addepisode(titulo, base_url + urlsbase, 17, thumbnail, totalit, information, thumbnail)
        if (len(matchEpisodio) >= 10):
            addDir(translate(30028), getProximaPagina(url), 19, os.path.join(artfolder, "next.png"), 1)


def get_show_episode_parts(name, url, iconimage):
    try:
        source = abrir_url(url)
    except:
        xbmc.log('Unexpected error: {0:s} :{1:s}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        source = ''

    if source:
        match = re.compile("[:=] '(.*)playlist\.m3u8\?([^']*)'\s*[,;]").findall(source)

        if match and match[0]:
            link = match[0][0] + tvi_resolver(match[0][0] + 'playlist.m3u8?' + match[0][1]).replace("%3D", "=")
            abrir_url(link)

            playlist = xbmc.PlayList(1)
            playlist.clear()
            liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
            liz.setInfo('Video', {})
            liz.setProperty('mimetype', 'video')
            playlist.add(link, liz)
            player = xbmc.Player()
            player.play(playlist)

    else:
        msgok(translate(30001), translate(30018));
        sys.exit(0)


def get_show_direto(name, url, iconimage):
    # Get source html
    try:
        source = abrir_url(url)
    except:
        xbmc.log("Can't parse url: " + url)
        msgok(translate(30001), translate(30018))
        sys.exit(0)

    # Processing - get session/wms/host
    try:
        session_string = re.search('nimblesessionid=(\w+)', source).group(0)
        xbmc.log("Session: " + session_string)
    except:
        session_string = ""
        xbmc.log("Session: None ")

    try:
        wms_string = re.search('wmsAuthSign=(\w+)', source).group(0)
        xbmc.log("WMS ID: " + wms_string)
    except:
        wms_string = ""
        xbmc.log("WMS ID: None ")

    try:
        host_string = re.search('https://[a-zA-Z0-9.\-/_]*playlist.m3u8', source).group(0)
        xbmc.log("Balancer host: " + host_string)
    except:
        host_string = "localhost"
        xbmc.log("Balancer host: None")

    tipostr = selfAddon.getSetting('tipostr')

    if tipostr == '0':
        quality = 3
    elif tipostr == '1':
        quality = 5
    else: quality = 7

    # Chunks construction
    url_playlist = host_string + "?" + wms_string
    xbmc.log("Playlist URL:" + url_playlist)
    chunks = abrir_url(url_playlist)
    chunks_array = chunks.split("\n")
    url_short = url_playlist.split("playlist")[0]
    url = url_short + chunks_array[quality]

    # URL Processing
    xbmc.log("Get Show Url: " + url)

    try:
        playlist = xbmc.PlayList(1)
        playlist.clear()
        liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo('Video', {})
        liz.setProperty('mimetype', 'video')
        playlist.add(url, liz)
        player = xbmc.Player()
        player.play(playlist)
        xbmc.log("DVD closed")

    except:
        msgok(translate(30001), translate(30018))
        sys.exit(0)


def tvi_resolver(url):
    try:
        source = abrir_url(url)
    except:
        xbmc.log('Unexpected error: {0:s} :{1:s}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        source = ''
    if source:
        try:
            tipostr = selfAddon.getSetting('tipostr')
            tipostr_b = 'b(15|10)00000'
            if tipostr == '0':
                tipostr_b = 'b(15|10)00000'
            elif tipostr == '1':
                tipostr_b = 'b(75|50)0000'
            elif tipostr == '2':
                tipostr_b = 'b(25|20)0000'
            elif tipostr == '3':
                tipostr_b = 'b(64|48)000_ao'
            xbmc.log("tipostr=" + tipostr + " tipostr_b=" + tipostr_b)
            match = re.compile('(chunklist.*_' + tipostr_b + '\.m3u8\?[^\\n]*)').findall(source)
            if match and match[0]:
                return match[0][0]
            else:
                match = re.compile('(chunklist.*\.m3u8\?[^\\n]*)').findall(source)
                if match and match[0]:
                    return match[0]
        except:
            xbmc.log('Unexpected error: {0:s} :{1:s}'.format(sys.exc_info()[0], sys.exc_info()[1]))
            return ''
    else:
        msgok(translate(30001), translate(30018))
        sys.exit(0)
