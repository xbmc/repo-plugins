import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import resources.lib.const_localize as clo;
from BeautifulSoup import BeautifulSoup
import re

def loadlist():
    lp_url='https://longnow.org/membership/signin/'
    headers = {'Referer': lp_url}
    lp = requests.get(lp_url+'?next=/seminars/list', headers=headers)
    
    if lp.status_code!=200:
        xbmcgui.Dialog().ok(my_addon.getLocalizedString(clo.ERR_NO_LOGIN),
                            my_addon.getLocalizedString(clo.INF_HTTP_STATE) % lp.status_code)
        return
        
    loginSoup=BeautifulSoup(lp.text)
    form= loginSoup.find("form")
    token=loginSoup.find("input", {"name":"csrfmiddlewaretoken"})
        
    username=my_addon.getSetting('username')
    password=my_addon.getSetting('password')
        
    if (username is None) or (username==""):
        xbmcgui.Dialog().ok(my_addon.getLocalizedString(clo.ERR_INV_USER),
                            my_addon.getLocalizedString(clo.HELP_INV_USER))
    if (password is None) or (password==""):
        xbmcgui.Dialog().ok(my_addon.getLocalizedString(clo.ERR_INV_PWD),
                            my_addon.getLocalizedString(clo.HELP_INV_PWD))
                
    data= {
        'username': username,
        'password': password,
        'next': '/seminars/list',
        'csrfmiddlewaretoken': token['value']
    }
                
    r = requests.post(lp_url, data=data, headers=headers,cookies=lp.cookies)
                
    listpage=r
                
    if listpage.status_code!=200:
        xbmcgui.Dialog().ok(my_addon.getLocalizedString(clo.ERR_NO_ACCESS),
                            my_addon.getLocalizedString(clo.INF_HTTP_STATE) % listpage.status_code,
                            my_addon.getLocalizedString(clo.HELP_NO_LOGIN))
        return
                    
    listSoup=BeautifulSoup(listpage.text)
                    
    errorblock=listSoup.find("div",{'class':'error_block'})
    if errorblock is not None:
        xbmcgui.Dialog().ok(my_addon.getLocalizedString(clo.ERR_NO_ACCESS),
                            my_addon.getLocalizedString(clo.INF_MSG_SERVER) % "".join(errorblock.findAll(text=True)))
        return
                       
    hdstring=re.compile('Full HD Video');
    for dl in listSoup.findAll("ul", 'download_list'):
        hdlink=dl.find('a',title=hdstring);
        if hdlink is not None:
            name=dl.parent.parent.find('td',{'class':'title'}).a.string
            url=hdlink['href'];
            li = xbmcgui.ListItem(name)
            li.setArt({'iconImage':'DefaultVideo.png'})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
my_addon = xbmcaddon.Addon()

xbmcplugin.setContent(addon_handle, 'movies')

try:
    loadlist()
except requests.exceptions.RequestException as e:
    xbmcgui.Dialog().ok(my_addon.getLocalizedString(clo.ERR_NO_CONNECT), str(e))
    
xbmcplugin.endOfDirectory(addon_handle)
