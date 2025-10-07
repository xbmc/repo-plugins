from bossanova808 import exception_logger
from resources.lib import switchback_plugin


if __name__ == "__main__":
    with exception_logger.log_exception():
        switchback_plugin.run()
