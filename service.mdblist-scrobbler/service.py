import xbmc

from resources.lib.main_monitor import MainMonitor


def main():
    monitor = MainMonitor()

    xbmc.log("Starting MDBList Scrobbler", level=xbmc.LOGINFO)

    monitor.waitForAbort()
    monitor.shutdown()

    xbmc.log("Stopping MDBList Scrobbler", level=xbmc.LOGINFO)


if __name__ == '__main__':
    main()
