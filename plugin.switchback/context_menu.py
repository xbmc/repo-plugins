import sys

from bossanova808 import exception_logger
from resources.lib import switchback_context_menu

if __name__ == "__main__":
    with exception_logger.log_exception():
        # args would be passed through, if there were any...
        # <itemlibrary = "context_menu.py" args="something">
        switchback_context_menu.run(sys.argv[1:])
