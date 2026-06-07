from resources.lib.ampache_monitor import AmpacheMonitor
from resources.lib.art_clean import init_cache, clean_settings, remove_expired

def Main():
    clean_settings()
    init_cache()
    remove_expired()
    AmpacheMonitor().run()
