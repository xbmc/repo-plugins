from resources.lib.kodion import runner
from resources.lib import break_api

__provider__ = break_api.Provider()
runner.run(__provider__)