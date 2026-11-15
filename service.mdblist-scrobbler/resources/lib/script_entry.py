import sys

import xbmc
import xbmcgui


def run():
    try:
        if "sync_now" in sys.argv:
            # Kodi runs RunScript in its own Python process, separate from the
            # long-running service (service.py) -- calling sync_orchestrator.run()
            # directly here would use a *different* module-level lock than the
            # service's, so its is_running() check could never see this sync in
            # progress (confirmed bug). Broadcast instead, so the running service
            # picks this up and runs it in its own process/lock domain, same as
            # the periodic timers and the live listener.
            xbmc.executebuiltin("NotifyAll(service.mdblist-scrobbler,sync_now)")
        else:
            from resources.lib import oauth

            if "disconnect" in sys.argv:
                oauth.run_disconnect()
            else:
                oauth.run_connect_flow()
    except Exception as e:
        xbmc.log("MDBList Scrobbler: script error - {}".format(e), level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification("MDBList Scrobbler", "Error: {}".format(str(e)[:80]), xbmcgui.NOTIFICATION_ERROR, 4000)
