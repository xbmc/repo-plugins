from ampache_monitor import AmpacheMonitor
from art_clean import clean_cache_art, clean_settings

clean_settings()
clean_cache_art()
AmpacheMonitor().run()
