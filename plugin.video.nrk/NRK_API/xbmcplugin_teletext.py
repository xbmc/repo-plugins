#
#
#   NRK plugin for XBMC Media center
#
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

import image
import os, sys
import sgmllib,urllib
import connection_manager
from image import ImageRGB
from shutil import rmtree, copytree
from utils import Plugin, Key, Log, PluginError

try: 
    import xbmc, xbmcgui
except: 
    DEBUG = 1
else: 
    DEBUG = 0
    
try:
    __plugin__ = sys.modules["__main__"].__plugin__
except:
    __plugin__ = 'DEBUG MODE'
    
__date__ = '24-07-2009'

Log.out( "Module: %s Dated: %s loaded!" % ( __name__, __date__ ) )


#Color Palette for teletext
pal = ( 
        (  0,   0,   0,   0),  (191,  56,   8), 
        (152, 199,  30     ),  (255, 204,   4),
        (  5,  86, 133     ),  (255,   0, 255),
        (167, 219, 231     ),  (255, 255, 255),
        (  0, 255, 255     )  
    )


#Bitmap fonts in hexadecimal strings    
chr = {
        0xA: '0000000000000202022242FE40200000',
        0x20:'00000000000000000000000000000000',
        0x21:'00000000080808080808080008080000',
        0x22:'00002222222200000000000000000000',
        0x23:'000000001212127E24247E4848480000',
        0x24:'00000000083E4948380E09493E080000',
        0x25:'00000000314A4A340808162929460000',
        0x26:'000000001C2222221C39454246390000',
        0x27:'00000808080800000000000000000000',
        0x28:'00000004080810101010101008080400',
        0x29:'00000020101008080808080810102000',
        0x2A:'00000000000008492A1C2A4908000000',
        0x2B:'0000000000000808087F080808000000',
        0x2C:'00000000000000000000000018080810',
        0x2D:'0000000000000000007E000000000000',
        0x2E:'00000000000000000000000018180000',
        0x2F:'00000000020204080810102040400000',
        0x30:'00000000182442424242424224180000',
        0x31:'000000000818280808080808083E0000',
        0x32:'000000003C4242020C102040407E0000',
        0x33:'000000003C4242021C020242423C0000',
        0x34:'00000000040C142444447E0404040000',
        0x35:'000000007E4040407C020202423C0000',
        0x36:'000000001C2040407C424242423C0000',
        0x37:'000000007E0202040404080808080000',
        0x38:'000000003C4242423C424242423C0000',
        0x39:'000000003C4242423E02020204380000',
        0x3A:'00000000000018180000001818000000',
        0x3B:'00000000000018180000001808081000',
        0x3C:'00000000000204081020100804020000',
        0x3D:'000000000000007E0000007E00000000',
        0x3E:'00000000004020100804081020400000',
        0x3F:'000000003C4242020408080008080000',
        0x40:'000000001C224A565252524E201E0000',
        0x41:'0000000018242442427E424242420000',
        0x42:'000000007C4242427C424242427C0000',
        0x43:'000000003C42424040404042423C0000',
        0x44:'00000000784442424242424244780000',
        0x45:'000000007E4040407C404040407E0000',
        0x46:'000000007E4040407C40404040400000',
        0x47:'000000003C424240404E4242463A0000',
        0x48:'00000000424242427E42424242420000',
        0x49:'000000003E08080808080808083E0000',
        0x4A:'000000001F0404040404044444380000',
        0x4B:'00000000424448506060504844420000',
        0x4C:'000000004040404040404040407E0000',
        0x4D:'00000000424266665A5A424242420000',
        0x4E:'0000000042626252524A4A4646420000',
        0x4F:'000000003C42424242424242423C0000',
        0x50:'000000007C4242427C40404040400000',
        0x51:'000000003C4242424242425A663C0300',
        0x52:'000000007C4242427C48444442420000',
        0x53:'000000003C424240300C0242423C0000',
        0x54:'000000007F0808080808080808080000',
        0x55:'000000004242424242424242423C0000',
        0x56:'00000000414141222222141408080000',
        0x57:'00000000424242425A5A666642420000',
        0x58:'00000000424224241818242442420000',
        0x59:'00000000414122221408080808080000',
        0x5A:'000000007E02020408102040407E0000',
        0x5B:'0000000E080808080808080808080E00',
        0x5C:'00000000404020101008080402020000',
        0x5D:'00000070101010101010101010107000',
        0x5E:'00001824420000000000000000000000',
        0x5F:'00000000000000000000000000007F00',
        0x60:'00201008000000000000000000000000',
        0x61:'0000000000003C42023E4242463A0000',
        0x62:'0000004040405C6242424242625C0000',
        0x63:'0000000000003C4240404040423C0000',
        0x64:'0000000202023A4642424242463A0000',
        0x65:'0000000000003C42427E4040423C0000',
        0x66:'0000000C1010107C1010101010100000',
        0x67:'0000000000023A44444438203C42423C',
        0x68:'0000004040405C624242424242420000',
        0x69:'000000080800180808080808083E0000',
        0x6A:'0000000404000C040404040404044830',
        0x6B:'00000000404044485060504844420000',
        0x6C:'000000001808080808080808083E0000',
        0x6D:'00000000000076494949494949490000',
        0x6E:'0000000000005C624242424242420000',
        0x6F:'0000000000003C4242424242423C0000',
        0x70:'0000000000005C6242424242625C4040',
        0x71:'0000000000003A4642424242463A0202',
        0x72:'0000000000005C624240404040400000',
        0x73:'0000000000003C4240300C02423C0000',
        0x74:'0000000010107C1010101010100C0000',
        0x75:'000000000000424242424242463A0000',
        0x76:'00000000000042424224242418180000',
        0x77:'00000000000041494949494949360000',
        0x78:'00000000000042422418182442420000',
        0x79:'0000000000004242424242261A02023C',
        0x7A:'0000000000007E0204081020407E0000',
        0x7B:'0000000C101008081010080810100C00',
        0x7C:'00000808080808080808080808080808',
        0x7D:'00000030080810100808101008083000',
        0x7E:'00000031494600000000000000000000',
        
        
        # Norwegian characters
        0xE6:'0000000000007689095F888889760000',
        0xF8:'0000000000003D464A4A525262BC0000',
        0xE5:'0000000018003C42023A4642463D0000',
        0xC6:'000000000E182848487E4848484E0000',
        0xD8:'000000003D464A4A4A52525262BC0000',
        0xC5:'000000003C18244242427E4242420000'
    }


