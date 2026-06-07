from resources.lib.deutschlandfunk.deutschlandfunkaddon import DeutschlandfunkAddon

import sys

if __name__ == '__main__':

    deutschlandfunkAddon = DeutschlandfunkAddon(int(sys.argv[1]))
    deutschlandfunkAddon.handle(sys.argv)
