import xbmc ,xbmcaddon
import os,md5
from django.utils.encoding import smart_str
def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
     
def savemessage(addon,message,image1,grey,lesezeit,xmessage,ymessage,breitemessage,hoehemessage,breitebild1,hoehebild1,fontname="font14",fontcolor="FFFFFFFF",startxbild1=-1,startybild1=-1,image2="",startxbild2=-1,startybild2=-1,breitebild2=0,hoehebild2=0):
    __addonname__ = addon.getAddonInfo('name')
    popupaddon=xbmcaddon.Addon("service.popwindow")
    popupprofile    = xbmc.translatePath( popupaddon.getAddonInfo('profile') ).decode("utf-8")
    popuptemp       = xbmc.translatePath( os.path.join( popupprofile, 'temp', '') ).decode("utf-8")
    message=smart_str(message)
    image1=unicode(image1).encode('utf-8')
    image2=unicode(image2).encode('utf-8')
    debug("message :"+message)
    debug("image :"+image1)
    debug("image :"+image2)
    debug("grey :"+grey)
    debug("popuptemp :"+popuptemp)
    debug("lesezeit :"+str(lesezeit))
    filename=__addonname__ + "_"+md5.new(message).hexdigest()  
    f = open( os.path.join(popuptemp,filename), 'w')    
    f.write(message+"###"+image1+"###"+grey+"###"+str(lesezeit)+"###"+str(xmessage)+"###"+str(ymessage)+"###"+ str(breitemessage)+"###"+str(hoehemessage)+"###"+str(startxbild1)+"###"+str(startybild1)+ "###"+str(breitebild1)+"###"+str(hoehebild1)+"###"+image2+"###"+str(startxbild2)+"###"+str(startybild2)+ "###"+str(breitebild2)+"###"+str(hoehebild2)+"###"+ str(fontname)+"###"+fontcolor)
    f.close()     
def  deletemessage(addon):
    __addonname__ = addon.getAddonInfo('name')
    popupaddon=xbmcaddon.Addon("service.popwindow")
    popupprofile    = xbmc.translatePath( popupaddon.getAddonInfo('profile') ).decode("utf-8")
    popuptemp       = xbmc.translatePath( os.path.join( popupprofile, 'temp', '') ).decode("utf-8")
    filename="DELETE_"+__addonname__ 
    f = open( os.path.join(popuptemp,filename), 'w')              
    f.write("DELETE")
    f.close()   