import re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import urllib.request
import urllib.parse
from urllib.request import Request, urlopen
import time
import requests
import inputstreamhelper
from bs4 import BeautifulSoup

from resources.lib.globals import G


def show_root_menu():
    """ Show the plugin root menu """
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32002) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "diretta_la7"}, li_style, folder=False, is_live=True)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32009) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7d.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "diretta_la7d"}, li_style, folder=False, is_live=True)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32001) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'rivedila7.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "rivedi_la7"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32004) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'rivedila7d.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "rivedi_la7d"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32010) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'la7prime.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "la7_prime"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32006) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'programmila7la7d.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "tutti_programmi"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32007) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'tgmeteo.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "tg_meteo"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32008) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'techela7.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "teche_la7"}, li_style)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def add_directory_item_nodup(parameters, li, title='', folder=True, is_live=False):
    if not title:
        title = G.TITOLO
    if title in G.LIST_PROGRAMMI:
        xbmc.log('PROGRAMMA DUPLICATO', xbmc.LOGINFO)
    else:
        url = sys.argv[0] + '?' + urllib.parse.urlencode(parameters)
        if is_live:
            url += '&_l=.pvr'  # disabilita per le dirette la richiesta di riprendere il video dall'ultima volta
        # xbmc.log('LIST------: '+str(url),xbmc.LOGINFO)
        if not folder:
            li.setInfo('video', {})
            li.setProperty('isPlayable', 'true')
        return xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url, listitem=li, isFolder=folder)


def play_dirette(url, live):
    url_title = ''
    regex5 = ''
    titolo_diretta = ''

    if live:
        if url == G.URL_LIVE_LA7:
            url_title = G.URL_BASE
            regex5 = r'emissioneString\s*=\s*"(.*?)"'
        elif url == G.URL_LIVE_LA7D:
            url_title = G.URL_BASE_LA7D
            regex5 = r'emissioneStringLa7d\s*=\s*"(.*?)"'
        # xbmc.log('URL TITLE-----: '+str(url_title),xbmc.LOGINFO)

        req = Request(url_title, headers={'user-agent': G.HEADERS_SET['user-agent']})
        page = urlopen(req).read()
        html = page.decode()
        # xbmc.log('REGEX5-----: '+str(re.findall(regex5, html)),xbmc.LOGINFO)
        titolo_diretta = re.findall(regex5, html)[0]
        # xbmc.log('TITOLO DIRETTA-----: '+str(titolo_diretta),xbmc.LOGINFO)

    response = requests.get(url, headers={'user-agent': G.HEADERS_SET['user-agent']}, verify=False).content.decode()
    try:
        preurl = re.findall('preTokenUrl = "(.+?)"', response)[0]
    except Exception as e:
        e = sys.exc_info()[0]
        xbmc.log('EXCEP PREURL: ' + str(e), xbmc.LOGINFO)
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
        return
    response = response.replace("\'", '"')
    mpdurl = re.findall('dash.+?"(.+?)"', response, re.DOTALL)[0]
    headers_tok = {
        'host': G.HEADERS_SET['host_token'],
        'user-agent': G.HEADERS_SET['user-agent'],
        'accept': G.HEADERS_SET['accept'],
        'accept-language': G.HEADERS_SET['accept-language'],
        'dnt': G.HEADERS_SET['dnt'],
        'te': G.HEADERS_SET['te'],
        'origin': G.HEADERS_SET['origin'],
        'referer': G.HEADERS_SET['referer'],
    }
    response = requests.get(preurl, headers=headers_tok, verify=False).json()
    pre_auth_token = response['preAuthToken']

    headers_lic = {
        'host': G.HEADERS_SET['host_license'],
        'user-agent': G.HEADERS_SET['user-agent'],
        'accept': G.HEADERS_SET['accept'],
        'accept-language': G.HEADERS_SET['accept-language'],
        'preAuthorization': pre_auth_token,
        'origin': G.HEADERS_SET['origin'],
        'referer': G.HEADERS_SET['referer'],
    }
    pre_lic = '&'.join(['%s=%s' % (name, value) for (name, value) in headers_lic.items()])
    # xbmc.log('LICENSE1------: '+str(pre_lic),xbmc.LOGINFO)

    tsatmp = str(int(time.time()))
    license_url = G.KEY_WIDEVINE + '?d=%s' % tsatmp
    lic_url = '%s|%s|R{SSM}|' % (license_url, pre_lic)
    # xbmc.log('LICENSE2------: '+str(lic_url),xbmc.LOGINFO)
    is_helper = inputstreamhelper.Helper(G.DRM_PROTOCOL, drm=G.DRM)
    if is_helper.check_inputstream():
        listitem = xbmcgui.ListItem(offscreen=True)
        listitem.setPath(mpdurl)
        if live:
            # listitem.setLabel(titolo_diretta)
            listitem.setInfo('video', {'plot': titolo_diretta, 'title': titolo_diretta})
            listitem.setProperty('ResumeTime', '206')   # https://github.com/xbmc/inputstream.adaptive/issues/647#issuecomment-825203536
            listitem.setProperty('TotalTime', '240')
        listitem.setProperty("inputstream", is_helper.inputstream_addon)
        listitem.setProperty("inputstream.adaptive.manifest_type", G.DRM_PROTOCOL)
        listitem.setProperty("inputstream.adaptive.license_type", G.DRM)
        listitem.setProperty("inputstream.adaptive.license_key", lic_url)
        listitem.setMimeType('application/dash+xml')
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, True, listitem)
    else:
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)


