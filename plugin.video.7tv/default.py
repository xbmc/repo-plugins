from resources.lib import kodimon
from resources.lib import prosiebensat1

__provider__ = prosiebensat1.Provider()
kodimon.run(__provider__)