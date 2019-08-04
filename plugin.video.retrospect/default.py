#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import os.path
import sys

import xbmc


def run_plugin():
    """ Runs Retrospect as a Video Add-On """

    log_file = None

    try:
        from retroconfig import Config
        from helpers.sessionhelper import SessionHelper

        # get a logger up and running
        from logger import Logger

        # only append if there are no active sessions
        if not SessionHelper.is_session_active():
            # first call in the session, so do not append the log
            append_log_file = False
        else:
            append_log_file = True

        log_file = Logger.create_logger(os.path.join(Config.profileDir, Config.logFileNameAddon),
                                        Config.appName,
                                        append=append_log_file,
                                        dual_logger=lambda x, y=4: xbmc.log(x, y))

        from urihandler import UriHandler

        from addonsettings import AddonSettings
        AddonSettings.set_language()

        from textures import TextureHandler

        # update the loglevel
        Logger.instance().minLogLevel = AddonSettings.get_log_level()

        use_caching = AddonSettings.cache_http_responses()
        cache_dir = None
        if use_caching:
            cache_dir = Config.cacheDir

        ignore_ssl_errors = AddonSettings.ignore_ssl_errors()
        UriHandler.create_uri_handler(cache_dir=cache_dir,
                                      cookie_jar=os.path.join(Config.profileDir, "cookiejar.dat"),
                                      ignore_ssl_errors=ignore_ssl_errors)

        # start texture handler
        TextureHandler.set_texture_handler(Config, Logger.instance(), UriHandler.instance())

        # run the plugin
        import plugin
        plugin.Plugin(sys.argv[0], sys.argv[2], sys.argv[1])

        # make sure we leave no references behind
        AddonSettings.clear_cached_addon_settings_object()
        # close the log to prevent locking on next call
        Logger.instance().close_log()
        log_file = None

    except:
        if log_file:
            log_file.critical("Error running plugin", exc_info=True)
            log_file.close_log()
        raise


# setup the paths in Python
from initializer import Initializer  # nopep8
Initializer.set_unicode()
currentPath = Initializer.setup_python_paths()

# ANY OF THESE SETTINGS SHOULD ONLY BE ENABLED FOR DEBUGGING PURPOSES
# from debug import remotedebugger
# debugger = remotedebugger.RemoteDebugger()

# Debugging with profiler
# import profile as cProfile
# import cProfile
# from debug import profilelinebyline as cProfile

# Path for PC
# statsPath = os.path.abspath(os.path.join(currentPath, "../DEV/retrospect.pc.leia.pstat"))
# Path for ATV
# statsPath = os.path.abspath("/private/var/mobile/retrospect.atv.pstat")
# Path for rPi
# statsPath = os.path.abspath("/home/pi/.kodi/addons/plugin.video.retrospect/retrospect.rpi.pstat")

# Profiled run
# cProfile.runctx("run_plugin()", globals(), locals(), statsPath)
# Normal run
run_plugin()