def play_video(page_video, live):
    # xbmc.log('PAGE VIDEO-----: '+str(page_video),xbmc.LOGINFO)

    # regex1 = 'vS = "(.*?)"'
    regex2 = '/content/(.*?).mp4'
    regex3 = 'm3u8: "(.*?)"'
    # regex4 = '  <iframe src="(.*?)"'

    req = Request(page_video, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page = urlopen(req).read()
    html = page.decode()
    if live:
        return
        # if re.findall(regex1, html):
        # xbmc.log('REGEX1-----: '+str(re.findall(regex1, html)),xbmc.LOGINFO)
        #     link_video = re.findall(regex1, html)[0]
    else:
        if re.findall(regex2, html):
            # xbmc.log('REGEX2-----: '+str(re.findall(regex2, html)),xbmc.LOGINFO)
            link_video = 'https://awsvodpkg.iltrovatore.it/local/hls/,/content/' + re.findall(regex2, html)[0] + '.mp4.urlset/master.m3u8'
            # xbmc.log('LINK2-----: '+str(link_video),xbmc.LOGINFO)
        elif re.findall(regex3, html):
            # xbmc.log('REGEX3-----: '+str(re.findall(regex3, html)),xbmc.LOGINFO)
            link_video = re.findall(regex3, html)[0]
        else:
            # xbmc.log('DECODIFICA DRM',xbmc.LOGINFO)
            play_dirette(page_video, False)
            return
        # elif re.findall(regex4, html):
        #     #xbmc.log('REGEX4-----: '+str(re.findall(regex4, html)),xbmc.LOGINFO)
        #     iframe = re.findall(regex4, html)[0]
        #     req2 = Request(iframe,headers={'user-agent': G.HEADERS_SET['user-agent']})
        #     page2=urlopen(req2)
        #     html2=page2.read()
        #     if re.findall(regex2, html2):
        #         #xbmc.log('REGEX2-B---: '+str(re.findall(regex2, html)),xbmc.LOGINFO)
        #         link_video = str("https:")+re.findall(regex2, html2)[0]

    listitem = xbmcgui.ListItem(G.TITOLO, offscreen=True)
    listitem.setInfo('video', {'Title': G.TITOLO})
    if G.THUMB != "":
        listitem.setArt({'thumb': G.THUMB})
    listitem.setInfo('video', {'plot': G.PLOT})
    if link_video == '':
        xbmc.log('RivediLA7: NO VIDEO LINK', xbmc.LOGINFO)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, False, listitem)
        return
    listitem.setProperty('inputstream', 'inputstream.adaptive')
    listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
    listitem.setPath(link_video)
    xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, True, listitem)


