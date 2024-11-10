from bossanova808 import exception_logger
from resources.lib import switchback_service

if __name__ == "__main__":
    with exception_logger.log_exception():
        switchback_service.run()
