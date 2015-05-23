from resources.lib.kodion import runner
from resources.lib import nowtv

__provider__ = nowtv.Provider()
runner.run(__provider__)