def rivedi(url, thumb):
    req = Request(url, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page = urlopen(req)
    html = BeautifulSoup(page, 'html5lib')
    G.GIORNO = html.find('div', class_='block block-system').find_all('div', class_=['item item--menu-guida-tv', 'item item--menu-guida-tv active'])
    # xbmc.log('GIORNO----------: '+str(G.GIORNO),xbmc.LOGINFO)
    if G.GIORNO:
        for div in reversed(G.GIORNO):
            date_day = div.find('div', class_='giorno-numero').text.strip()
            date_month = div.find('div', class_='giorno-mese').text.strip()
            date_row_week = div.find('div', class_='giorno-text').text.strip()
            a = div.a.get('href').strip()
            liStyle = xbmcgui.ListItem(date_row_week + " " + date_day + " " + date_month, offscreen=True)
            liStyle.setArt({'thumb': os.path.join(G.THUMB_PATH, thumb), 'fanart': G.FANART_PATH})
            add_directory_item_nodup({"mode": G.MODE, "giorno": a}, liStyle)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def rivedi_giorno():
    req = Request(G.URL_BASE + G.GIORNO, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page = urlopen(req)
    html = BeautifulSoup(page, 'html5lib')
    guida_tv = html.find(id="content_guida_tv_rivedi").find_all('div', class_='item item--guida-tv')
    if guida_tv:
        for div in guida_tv:
            orario = div.find('div', class_='orario').contents[0].strip()
            nome = div.find('div', class_='property').text.strip()
            thumb = 'https:' + div.find('div', class_='bg-img lozad').get('data-background-image')
            plot = div.find('div', class_='occhiello').text.strip()
            if div.a:
                urll = div.a.get('href').strip()
                # xbmc.log('------LINK------: '+str(urll),xbmc.LOGINFO)
                liStyle = xbmcgui.ListItem(orario + " " + nome, offscreen=True)
                liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
                liStyle.setInfo('video', {'plot': plot})
                liStyle.setProperty('isPlayable', 'true')
                url2 = sys.argv[0] + '?' + urllib.parse.urlencode({"mode": G.MODE, "play": urll, "titolo": nome, "thumb": thumb, "plot": plot})
                xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url2, listitem=liStyle, isFolder=False)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_lettera():
    req_p = Request(G.URL_PROGRAMMI, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page_p = urlopen(req_p)
    html_p = BeautifulSoup(page_p, 'html5lib')
    programmi = html_p.find(id='container-programmi-list').find_all('div', class_='list-item')
    # xbmc.log('PROGRAMMI----------: '+str(programmi),xbmc.LOGINFO)
    req_pd = Request(G.URL_PROGRAMMILA7D, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page_pd = urlopen(req_pd)
    html_pd = BeautifulSoup(page_pd, 'html5lib')
    programmila7d = html_pd.find(id='container-programmi-list').find_all('div', class_='list-item')
    req_tp = Request(G.URL_TUTTI_PROGRAMMI, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page_tp = urlopen(req_tp)
    html_tp = BeautifulSoup(page_tp, 'html5lib')
    tutti_programmi = html_tp.find_all('div', class_='list-item')

    if programmi or programmila7d or tutti_programmi:
        for dati in programmi:
            if dati.find('div', class_='titolo'):
                titolo = dati.find('div', class_='titolo').text.strip()
                # xbmc.log('TITLE1-----: '+str(titolo),xbmc.LOGINFO)
                liStyle = xbmcgui.ListItem(titolo, offscreen=True)
                url_trovato = dati.a.get('href').strip()
                # xbmc.log('URL--------: '+str(url_trovato),xbmc.LOGINFO)
                if url_trovato != '/meteola7' and url_trovato != '/meteo-della-sera' and url_trovato != '/tgla7' and url_trovato != '/film' and url_trovato != '/film-e-fiction':
                    if url_trovato == '/facciaafaccia':
                        url_trovato = '/faccia-a-faccia'
                    if url_trovato == '/il-boss-dei-comici':
                        url_trovato = '/boss-dei-comici'
                    if url_trovato == '/lariadestate':
                        url_trovato = '/laria-destate'
                    if url_trovato == '/taga-doc':
                        url_trovato = '/tagada-doc'
                    link = G.URL_BASE + url_trovato
                    # xbmc.log('LINK-----: '+str(link),xbmc.LOGINFO)
                    if len(dati) > 0:
                        try:
                            thumb = dati.find('div', class_='image-bg lozad').get('data-background-image')
                        except Exception as e:
                            e = sys.exc_info()[0]
                            xbmc.log('EXCEP THUMB1: ' + str(e), xbmc.LOGINFO)
                            thumb = ''
                        if thumb:
                            liStyle.setArt({'thumb': thumb})
                        else:
                            xbmc.log('NO THUMB1', xbmc.LOGINFO)
                    liStyle.setArt({'fanart': G.FANART_PATH})
                    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

                    if titolo not in G.LIST_PROGRAMMI:
                        G.LIST_PROGRAMMI.append(titolo)

        for dati in programmila7d:
            if dati.find('div', class_='titolo'):
                titolo = dati.find('div', class_='titolo').text.strip()
                # xbmc.log('TITLE1-----: '+str(titolo),xbmc.LOGINFO)
                liStyle = xbmcgui.ListItem(titolo, offscreen=True)
                url_trovato = dati.a.get('href').strip()
                if url_trovato != '/meteola7' and url_trovato != '/meteo-della-sera' and url_trovato != '/tgla7' and url_trovato != '/film' and url_trovato != '/film-e-fiction':
                    if url_trovato == '/facciaafaccia':
                        url_trovato = '/faccia-a-faccia'
                    if url_trovato == '/il-boss-dei-comici':
                        url_trovato = '/boss-dei-comici'
                    if url_trovato == '/lariadestate':
                        url_trovato = '/laria-destate'
                    if url_trovato == '/taga-doc':
                        url_trovato = '/tagada-doc'
                    link = G.URL_BASE + url_trovato
                    # xbmc.log('LINK-----: '+str(link),xbmc.LOGINFO)
                    if len(dati) > 0:
                        try:
                            thumb = dati.find('div', class_='image-bg lozad').get('data-background-image')
                        except Exception as e:
                            e = sys.exc_info()[0]
                            xbmc.log('EXCEP THUMB2: ' + str(e), xbmc.LOGINFO)
                            thumb = ''
                        if thumb:
                            liStyle.setArt({'thumb': thumb})
                        else:
                            xbmc.log('NO THUMB2', xbmc.LOGINFO)
                    liStyle.setArt({'fanart': G.FANART_PATH})
                    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)
                    if titolo not in G.LIST_PROGRAMMI:
                        G.LIST_PROGRAMMI.append(titolo)

        for dati in tutti_programmi:
            if dati.find('div', class_='titolo'):
                titolo = dati.find('div', class_='titolo').text.strip()
                # xbmc.log('TITLE2: '+str(titolo),xbmc.LOGINFO)
                liStyle = xbmcgui.ListItem(titolo, offscreen=True)
                url_trovato = dati.a.get('href').strip()
                # xbmc.log('URL TROVATO-----: '+str(url_trovato),xbmc.LOGINFO)
                if url_trovato != '/meteola7' and url_trovato != '/meteo-della-sera' and url_trovato != '/tgla7' and url_trovato != '/film' and url_trovato != '/film-e-fiction':
                    if url_trovato == '/facciaafaccia':
                        url_trovato = '/faccia-a-faccia'
                    if url_trovato == '/il-boss-dei-comici':
                        url_trovato = '/boss-dei-comici'
                    if url_trovato == '/lariadestate':
                        url_trovato = '/laria-destate'
                    if url_trovato == '/taga-doc':
                        url_trovato = '/tagada-doc'
                    link = G.URL_BASE + url_trovato
                    # xbmc.log('LINK-----: '+str(link),xbmc.LOGINFO)
                    if len(dati) > 0:
                        try:
                            thumb = dati.find('div', class_='image-bg lozad').get('data-background-image')
                        except Exception as e:
                            e = sys.exc_info()[0]
                            xbmc.log('EXCEP THUMB3: ' + str(e), xbmc.LOGINFO)
                            thumb = ''
                        if thumb:
                            liStyle.setArt({'thumb': thumb})
                        else:
                            xbmc.log('NO THUMB3', xbmc.LOGINFO)
                    liStyle.setArt({'fanart': G.FANART_PATH})
                    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

        # Prog aggiunti manualmente
        programmi = {
            'LA MALA EDUCAXXXION 2': {
                'url': '/la-mala-educaxxxion',
                'img': 'https://kdam.iltrovatore.it/p/103/sp/10300/thumbnail/entry_id/0_j0z82ps2/version/100001/type/5/width/600/height/360/quality/100/name/0_j0z82ps2.jpg'
            },
            'NON CLASSIFICATI': {
                'url': '/non-classificati',
                'img': '',
            },
        }
        for programma, program_info in programmi.items():
            titolo = programma
            liStyle = xbmcgui.ListItem(titolo, offscreen=True)
            url_trovato = program_info['url']
            link = G.URL_BASE + url_trovato
            thumb = program_info['img']
            liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
            add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

        xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_la7prime():
    titolo = 'LA7 Prime'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/la7prime'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'la7prime.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Film'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/film'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'film.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Film e Fiction'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/film-e-fiction'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'filmfiction.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_lettera_teche_la7():
    req_teche = Request(G.URL_TECHE_LA7, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page_teche = urlopen(req_teche)
    html_teche = BeautifulSoup(page_teche, 'html5lib')
    teche_la7 = html_teche.find_all('div', class_='list-item')

    if teche_la7:
        for dati in teche_la7:
            if dati.find('div', class_='titolo'):
                nomicognomi = dati.find('div', class_='titolo').text.strip()
                cognominomi = " ".join(reversed(nomicognomi.split(" ")))
                liStyle = xbmcgui.ListItem(cognominomi, offscreen=True)
                url_trovato = dati.a.get('href').strip()
                link = G.URL_BASE + url_trovato
                # xbmc.log('LINK-----: '+str(link),xbmc.LOGINFO)
                if len(dati) > 0:
                    try:
                        thumb = 'https:' + dati.find('div', class_='image-bg lozad').get('data-background-image')
                    except Exception as e:
                        e = sys.exc_info()[0]
                        xbmc.log('EXCEP THUMB4: ' + str(e), xbmc.LOGINFO)
                        thumb = ''
                    if thumb:
                        liStyle.setArt({'thumb': thumb})
                    else:
                        xbmc.log('NO THUMB4', xbmc.LOGINFO)
                liStyle.setArt({'fanart': G.FANART_PATH})
                add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, cognominomi)

        xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_lettera_tg_meteo():
    titolo = 'TG LA7'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/tgla7'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'tgla7.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'TG LA7d'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = G.URL_TGLA7D
    thumb = os.path.join(G.THUMB_PATH, 'tgla7d.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Omnibus News'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'flag_omnibus_news'
    thumb = os.path.join(G.THUMB_PATH, 'omnibusnews.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Meteo LA7'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/meteola7'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'meteola7.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Meteo della Sera'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    url_trovato = '/meteo-della-sera'
    link = G.URL_BASE + url_trovato
    thumb = os.path.join(G.THUMB_PATH, 'meteodellasera.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def video_programma():
    page = ''
    first = None

    # xbmc.log('LINK GLOBAL------: '+str(G.LINK),xbmc.LOGINFO)
    if G.LINK == 'flag_omnibus_news':
        G.OMNIBUS_NEWS = True
        G.LINK = G.URL_BASE + '/omnibus'

    if (G.PAGENUM == 0) and (G.LINK != G.URL_BASE + '/film'):
        video_programma_landpage()

    if G.LINK != G.URL_TGLA7D:
        req = Request(G.LINK + "/rivedila7", headers={'user-agent': G.HEADERS_SET['user-agent']})
        try:
            page = urlopen(req)
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP URL: ' + str(e), xbmc.LOGINFO)
            if xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005)):
                xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
                return
        html = BeautifulSoup(page, 'html5lib')

        if G.PAGENUM == 0:
            xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url='', listitem=xbmcgui.ListItem("[B][COLOR blue]" + 'SETTIMANA' + "[/COLOR][/B]", offscreen=True))
            # FIRST VIDEO
            if html.find('div', class_='ultima_puntata'):
                first = html.find('div', class_='ultima_puntata')
            elif html.find('div', class_='contenitoreUltimaReplicaLa7d'):
                first = html.find('div', class_='contenitoreUltimaReplicaLa7d')
            elif html.find('div', class_='contenitoreUltimaReplicaNoLuminosa'):
                first = html.find('div', class_='contenitoreUltimaReplicaNoLuminosa')
            else:
                xbmc.log('NO FIRST VIDEO', xbmc.LOGINFO)
                if xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005)):
                    xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)
                    return
            titolo = first.find('div', class_='title_puntata').text.strip()

            if G.OMNIBUS_NEWS:
                first_video(first, titolo, titolo.find(G.FILTRO_OMNIBUS) != -1)
            elif G.LINK == G.URL_BASE + '/omnibus':
                first_video(first, titolo, titolo.find(G.FILTRO_OMNIBUS) == -1)
            else:
                first_video(first, titolo, True)
            # xbmc.log('FIRST VIDEO----: '+str(titolo),xbmc.LOGINFO)

            # WEEK VIDEO
            if html.findAll(text=" LA SETTIMANA"):
                video_settimana = html.find('div', class_='home-block__content-carousel container-vetrina').find_all('div', class_='item')
                # xbmc.log('LA SETTIMANA----: '+str(video_settimana),xbmc.LOGINFO)
                if video_settimana:
                    get_rows_video(video_settimana)
            else:
                xbmc.log('NO WEEK VIDEO', xbmc.LOGINFO)

            if html.findAll(text="Puntate Cult"):
                xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url='', listitem=xbmcgui.ListItem("[B][COLOR blue]" + 'ARCHIVIO' + "[/COLOR][/B]", offscreen=True))

        # CULT VIDEO
        if html.findAll(text="Puntate Cult"):
            if (G.LINK == G.URL_BASE + '/chi-sceglie-la-seconda-casa') or (
                    G.LINK == G.URL_BASE + '/lingrediente-perfetto'):
                req2 = Request(G.LINK + "/rivedila7", headers={'user-agent': G.HEADERS_SET['user-agent']})
            else:
                req2 = Request(G.LINK + "/rivedila7/archivio?page=" + str(G.PAGENUM), headers={'user-agent': G.HEADERS_SET['user-agent']})
            page2 = urlopen(req2)
            html2 = BeautifulSoup(page2, 'html5lib')
            video_archivio = html2.find('div', class_='view-content clearfix').find_all('div', class_='views-row')
            if video_archivio:
                get_rows_video(video_archivio)

                if not G.OMNIBUS_NEWS:
                    page = html2.find('li', class_='pager-next')
                    pagenext(page)
    # Tg LA7d
    else:
        req = Request(G.LINK + "?page=" + str(G.PAGENUM), headers={'user-agent': G.HEADERS_SET['user-agent']})
        page = urlopen(req)
        html = BeautifulSoup(page, 'html5lib')
        video_tgla7d = html.find('div', class_='tgla7-category').find_all('article', class_='tgla7-new clearfix')
        if video_tgla7d:
            get_rows_video_tgla7d(video_tgla7d)
            page = html.find('li', class_='next')
            pagenext(page)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def video_programma_teche_la7():
    # xbmc.log('LINK------: '+str(G.LINK),xbmc.LOGINFO)
    req = Request(G.LINK + "?page=" + str(G.PAGENUM), headers={'user-agent': G.HEADERS_SET['user-agent']})
    page = urlopen(req)
    html = BeautifulSoup(page, 'html5lib')

    if G.PAGENUM == 0:
        # PREVIEW VIDEO
        video_preview = html.find('div', class_='vetrina-protagonista')
        if video_preview:
            get_rows_video_techela7_preview(video_preview)

    # ARCHIVIO VIDEO    
    if html.find('div', class_='view-content clearfix'):
        video_techela7 = html.find('div', class_='view-grouping-content').find_all('div', class_='list-item')
        if video_techela7:
            get_rows_video_techela7(video_techela7)
            page = html.find('li', class_='pager-next')
            pagenext(page)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def first_video(first, titolo, filtro):
    if filtro:
        thumblink = first.find('div', class_='holder-bg lozad').get('data-background-image')
        if thumblink.startswith('//'):
            thumb = 'https:' + thumblink
        else:
            thumb = thumblink
        # xbmc.log('THUMB 1------: '+str(thumb),xbmc.LOGINFO)
        data_orig = first.find('div', class_='scritta_ultima').text.strip()
        data = '[I] - (' + data_orig.replace('/', '.') + ')[/I]'
        try:
            plot = first.find('div', class_='occhiello').text.strip()
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP PLOT1: ' + str(e), xbmc.LOGINFO)
            plot = ""
        link = G.URL_BASE + first.find('a').get('href')
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def video_list(div, titolo, filtro):
    if filtro:
        thumblink = div.find('div', class_='bg-img lozad').get('data-background-image')
        if thumblink.startswith('//'):
            thumb = 'https:' + thumblink
        else:
            thumb = thumblink
        # xbmc.log('THUMB 2------: '+str(thumb),xbmc.LOGINFO)
        # subdata=div.find('a').get('href')
        # data='[I] - ('+subdata[24:34]+')[/I]'
        try:
            data_orig = div.find('div', class_='data').text.strip()
            data = '[I] - (' + data_orig.replace('/', '.') + ')[/I]'
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP DATA_1: ' + str(e), xbmc.LOGINFO)
            data = ""
        plot = ''
        link = G.URL_BASE + div.find('a').get('href')
        # xbmc.log('TEST------: '+str(data),xbmc.LOGINFO)
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def get_rows_video(video):
    for div in video:
        titolo = div.find('div', class_='title').text.strip()
        # xbmc.log('TITOLO: '+str(titolo.find(G.FILTRO_OMNIBUS)),xbmc.LOGINFO)
        if G.OMNIBUS_NEWS:
            video_list(div, titolo, titolo.find(G.FILTRO_OMNIBUS) != -1)
        elif G.LINK == G.URL_BASE + '/omnibus':
            video_list(div, titolo, titolo.find(G.FILTRO_OMNIBUS) == -1)
        else:
            video_list(div, titolo, True)