def binary(n):
   digits = { '0': '000', '1': '001', '2': '010', '3': '011',
              '4': '100', '5': '101', '6': '110', '7': '111'}
   octStr = "%o" % n
   binStr = ''
   for c in octStr: binStr += digits[c]
   return binStr

   
def str2int(s): 
    return sum( [ord(c) * 256 ** i for i, c in enumerate( s[::-1] )] )

    
NONE = -1;  ROOT = 0;  HEAD = 1
TTVH =  2;  MAIN = 3;  GTBL = 4
ANCR =  5;  READ = 6;  LEAD = 7;
TRANSPARENT = 0
Y = 0
X = 1 


class GfxChar:

    def __init__(self):
        self.color = [0,0,0,0,0,0]
        self.point = [0,0,0,0,0,0]
        self.primary_color = 0
        self.count = 0
        
    def append(self, color, point):
        self.color[self.count] = color
        self.point[self.count] = point
        if point == 1: self.primary_color = color
        self.count += 1
    
    def hex_font(self):
        rref = pref = fprt = 0
        fontstr = []
        for p in self.point:
            if p == 1: val = 'F'
            else: val = '0'
            if rref == 1: 
                if fprt == 2:
                    m =6
                else: m = 5
                fontstr.append( (pref + val) * m )
                rref = pref = 0
                fprt += 1
            else: 
                pref = val
                rref = 1
            
        fontstr = ''.join(fontstr)
        return fontstr, self.primary_color, 0, None
    
    def binary(self):
        hexstr, fgc, bgc, chr = self.hex_font()
        f2 = lambda s, l=[]: (l.extend(s), l.reverse(), ''.join(l))[2]
        a = hexstr.decode('hex')
        d = binary(str2int(a))
        bin = f2(d)
        return bin, fgc, bgc, chr
            
   
   
