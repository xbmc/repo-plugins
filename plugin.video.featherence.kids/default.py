# -*- coding: utf-8 -*-

import urllib,urllib2,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os,random
import json

from variables import *
from modules import *

url, name, mode, iconimage, desc, num, viewtype, fanart = pluginend(admin)

pluginend2(admin, url, containerfolderpath, viewtype)