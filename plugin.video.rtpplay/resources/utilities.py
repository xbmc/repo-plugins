#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: enen92 

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
import xbmc,re
from common_variables import *

def title_clean_up(title):
	title=title.replace('\xc3', "Ã").replace('\xd3', "Ó").replace('\xda', "Ú").replace('\xca', "Ê").replace('\xc9', "É").replace('\xc7', "Ç").replace('\xcd', "Í").replace('\xc2', "Â").replace('\xc1', "Á").replace('\xc0', "À").replace('\xe9', "é").replace('\xed', "í").replace('\xf3', "ó").replace('\xe7', "ç").replace('\xe3', "ã").replace('\xe2', "â").replace('\xea', "ê").replace('\xe1', "á").replace('\xfa', "ú").replace('\xe0', "à").replace('&uacute;', "ú").replace('&ccedil;', "ç").replace('&atilde;', "ã").replace('&acirc;', "â").replace('&ecirc;', "ê").replace('&oacute;', "ó").replace('&Oacute;', "Ó").replace('&Aacute;', "Á").replace('&aacute;', "á").replace('&eacute;', "é").replace('\xf5','õ').replace('Emissão em direto ','').replace('<span>','')
	return title.strip()
	
def removeNonAscii(s): return "".join(filter(lambda x: ord(x)<128, s))

def clean_html(text):
	return text.replace('<span id="etcPlus0">...</span><span class="moretext" id="hiddenText0">','').replace('<span onclick="RTPPLAY.utils.textHideShow(0)" id="moreText0" class="maistext" title="Saiba mais sobre o programa"><b> mostrar mais<span class="img_play_nr">','').replace('</span>','').replace('</b>','').replace('</p>','').replace('<br />','').replace('<br/>','').replace('<p>','').replace('<br>','')
	
def format_data(data):
	try:
		data = re.compile('(\d+) (.+?), (\d+)').findall(data)
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
		return data[0][2]+'/'+mes+'/'+data[0][0]
	except: return '00/00/00'
	
