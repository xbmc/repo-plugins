# -*- coding: utf-8 -*-
from resources.lib.mediaset import Mediaset
from phate89lib import kodiutils, staticutils

mediaset = Mediaset()
mediaset.log = kodiutils.log
def pulisci_cerca(s):
    s = s.lower()
    s = s.replace("à","a")
    s = s.replace("è","e")
    s = s.replace("é","e")
    s = s.replace("ì","i")
    s = s.replace("ò","o")
    s = s.replace("ù","u")
    s = s.replace(" ","-")
    s = s.replace("'","-")
    return s

def stamp_ep(ep):
    ep['mediatype'] = 'video'
    kodiutils.addListItem("[COLOR blue]"+ep["title"]+"[/COLOR]", {'mode':'playMediaset','id':ep["id"]}, thumb=ep["thumbs"],videoInfo=ep,isFolder=False)

def stamp_live(ch):
    ch['mediatype'] = 'video'
    kodiutils.addListItem("[COLOR blue]"+ch["title"]+"[/COLOR]", {'mode':'playLive','stream_url':ch["url"]}, thumb=kodiutils.IMAGE_PATH_T + ch["thumbs"],videoInfo=ch,isFolder=False)

def root():
    kodiutils.addListItem("Canali Live",{'mode':'canali_live'})
    kodiutils.addListItem("Elenco programmi",{'mode':'elenco_programmi'})
    kodiutils.addListItem("Ultime puntate News",{'mode':'ultime_puntate','prog_tipo':'news'})
    kodiutils.addListItem("Ultime puntate Sport",{'mode':'ultime_puntate','prog_tipo':'sport'})
    kodiutils.addListItem("Ultime puntate Intrattenimento",{'mode':'ultime_puntate','prog_tipo':'intrattenimento'})
    kodiutils.addListItem("Ultime puntate Fiction",{'mode':'ultime_puntate','prog_tipo':'fiction'})
    kodiutils.addListItem("Ultime puntate Elenco canali",{'mode':'ultime_puntate_canali'})
    kodiutils.addListItem("Ultime Sport Mediaset",{'mode':'sportmediaset'})
    kodiutils.addListItem("Più visti Ieri",{'mode':'piuvisti','range_visti':'ieri'})
    kodiutils.addListItem("Più visti Settimana",{'mode':'piuvisti','range_visti':'settimana'})
    kodiutils.addListItem("Più visti Mese",{'mode':'piuvisti','range_visti':'mese'})
    kodiutils.addListItem("Cerca...",{'mode':'cerca'})
    kodiutils.endScript()

def sportmediaset_root():
    kodiutils.addListItem("Highlights",{'mode':'sportmediaset','progsport_tipo':'/tutti_i_gol/'})
    kodiutils.addListItem("Calcio",{'mode':'sportmediaset','progsport_tipo':'/calcio/'})
    kodiutils.addListItem("Champions League",{'mode':'sportmediaset','progsport_tipo':'/champions_league/'})
    kodiutils.addListItem("Europa League",{'mode':'sportmediaset','progsport_tipo':'/europa_league/'})
    kodiutils.addListItem("Superbike",{'mode':'sportmediaset','progsport_tipo':'/superbike/'})
    kodiutils.addListItem("Altri sport",{'mode':'sportmediaset','progsport_tipo':'/altrisport/'})
    kodiutils.addListItem("Motori",{'mode':'sportmediaset','progsport_tipo':'/motori/'})
    kodiutils.endScript()

def puntate_canali_root():
    kodiutils.addListItem("Italia 1",{'mode':'ultime_puntate','prog_tipo':'I1'}, thumb=kodiutils.IMAGE_PATH_T + "Italia_1.png")
    kodiutils.addListItem("Canale 5",{'mode':'ultime_puntate','prog_tipo':'C5'}, thumb=kodiutils.IMAGE_PATH_T + "Canale_5.png")
    kodiutils.addListItem("Rete 4",{'mode':'ultime_puntate','prog_tipo':'R4'}, thumb=kodiutils.IMAGE_PATH_T + "Rete_4.png")
    kodiutils.addListItem("Italia 2",{'mode':'ultime_puntate','prog_tipo':'I2'}, thumb=kodiutils.IMAGE_PATH_T + "Italia_2.png")
    kodiutils.addListItem("La 5",{'mode':'ultime_puntate','prog_tipo':'KA'}, thumb=kodiutils.IMAGE_PATH_T + "La_5.png")
    kodiutils.addListItem("TGCOM24",{'mode':'ultime_puntate','prog_tipo':'KF'}, thumb=kodiutils.IMAGE_PATH_T + "TGCOM24.png")
    kodiutils.addListItem("Iris",{'mode':'ultime_puntate','prog_tipo':'KI'}, thumb=kodiutils.IMAGE_PATH_T + "Iris.png")
    kodiutils.endScript()

