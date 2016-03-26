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
from datetime import date, timedelta
import xbmc,re,logging
from common_variables import *

def title_clean_up(title):
    title=title.replace('\xc3', "Ã").replace('\xd3', "Ó").replace('\xda', "Ú").replace('\xca', "Ê").replace('\xc9', "É").replace('\xc7', "Ç").replace('\xcd', "Í").replace('\xc2', "Â").replace('\xc1', "Á").replace('\xc0', "À").replace('\xe9', "é").replace('\xed', "í").replace('\xf3', "ó").replace('\xe7', "ç").replace('\xe3', "ã").replace('\xe2', "â").replace('\xea', "ê").replace('\xe1', "á").replace('\xfa', "ú").replace('\xe0', "à").replace('&uacute;', "ú").replace('&ccedil;', "ç").replace('&atilde;', "ã").replace('&acirc;', "â").replace('&ecirc;', "ê").replace('&oacute;', "ó").replace('&Oacute;', "Ó").replace('&Aacute;', "Á").replace('&aacute;', "á").replace('&eacute;', "é").replace('\xf5','õ').replace('Emissão em direto ','').replace('<span>','')
    return title

def removeNonAscii(s): return "".join(filter(lambda x: ord(x)<128, s))

def format_data(data):
    dateformate = "%d/%m/%Y"
    if data=="Hoje" : return date.today().strftime(dateformate)
    if data=="Ontem" : return (date.today() - timedelta(days=1)).strftime(dateformate)
    try:
        data = re.compile('\w*,?\s+(\d+)\s+(\w+),?\s+(\d+)').findall(data)
        if data[0][1].lower() == 'jan': mes = '01'
        elif data[0][1].lower() == 'fev': mes = '02'
        elif data[0][1].lower() == 'mar': mes = '03'
        elif data[0][1].lower() == 'abr': mes = '04'
        elif data[0][1].lower() == 'mai': mes = '05'
        elif data[0][1].lower() == 'jun': mes = '06'
        elif data[0][1].lower() == 'jul': mes = '07'
        elif data[0][1].lower() == 'ago': mes = '08'
        elif data[0][1].lower() == 'set': mes = '09'
        elif data[0][1].lower() == 'out': mes = '10'
        elif data[0][1].lower() == 'nov': mes = '11'
        elif data[0][1].lower() == 'dez': mes = '12'
        return date(int(data[0][2]),int(mes),int(data[0][0])).strftime(dateformate)
    except Exception as e:
        logging.exception("message")
        return '00/00/00'

def translate(text):
      return selfAddon.getLocalizedString(text).encode('utf-8')

def convert_to_minutes(duration):
    try:
        split = re.compile('(\d+):(\d+):(\d+)').findall(duration)
        return int(split[0][0])*3600 + int(split[0][1])*60 + int(split[0][2])
    except: return '0'

def setview(setting_name):
    setting = selfAddon.getSetting(setting_name)
    if setting == "0": xbmc.executebuiltin("Container.SetViewMode(50)")
    elif setting == "1": xbmc.executebuiltin("Container.SetViewMode(51)")
    elif setting == "2": xbmc.executebuiltin("Container.SetViewMode(500)")
    elif setting == "3":
        if "nox" in xbmc.getSkinDir(): xbmc.executebuiltin("Container.SetViewMode(56)")
        else: xbmc.executebuiltin("Container.SetViewMode(501)")
    elif setting == "4":
        if "nox" in xbmc.getSkinDir(): xbmc.executebuiltin("Container.SetViewMode(57)")
        else: xbmc.executebuiltin("Container.SetViewMode(508)")
    elif setting == "5": 
        if "nox" in xbmc.getSkinDir(): xbmc.executebuiltin("Container.SetViewMode(55)")
        else: xbmc.executebuiltin("Container.SetViewMode(504)")
    elif setting == "6":
        if "nox" in xbmc.getSkinDir(): xbmc.executebuiltin("Container.SetViewMode(51)")        
        else:xbmc.executebuiltin("Container.SetViewMode(503)")
    elif setting == "7":
        if "nox" in xbmc.getSkinDir(): xbmc.executebuiltin("Container.SetViewMode(501)")
        else: xbmc.executebuiltin("Container.SetViewMode(515)")
    return

def getProgramaId(url):
    return re.findall(".*/?programa/[\w\d-]*/([\d\w]+)",url)[0];

def getAjaxUrl(programaId, temporada, tipo, pagina ='1'):
    return 'http://tviplayer.iol.pt/ajax/multimedias/%s/%s/%s/%s' % (programaId, temporada, tipo, pagina)

def getListaProgramasUrl(ano='', letra='', canal='', categoria='' ,pagina='1'):
    return 'http://tviplayer.iol.pt/programas/ultimos/ano:%s/letra:%s/canal:%s/categoria:%s/%s' % (ano, letra, canal, categoria ,pagina)

def getProximaPagina(url):
    x =url.rindex('/')
    try:
        newUrl =url[:x+1] + str(int(url[x+1:])+1)
    except:
        newUrl =url+'/2'
    return newUrl