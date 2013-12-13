"""
DAILY_TEXT RELATED FUNCTIONS
"""
import xbmc
import xbmcgui
import xbmcplugin

import os
import jw_config
import jw_common
import re

# Show daily text 
def showDailyText(date):

    language    = jw_config.language

    json_url    = jw_config.wol_url 
    json_url    = json_url + "dt/" 
    json_url    = json_url + jw_config.const[language]["wol"] + "/" + date

    json        = jw_common.loadJsonFromUrl(url = json_url, ajax = True)

    text        = json["items"][0]["content"]
    text        = jw_common.cleanUpText(text)

    dialog = DailiyText()
    dialog.customInit(text)
    dialog.doModal()
    del dialog
    xbmc.executebuiltin('Action("back")')


# Window showing daily text
class DailiyText(xbmcgui.WindowDialog):

    def __init__(self):
        if jw_config.emulating: xbmcgui.Window.__init__(self)

    def customInit(self, text):
        
        border = 50 # px relative to 1280/720 fixed grid resolution

        # width is always 1280, height is always 720.
        # getWidth() and getHeight() instead read the REAL screen resolution
        bg_image = jw_config.dir_media + "blank.png"
        self.ctrlBackgound = xbmcgui.ControlImage(
            0,0, 
            1280, 720, 
            bg_image
        )
        self.ctrlDate= xbmcgui.ControlTextBox(
            border, 0, 
            1280 - border *2, 60, 
            'font35_title', "0xFF0000FF"
        )
        self.ctrlScripture= xbmcgui.ControlTextBox(
            border, 60, 
            1280 - border *2, 140, # Not down 140 !
            'font35_title', "0xFF000000"
        )
        self.ctrlComment= xbmcgui.ControlTextBox(
            border, 200, 
            1280 - border *2, 720 - 200, 
            'font30', "0xFF000000"
        )
        
        self.addControl (self.ctrlBackgound)
        self.addControl (self.ctrlDate)
        self.addControl (self.ctrlScripture)
        self.addControl (self.ctrlComment)

        self.ctrlDate.setText( self.getDateLine(text) )
        self.ctrlScripture.setText( self.getScriptureLine(text) )
        self.ctrlComment.setText( self.getComment(text) )

    #get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
    def onAction(self, action):
        #Every key will close the windo
        self.close()
        return

    # Grep today's textual date
    def getDateLine(self, text):

        regexp_date = "'ss'>([^<].*)</p>"
        date_list = re.findall(regexp_date, text)    
        date = date_list[0] # + " [" + str(self.getWidth()) + " x " + str(self.getHeight()) + "] "
        return date.encode("utf8")

    # Grep holy scripture ref
    def getScriptureLine(self, text):
       
        regexp_scripture = "'sa'>(.*)</div>"
        scripture_list = re.findall(regexp_scripture, text)    
        if scripture_list == []:
            return ""

        scripture = scripture_list[0]
        scripture = jw_common.removeHtml(scripture)    

        return scripture.encode("utf8") 

    # Grep comment 
    def getComment(self, text):

        regexp_full_comment = "'sb'>(.*)"
        full_comment_list = re.findall(regexp_full_comment, text)
        if full_comment_list == []:
            return ""

        full_comment = full_comment_list[0]
        full_comment = jw_common.removeHtml(full_comment)

        return  full_comment.encode("utf8")