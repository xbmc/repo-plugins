__version__ = "0.1"
print "image module, version %s - Victor Vikene" % __version__ 

DEBUG = 1

ALPHA_MAX = 255
ALPHA_MIN = 0

# common colors
BLACK    = (   0,   0,   0 )
RED      = ( 255,   0,   0 )
GREEN    = (   0, 255,   0 )
BLUE     = (   0,   0, 255 )
CYAN     = (   0, 255, 255 )
MAGENTA  = ( 255,   0, 255 )
YELLOW   = ( 255, 255,   0 )
WHITE    = ( 255, 255, 255 )
DKRED    = ( 128,   0,   0 )
DKGREEN  = (   0, 128,   0 )
DKBLUE   = (   0,   0, 128 )
TEAL     = (   0, 128, 128 )
PURPLE   = ( 128,   0, 128 )
BROWN    = ( 128, 128,   0 )
GRAY     = ( 128, 128, 128 )


class ImageRGB(object):
  
  def __init__( self, width, height, alpha=False, bgc=BLACK, fgc=WHITE ):
  
    self.wd = int( width )
    self.ht = int( height ) 
    self.alpha = alpha
    
    if DEBUG:
        print 'image width: %d height: %d' % ( self.wd, self.ht)
    
    if len(bgc) == 3 and self.alpha == True:
        bgc = self.rgb_rgba(bgc)
    self.bgc = bgc
    
    if len(fgc) == 3 and self.alpha == True:
        fgc = self.rgb_rgba(fgc)
    self.pen = fgc
    
    self.penlen = len(self.pen)
    self.array = list(self.bgc) * (self.wd * self.ht)

    
  def rgb_rgba( self, rgb):
    r, g, b = rgb
    return r, g, b, ALPHA_MAX
    
    
  def setColor( self, pc ):
    if len(pc) == 3 and self.alpha == True:
        pc = self.rgb_rgba(pc)
    self.pen = pc

    
  def getColor( self ):
    return self.pen
 
 
  def plot( self, x, y, pc=None ):
    
    if pc: 
        if len(pc) == 3 and self.alpha == True:
            pc = self.rgb_rgba(pc)
        pen = pc
    else: 
        pen = self.pen
        
    x = int(x); y = int(y)
    h = self.ht; w = self.wd
    p = self.penlen
    
    z = (w * p * y) + (x  * p)

    if 0 <= z < (w * p * h):
        self.array[z:z+p] = pen
    else: pass


        
        
        
# Testruns
if __name__ == "__main__":
  
  test = 1
  if test == 1:
    img = ImageRGB( 4, 4 )
    img.plot(0,0)
    img.plot(1,0)
    img.plot(2,1)
    img.plot(3,1)
    print img.array[:12]
    print img.array[12:24]
    print img.array[24:36]
    print img.array[36:48]
    print len(img.array)
