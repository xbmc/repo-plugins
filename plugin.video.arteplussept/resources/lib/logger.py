"""Utilities to write log files with api traces"""

from os.path import join as OSPJoin
from datetime import datetime
# pylint: disable=import-error
from xbmcswift2 import Plugin
# pylint: disable=import-error
from xbmcswift2 import xbmcvfs
from . import settings

def log_json(reply, log_suffix):
    """save request and response in reply into a file
    with file name containing log_suffix in addon user data
    if loglevel settings is set to API.
    :param reply Python requests library object with every information to log
    :param log_suffix string to be used in log file name along current date and time
    """
    plugin = Plugin()
    msettings = settings.Settings(plugin)
    if (not reply or msettings.loglevel != settings.loglevel[1]):
        return

    base_path = plugin.storage_path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
    log_path = OSPJoin(base_path, f"{timestamp}_{log_suffix}.json")
    reqhdrs = format_headers(reply.request.headers)
    reshdrs = format_headers(reply.headers)
    with xbmcvfs.File(log_path, 'w') as log_file:
        log_file.write("---------------- request ----------------\n")
        log_file.write(f"{reply.request.method} {reply.request.url}\n")
        log_file.write(f"{reqhdrs}\n")
        log_file.write(f"payload : {reply.request.body}\n")
        log_file.write("---------------- response ----------------\n")
        log_file.write(f"{reply.status_code} {reply.reason} {reply.url}\n")
        log_file.write(f"{reshdrs}\n")
        log_file.write(f"payload : {reply.text}")

def format_headers (headers):
    """Map headers into a readable string to be logged"""
    return '\n'.join(f'{k}: {v}' for k, v in headers.items())