def get_rows_video_tgla7d(video):
    for div in video:
        titolo = div.find('div', class_='tgla7-condividi').get('data-title').strip()
        thumb_link = div.find('div', class_='tgla7-img').get('style')
        thumb = thumb_link[22:-1]
        try:
            plot = div.find('div', class_='tgla7-descrizione').text.strip()
        except Exception as e:
            e = sys.exc_info()[0]
            xbmc.log('EXCEP PLOT_TGLA7d: ' + str(e), xbmc.LOGINFO)
            plot = ""
        link = div.find('div', class_='tgla7-condividi').get('data-share')
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo, "thumb": thumb, "plot": plot}, liStyle, folder=False)


def get_rows_video_techela7_preview(video):
    # xbmc.log('TEST-----: '+str(video),xbmc.LOGINFO)
    regex5 = 'poster: "(.*?)"'
    html = str(video)

    titolo = video.find('a', class_='title').text.strip()
    data = '[I] - (' + video.find('span', class_='date-display-single').text.strip() + ')[/I]'
    # xbmc.log('DATA-----: '+str(data),xbmc.LOGINFO)
    if re.findall(regex5, html):
        # xbmc.log('REGEX----------: '+str(re.findall(regex5, html)),xbmc.LOGINFO)
        thumb = 'https:' + re.findall(regex5, html)[0]
    else:
        thumb = ''
    plot = video.find('div', class_='description').text.strip()
    link = G.URL_BASE + video.find('a', class_='title').get('href')
    liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {'plot': plot})
    add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, folder=False)