class GfxPack:
    def __init__(self, size):
        self.chars = []
        self.size = size
        self.counter = self.cref = 0
        for i in range(self.size):
            self.chars.append( GfxChar() )
    
    def feedline(self):
        self.counter = self.cref = 0
    
    def hex_fonts(self):
        fonts = []
        for c in self.chars:
            f = c.hex_font()
            fonts.append(f)
        return fonts
    
    def bin_fonts(self):
        fonts = []
        for c in self.chars:
            f = c.binary()
            fonts.append(f)
        return fonts
        
    def plot(self, color): 
        if color != 0: 
            point = 1  
        else: 
            point = 0 
        self.chars[self.cref].append(color, point)
        if self.counter % 2 == 1: 
            self.cref += 1 
        self.counter += 1
    
    def close(self):
        del self.size
        del self.cref
        del self.counter
            
    def read(self):
        return self.bin_fonts()
        
 
class Cell:
    #const
    TXT = 0
    GFX = 1
    REF = 2
    
    def __init__(self):
        #common vars
        self.id      = 0
        self.data    = ''
        self.chars   = []
        self.dtype   = 0
        self.fcolor  = 0
        self.bcolor  = 0
        self.colspan = 1
        self.anchors = []
        
    
    def add(self, data):
        #Replaceeventualy unwated characters
        self.data += data.replace('\n', '')
 
 
    def close(self):
        #Fill in the empty space made by the colspans
        self.data += ' ' * (self.colspan - len(self.data))
           
           
    def create_gfx_pack(self):
        self.gfx   = GfxPack(self.colspan)
        self.dtype = self.GFX
        
    
    def read(self):
        if self.dtype == self.GFX: 
            return self.gfx.read()
        else: 
            for i in range( len(self.data) ):
                f2 = lambda s, l=[]: (l.extend(s), l.reverse(), ''.join(l))[2]
                a = ord(self.data[i])
                if a in chr:
                    c = chr[a].decode('hex')
                    d = binary( str2int(c) ) 
                    bin = f2(d)
                    self.chars.append( ( bin, self.fcolor, 
                                         self.bcolor, self.data[i] ) )
            return self.chars
 
        
class Row:

    def __init__(self):
        self.id = 0
        self.cells = []
        
    def to_string(self, lineno=None, out=''):
        if lineno: out += '[%02d]' % self.id
        for cell in self.cells:
            if cell.dtype == Cell.GFX: 
                strout = ''
            else: 
                strout = cell.data
            out += strout
        return out
        
    def read(self):
        chars = []
        for cell in self.cells:
            for char in cell.read():
                chars.append(char)
        return chars

            

    
        
