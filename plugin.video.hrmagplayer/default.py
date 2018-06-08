# -*- coding: utf-8 -*-
import sys
from libplayer.player import *

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    dispatch(sys.argv[0], sys.argv[1], sys.argv[2])
