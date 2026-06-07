from resources.lib.ardaktuell.ardaktuelladdon import ArdAktuellAddon
import sys

if __name__ == '__main__':

    ardAktuellAddon = ArdAktuellAddon(int(sys.argv[1]))
    ardAktuellAddon.handle(sys.argv)
