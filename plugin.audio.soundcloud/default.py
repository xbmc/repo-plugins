from resources.lib.kodion import runner
from resources.lib import soundcloud

__provider__ = soundcloud.Provider()
runner.run(__provider__)