def canali_live_root():
    kodiutils.setContent('videos')
    for ch in mediaset.get_canali_live():
        stamp_live(ch)
    kodiutils.endScript()

def elenco_programmi_root():
    for lettera in mediaset.get_prog_root():
        kodiutils.addListItem(lettera["index"],{'mode':'elenco_programmi','prog_id':lettera["index"]})
    kodiutils.endScript()

def elenco_programmi_list(progId):
    kodiutils.setContent('videos')
    for lettera in mediaset.get_prog_root():
        if lettera['index'] == progId:
            for programma in lettera["program"]:    
                kodiutils.addListItem(programma["label"],{'mode':'elenco_programmi','prog_url':programma["url"]}, thumb=programma['thumbnail'])
    kodiutils.endScript()

def elenco_programmi_groupList(progUrl):
    for group in mediaset.get_url_groupList(progUrl):
        kodiutils.addListItem(group["title"], {'mode':'elenco_programmi', 'group_url': group["url"]})
    for season in mediaset.get_prog_seasonList(progUrl):
        kodiutils.addListItem(season["title"],{'mode':'elenco_programmi','prog_url':season["url"]})
    kodiutils.endScript()

def elenco_programmi_epList(groupUrl):
    kodiutils.setContent('videos')
    for ep in mediaset.get_prog_epList(groupUrl):
        stamp_ep(ep)
    kodiutils.endScript()

def sportmediaset_epList(progsportTipo):
    kodiutils.setContent('videos')
    for ep in mediaset.get_global_epList(2):
        if (progsportTipo in ep["url"]): stamp_ep(ep)        
    kodiutils.endScript()

def puntate_epList(progTipo):
    kodiutils.setContent('videos')
    for ep in mediaset.get_global_epList(0):
        if (progTipo in ep["tipo"]): stamp_ep(ep)
    kodiutils.endScript()

def piuvisti_epList(rangeVisti):
    kodiutils.setContent('videos')
    for ep in mediaset.get_global_epList(1,rangeVisti):
        stamp_ep(ep)
    kodiutils.endScript()

def cerca():
    kodiutils.setContent('videos')
    kb = kodiutils.getKeyboard()
    kb.setHeading("Cerca un programma")
    kb.doModal()
    if kb.isConfirmed():
        text = kb.getText()
        text = pulisci_cerca(text)
        for lettera in mediaset.get_prog_root():
            for programma in lettera["program"]:
                if (programma["mc"].find(text) > 0):
                    kodiutils.addListItem(programma["label"],{'mode':'elenco_programmi','prog_url':programma["url"]}, thumb=programma['thumbnail'])
    kodiutils.endScript()

def playMediaset(streamId):
    url = mediaset.get_stream(streamId)
    if (url):
        # Play the item
        if ("mp4" in url): kodiutils.setResolvedUrl(url["mp4"])
        elif ("f4v" in url): kodiutils.setResolvedUrl(url["f4v"])
        elif ("wmv" in url): kodiutils.setResolvedUrl(url["wmv"])
    kodiutils.setResolvedUrl(solved=False)

def playLive(streamUrl):
    # Play the item
    kodiutils.setResolvedUrl(streamUrl)

# parameter values
params = staticutils.getParams()
mode = str(params.get("mode", ""))
progId = str(params.get("prog_id", ""))
progUrl = str(params.get("prog_url", ""))
groupUrl = str(params.get("group_url", ""))
progTipo = str(params.get("prog_tipo", ""))
progsportTipo = str(params.get("progsport_tipo", ""))
title = str(params.get("title", ""))
streamId = str(params.get("id", ""))
streamUrl = str(params.get("stream_url", ""))
thumbs = str(params.get("thumbs", ""))
desc = str(params.get("desc", ""))
rangeVisti = str(params.get("range_visti", ""))

if 'mode' in params:
    if params['mode'] == "canali_live":
        canali_live_root()
    elif params['mode'] == "elenco_programmi":
        if 'prog_id' in params:
            elenco_programmi_list(params['prog_id'])
        elif 'prog_url' in params:
            elenco_programmi_groupList(params['prog_url'])
        elif 'group_url' in params:
            elenco_programmi_epList(params['group_url'])
        else:
            elenco_programmi_root()
    elif params['mode'] == "sportmediaset":
        if 'progsport_tipo'in params:
            sportmediaset_epList(params['progsport_tipo'])
        else:
            sportmediaset_root()
    elif params['mode'] == "ultime_puntate":
        puntate_epList(params['prog_tipo'])
    elif params['mode'] == "ultime_puntate_canali":
        puntate_canali_root()
    elif params['mode'] == "piuvisti":
        piuvisti_epList(params['range_visti'])
    elif params['mode'] == "cerca":
        cerca()
    elif params['mode'] == "playMediaset":
        playMediaset(params['id'])
    elif params['mode'] == "playLive":
        playLive(params['stream_url'])
else:
    root()