class TTVParser(sgmllib.SGMLParser):

    def parse(self, s):
        self.feed(s)
        self.close()
        
        
    def __init__(self, verbose=0):
        sgmllib.SGMLParser.__init__(self, verbose)
        self.grc = 0
        self.gcc = 0
        self.lcc = 0
        self.state    = NONE
        self.table    = []
        self.anchor   = {}
        self.metadata = {}
        
        self.reset_row()
        self.reset_cell() 
 
        self.metadata['subpages'] = 0
        self.metadata['substat']  = 'none'
        
        
    def reset_row(self):
        self.row = Row()
        self.idx = 0
        
    def reset_cell(self):
        self.cell = Cell()
        
        
    def start_a(self, attributes):
        if self.state == MAIN:
            self.state = ANCR
            for a, val in attributes:
                if a == 'href':
                    self.anchor['href'] = val
                    
                    
    def end_a(self):
        if self.state == ANCR:
            self.cell.anchors.append(self.anchor)
            self.anchor = {}
            self.state  = MAIN
        
        
    def start_td(self, attributes):
        if self.state == MAIN: 
            for name, value in attributes:
                if name == 'colspan':
                    self.cell.colspan = int(value)
                elif name == "class":
                    if value[0] == 't' and len(value) == 3:
                        self.cell.bcolor = int(value[-1])
                        self.cell.fcolor = int(value[-2])
            self.cell.id = self.idx
            self.idx += self.cell.colspan

            
        elif self.state == GTBL:
            for name, value in attributes:
                if name == "class":
                    color = int(value[-1])
                    self.cell.gfx.plot(color)
                    
            
    def end_td(self):
        if self.state == MAIN:
            self.cell.close()
            self.row.cells.append(self.cell)
            self.cell = Cell()
            
            
    def start_tr(self, attributes):

        if self.state == ROOT:
            self.state = HEAD
        elif self.state == HEAD:
            self.state = TTVH
        elif self.state == TTVH:
            self.state = MAIN
        
        if self.state == MAIN:
            for name, value in attributes:
                if name == 'id':
                    self.row.id = int(value)

      
    def end_tr(self):
        if self.state == MAIN:
            self.table.append(self.row)
            self.reset_row()
            
        elif self.state == GTBL:
            self.cell.gfx.feedline()
        
        elif self.state == READ:
            self.state = TTVH
         
         
    def start_table(self, attributes):
        for a,v in attributes:
            if a == 'class':
                if v == 'ttv':
                    self.state = ROOT
                    
        if self.state == MAIN:
            self.state = GTBL
            self.cell.create_gfx_pack()
      
      
    def end_table(self):
        if self.state == GTBL:
            self.state = MAIN
        else:
            self.state = NONE

            
    def start_font(self, attributes):
        if self.state == TTVH:
            self.state = LEAD
            self.hcount = 0
        elif ( self.state == LEAD ) or ( self.state == READ ):
            self.state = READ
            

            
    def handle_data(self, data):
        if self.state == MAIN or self.state == ANCR:
            self.cell.add(data)
            
        elif self.state == LEAD:
        
            if self.hcount == 0:
                self.metadata['page']    = int( data[0:-2] )
                self.metadata['subpage'] = int( data[-1] )
                
            elif self.hcount == 1:
                self.metadata['channel'] = data
                
            elif self.hcount == 2:
                self.metadata['date']    = data
                
            self.hcount += 1
            
        elif self.state == READ:
            
            try:
                sub = int(data)
            except:
                if data == '>':
                    self.metadata['substat'] = 'more'
                elif data == '<':
                    self.metadata['substat'] = 'less'
            else:
                self.metadata['subpages'] = int(data)
                
                
        elif self.state == ANCR:
            self.anchor['title'] = data
    
 


