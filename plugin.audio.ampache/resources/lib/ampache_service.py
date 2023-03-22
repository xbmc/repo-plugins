from resources.lib.ampache_monitor import AmpacheMonitor
from resources.lib.art_clean import clean_cache_art, clean_settings

def Main():
    clean_settings()
    clean_cache_art()
    AmpacheMonitor().run()