def get_rows_video_techela7(video):
    for div in video:
        titolo = div.find('div', class_='title').text.strip()
        data = '[I] - (' + div.find('div', class_='data').text.strip() + ')[/I]'
        # xbmc.log('DATA-----: '+str(data),xbmc.LOGINFO)
        thumb = 'https:' + div.find('div', class_='bg-img lozad').get('data-background-image')
        plot = ""
        link = G.URL_BASE + div.a.get('href').strip()
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, folder=False)


def video_programma_landpage():
    # xbmc.log('LINK GLOBAL_LAND------: '+str(G.LINK),xbmc.LOGINFO)
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url='', listitem=xbmcgui.ListItem("[B][COLOR blue]" + 'HOME' + "[/COLOR][/B]", offscreen=True))

    if G.LINK == G.URL_BASE + '/faccia-a-faccia':
        link_landpage = G.URL_BASE + '/facciaafaccia'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    elif G.LINK == G.URL_BASE + '/boss-dei-comici':
        link_landpage = G.URL_BASE + '/il-boss-dei-comici'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    elif G.LINK == G.URL_BASE + '/laria-destate':
        link_landpage = G.URL_BASE + '/lariadestate'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    elif G.LINK == G.URL_BASE + '/tagada-doc':
        link_landpage = G.URL_BASE + '/taga-doc'
        req = Request(link_landpage, headers={'user-agent': G.HEADERS_SET['user-agent']})
    else:
        req = Request(G.LINK, headers={'user-agent': G.HEADERS_SET['user-agent']})
    page = urlopen(req)
    html = BeautifulSoup(page, 'html5lib')

    # VIDEO INIZIALE
    video_iniziale = html.find('div', class_='ultima_puntata')
    if video_iniziale:
        get_rows_video_landpage_preview(video_iniziale)

    # PUNTATE    
    if (html.findAll(text="puntate")) or (html.findAll(text="Guarda ora")):
        # xbmc.log('TEST------: '+str(html.find('div',class_='home-block__content-inner')),xbmc.LOGINFO)
        video_puntate_1r = html.find('div', class_='home-block__content-inner').select('div[class="item"]')
        video_puntate_2r = html.find('section', class_='home-block home-block--oggi-striscia home-block--fixed').find_all('div', class_='item')
        # xbmc.log('TEST------: '+str(video_puntate_2r),xbmc.LOGINFO)
        if video_puntate_1r:
            get_rows_video_landpage(video_puntate_1r)
        if video_puntate_2r:
            get_rows_video_landpage(video_puntate_2r)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    # xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def get_rows_video_landpage_preview(video):
    # xbmc.log('TEST-----: '+str(video),xbmc.LOGINFO)
    titolo = video.find('div', class_='title_puntata').text.strip()
    data = '[I] - (' + video.find('div', class_='scritta_ultima').text.strip() + ')[/I]'
    thumblink = video.find('div', class_='holder-bg lozad').get('data-background-image')
    if thumblink.startswith('//'):
        thumb = 'https:' + thumblink
    else:
        thumb = thumblink
    plot = video.find('div', class_='occhiello').text.strip()
    link = G.URL_BASE + video.find('a').get('href')
    liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {'plot': plot})
    add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def get_rows_video_landpage(video):
    # xbmc.log('VIDEO-----: '+str(video),xbmc.LOGINFO)
    for div in video:
        titolo = div.find('div', class_='occhiello').text.strip()
        # xbmc.log('TITOLO-----: '+str(titolo),xbmc.LOGINFO)
        data = '[I] - (' + div.find('div', class_='data').text.strip() + ')[/I]'
        thumblink = div.find('div', class_='bg-img lozad').get('data-background-image')
        if thumblink.startswith('//'):
            thumb = 'https:' + thumblink
        else:
            thumb = thumblink
        plot = ""
        link = G.URL_BASE + div.a.get('href').strip()
        liStyle = xbmcgui.ListItem(titolo + data, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data, "thumb": thumb, "plot": plot}, liStyle, titolo + data, folder=False)


