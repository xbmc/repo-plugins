from resources.lib.ardaktuell.ardaktuelladdon import ArdAktuellAddon
import sys

__PLUGIN_ID__ = "plugin.video.ardaktuell"

if __name__ == '__main__':

    ardAktuellAddon = ArdAktuellAddon(int(sys.argv[1]))
    ardAktuellAddon.handle(sys.argv)