class TTV:
    
    w    =   8; h    = 14
    cols =  39; rows = 24
    sub  =  1
    subs =   1
    bg_alpha = 200
    
    header = 'NRK Tekst tv laster..'
    
    
    def __init__(self, cache=False, page=100):
        self.conn = connection_manager.DataHandle()
        self.savepath = os.path.join(os.getcwd(), 'ttv_images')
        self.status = 900
        self.cache = cache
        self.page = page
        
        
    def get_url(self):
        tpl = ( 'http://www2.nrk.no/teksttv/'
                'index.asp?channel=1&page=%d&subpage=%d' )
                
        url = tpl % ( self.page, self.sub )
        if DEBUG: 
            Log.out('nrk ttv url: %s' % url)
        return url
        
        
    def get_savefile(self):
        return os.path.join(
                    self.savepath, 
                    'ttv_p%dsp_%d.png' % ( self.page, self.sub )
                )
        
        
    def page_up(self):
        return self.get_page(self.page + 1)
        
        
    def page_down(self):
        return self.get_page(self.page - 1)
        
        
    def next_page(self):
        return self.get_subpage(self.sub + 1)
    
    
    def has_next(self):
        if self.sub < self.subs: 
            return True
        
        
    def prev_page(self):
        return self.get_subpage(self.sub - 1)
    
    
    def has_prev(self):
        if self.sub > 1: 
            return True
        
        
    def get_subpage(self, subpage):
        return self.get_page(self.page, subpage)
        
        
    def get_page(self, page=100, sub=1):
        
        if (page < 100 or page > 999) or (sub < 1 or sub > 99):
            self.status = 901
            return
        
        self.status = 900    
        self.page   = page
        self.sub    = sub
        savefile    = self.get_savefile()
        
        if connection_manager.Cache.has_cache(savefile, 10) and self.cache:
            return savefile
            
        url  = self.get_url()
        data = self.conn.get_data(url)
            
        self.parse(data)
        
        if len(self.parser.table) == 0:
            self.status = 904
            return
            
        ch  = self.channel = self.parser.metadata['channel']  or 'NRK1'
        sps = self.subs    = self.parser.metadata['subpages'] or 1
        sp  = self.sub     = self.parser.metadata['subpage']  or 1
        dt  = self.date    = self.parser.metadata['date']
        pg  = self.page    = self.parser.metadata['page']

        subp = '(%02d/%02d' % ( sp, sps )
        
        if self.parser.metadata['substat'] == 'more': 
            subp += '+)'
        else: 
            subp += ') '
            
        cnt = self.cols - (len(ch) + len(dt) + 5) - (len(subp) + 4)
        head = ' %s    %s%s%s %s ' % (ch, dt, ' '*cnt , str(pg), subp)
        cell = Cell()
        cell.fcolor = 0
        cell.bcolor = 7
        cell.add( head )
      
      
        w = self.w * self.cols
        h = self.h * self.rows
        self.img = ImageRGB( w, h, True, pal[0] )
        
        self.paintHexFonts( 0, cell.read(), 1 )
        
        for row in self.parser.table:   
            self.paintHexFonts( row.id + 1, row.read() )
            
        return self.save()
        
        
    def parse(self, data):
        self.parser = TTVParser()
        self.parser.parse(data)
   
   
    def create_background(self):
        file = os.path.join( self.savepath, 'bg_%d.png' % ( self.bg_alpha ) )
        print 'background file: %s' % file
        if connection_manager.Cache.has_cache(file):
            print 'use cached background'
            return file
            
        w = self.w * self.cols
        h = self.h * self.rows
        r, g, b, NA = pal[0]
        a = self.bg_alpha
        rgba = ( r, g, b, a)
        img = ImageRGB( w, h, True, rgba )
        
        import png
        
        bg = image.BLACK 
        bd = 8
            
        if os.path.isdir(os.path.dirname(file)) == False:
            os.makedirs(os.path.dirname(file))
        
        fh  = open(file, 'wb')
        save_img = png.Writer(w, h, alpha=True, bitdepth=bd, background=bg)
        save_img.write_array(fh, img.array)
        fh.close()
        
        del img
        
        return file
        
        
    def paintHexFonts(self, y, fonts, offset=2):
        
        r = self.rows - offset
        
        #Set characters width and height and set x/y-position
        w = self.w
        h = self.h
        y = y * h + h
        x = 0
           
        for f in fonts:
            
            #Unpack fonts values
            fnt, fgc, bgc, chr = f
            fgc, bgc = pal[fgc], pal[bgc]
            
            #Don't plot background if its 
            #"transparent" (black) to increase speed
            if bgc == (0, 0, 0): 
                bgc = None
            
            #Set local loop references and plot background
            lx = x; ly = y
            if bgc:
                for k in range( w * h ):
                    if k % w == 0:
                        ly -= 1
                        lx  = x
                    self.img.plot(lx, ly, bgc)
                    lx -= 1
            
            #Reset local loop references and plot text
            lx = x
            ly = y
            for j in range( len(fnt) ):
                if j % w == 0:
                    ly -= 1
                    lx  = x
                if int(fnt[j]):
                    self.img.plot( lx, ly, fgc )
                lx -= 1
            
            #Set x-axis reference for next character
            x += w
            

        
    def save(self):   
        import png
        
        w = self.img.wd 
        h = self.img.ht
        bg = image.BLACK 
        bd = 8
        file = self.get_savefile()
        
        if self.status > 900:
            return
            
        if os.path.isdir(os.path.dirname(file)) == False:
            os.makedirs(os.path.dirname(file))
        
        print 'Save image to file %s' % file
        
        fh  = open(file, 'wb')
        img = png.Writer(w, h, alpha=True, bitdepth=bd, background=bg)
        img.write_array(fh, self.img.array)
        fh.close()
        
        del self.img
        
        return file

   

# Action Identificator constants
REMOTE_0 = 58;   REMOTE_1 = 59
REMOTE_2 = 60;   REMOTE_3 = 61
REMOTE_4 = 62;   REMOTE_5 = 63
REMOTE_6 = 64;   REMOTE_7 = 65
REMOTE_8 = 66;   REMOTE_9 = 67