def pagenext(pagenb):
    if pagenb:
        liStyle = xbmcgui.ListItem('[B]' + G.LANGUAGE(32003) + '[/B]', offscreen=True)
        liStyle.setArt({'fanart': G.FANART_PATH})
        add_directory_item_nodup({"mode": G.MODE, "link": G.LINK, "page": G.PAGENUM + 1}, liStyle)


def run(argv):
    """ Addon entry point """
    G.init_globals(argv)

    if G.PARAMS.get("page", "") == "":
        G.PAGENUM = 0
    else:
        G.PAGENUM = int(G.PARAMS.get("page", ""))

    if G.MODE == "diretta_la7":
        play_dirette(G.URL_LIVE_LA7, True)

    elif G.MODE == "diretta_la7d":
        play_dirette(G.URL_LIVE_LA7D, True)

    elif G.MODE == "rivedi_la7":
        if G.PLAY == "":
            if G.GIORNO == "":
                rivedi(G.URL_RIVEDILA7, 'rivedila7.jpg')
            else:
                rivedi_giorno()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "rivedi_la7d":
        if G.PLAY == "":
            if G.GIORNO == "":
                rivedi(G.URL_RIVEDILA7D, 'rivedila7d.jpg')
            else:
                rivedi_giorno()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "la7_prime":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_la7prime()
            else:
                video_programma()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "tutti_programmi":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera()
            else:
                video_programma()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "tg_meteo":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera_tg_meteo()
            else:
                video_programma()
        else:
            play_video(G.PLAY, False)

    elif G.MODE == "teche_la7":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera_teche_la7()
            else:
                video_programma_teche_la7()
        else:
            play_video(G.PLAY, False)

    else:
        show_root_menu()
