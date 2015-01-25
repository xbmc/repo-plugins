from resources.lib.kodion import runner, debug
from resources.lib import prosiebensat1

__provider__ = prosiebensat1.Provider()
runner.run(__provider__)