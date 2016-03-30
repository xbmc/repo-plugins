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

import xbmcvfs
from common_variables import *
from net import Net

mensagemok=xbmcgui.Dialog().ok


def abrir_url(url ,referer = base_url):
    if not os.path.exists(datapath): xbmcvfs.mkdir(datapath)

    net = Net(cookie_file=cookie_TviFile, proxy='', user_agent=user_agent, http_debug=True)
    if os.path.exists(cookie_TviFile): net.set_cookies(cookie_TviFile)
    try:
        ref_data = {'Referer':referer}
        html = net.http_GET(url,headers=ref_data).content.encode('latin-1', 'ignore')
        net.save_cookies(cookie_TviFile)
        return html
    except:
        return ''



def post_url(actionUrl,data = {},referer= base_url):
    if not os.path.exists(datapath): xbmcvfs.mkdir(datapath)
    net = Net(cookie_file=cookie_TviFile, proxy='', user_agent=user_agent, http_debug=True)
    try:
        ref_data = {'Referer':referer}
        html = net.http_POST(actionUrl,form_data=data,headers=ref_data).content.encode('latin-1', 'ignore')
        net.save_cookies(cookie_TviFile)
        return html
    except:
        return ''
