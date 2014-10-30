from resources.lib import kodimon
from resources.lib import soundcloud

__provider__ = soundcloud.Provider()
kodimon.run(__provider__)