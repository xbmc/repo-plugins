import sys
from xbmcplugin import setContent

from lib.sections import router
	
setContent(int(sys.argv[1]), 'videos')

router(sys.argv)