EXIT_CODES = (9, 10, 216, 257, 275, 216, )

LOADING_IMG = Plugin.image('ttv_loading.png')
ERROR_IMG   = Plugin.image('ttv_notfound.png')


xbmc.executebuiltin("Skin.SetString(ttv-image, %s)" % LOADING_IMG )

        
if not DEBUG:
    class TTVDlg(xbmcgui.WindowXMLDialog):
        """ Show skinned Dialog with our information """
        
        XML = "teletext.xml"

        
        def __init__( self, *args, **kwargs):
            if Key(sys.argv[2]).page: page = key.page
            else: page = 100
                
            self.action = None
            self.buttons = {}
            self.ttv = TTV(cache=True)
            self.ttv.page = page
            self.ttv.savepath = Plugin.get_cachepath()
            
            bg = self.ttv.create_background()
            xbmc.executebuiltin("Skin.SetString(bgimg, %s)" %bg)      

            self.image = LOADING_IMG
            self.pref = ''
            
            
        def onInit(self):
            self.image = self.ttv.get_page(page = self.ttv.page)
            self.rebuild()
                
                
        def onClick(self, controlId):
            if controlId in (20, 21, 22, 23):
                self.image = LOADING_IMG
                self.rebuild()
                if controlId == 20: self.image = self.ttv.page_up()
                elif controlId == 21: self.image = self.ttv.page_down()
                elif controlId == 23: self.image = self.ttv.next_page()
                elif controlId == 22: self.image = self.ttv.prev_page()
                
                self.update_pageno(self.ttv.page)
                self.rebuild()
                
            elif controlId in range(500,511):
                self.update_pageno(  str( controlId - 500 ) )
                    
            else:
                print controlId

                
        def onFocus(self, controlId):
            pass
            

        def onAction(self, action):
            try:
                buttonCode =  action.getButtonCode()
                actionID   =  action.getId()
            except: 
                return

            if actionID == REMOTE_0: no = '0'
            elif actionID == REMOTE_1: no = '1'
            elif actionID == REMOTE_2: no = '2'
            elif actionID == REMOTE_3: no = '3'
            elif actionID == REMOTE_4: no = '4'
            elif actionID == REMOTE_5: no = '5'
            elif actionID == REMOTE_6: no = '6'
            elif actionID == REMOTE_7: no = '7'
            elif actionID == REMOTE_8: no = '8'
            elif actionID == REMOTE_9: no = '9'

            if actionID >= REMOTE_0 and actionID <= REMOTE_9:
                self.update_pageno( no )
                
                
            if (actionID in EXIT_CODES or buttonCode in EXIT_CODES):
                self.close()
            
                

        def rebuild(self):
            if not self.image:
                if self.ttv.status == 904:
                    self.image = ERROR_IMG
            xbmc.executebuiltin("Skin.SetString(ttv-image, %s)" % self.image)
            xbmc.executebuiltin("Skin.SetString(ttv-page, %s)" % self.ttv.page)
            
            
        def update_pageno(self, no):
            if len(self.pref) == 3:
                self.pref = ''

            no = str( no )
            
            if no == '0':
                if len( self.pref ) == 0:
                    return
                
            self.pref += str( no )
            self.set_pageno_label()

            if len(self.pref) == 3:
                self.image = LOADING_IMG
                self.rebuild()

                self.image = self.ttv.get_page( int(self.pref) )
                self.rebuild()


        def set_pageno_label(self):
            txt = self.pref + '-'*(3 - len(self.pref))
            xbmc.executebuiltin("Skin.SetString(ttv-page, %s)" % txt)
            
        
        def open(self):
            self.doModal()
        


if not DEBUG:
    def Main():
        ttv = TTVDlg( TTVDlg.XML, os.getcwd(), "Default" ).open()    
        del ttv


                    
if __name__ == "__main__":
    
    ttv = TTV()
    try:
        pageno = int( sys.argv[1] )
    except: 
        pageno = 100
        
    print ttv.get_page(pageno)
        
        
        
        