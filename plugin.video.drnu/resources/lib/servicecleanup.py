#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Background maintenance of the requests-cache sqlite database.

Used by service.py to expire old responses and VACUUM the cache while Kodi
is running, independent of addon invocations. Deliberately free of Kodi
imports (settings are injected) so the logic is unit-testable without the
Kodi stub modules.

The marker file and cache file names mirror Api.init_sqlite_db() in tvapi:
the service rewrites 'requests_cleaned' after a cleanup so the addon skips
its own cleanup pass, and it refuses to touch a database without a marker
file, since that state means the addon will wipe and rebuild the cache.

The service's own due-check uses a separate 'cache_vacuumed' marker. The
daily re-cache crawl refreshes 'requests_cleaned' (it deletes expired
responses too), so gating the VACUUM on that same marker would postpone it
forever.
"""
import gc
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

import requests_cache

MARKER_FILE = 'requests_cleaned'
VACUUM_MARKER_FILE = 'cache_vacuumed'
CACHE_PREFIX = 'requests.cache'
DB_FILE = CACHE_PREFIX + '.sqlite'


def cache_db_path(cache_path: Path) -> Path:
    return cache_path / DB_FILE


def cleanup_due(cache_path: Path, cleanup_every: int, now: Optional[float] = None) -> bool:
    """True when the last VACUUM marker is missing or older than cleanup_every days.

    Keyed on the vacuum marker, not requests_cleaned: the daily re-cache
    refreshes the latter and would otherwise keep postponing the VACUUM.
    """
    marker = cache_path / VACUUM_MARKER_FILE
    if not marker.exists():
        return True
    if now is None:
        now = time.time()
    age_days = (now - marker.stat().st_mtime) / 3600 / 24
    return age_days >= cleanup_every


def vacuum_db(db: Path, log_func: Optional[Callable] = None) -> bool:
    """VACUUM the sqlite db so deleted rows actually release disk space."""
    if not db.exists():
        return False
    try:
        con = sqlite3.connect(str(db), timeout=30)
        try:
            con.isolation_level = None
            con.execute('VACUUM')
        finally:
            con.close()
        return True
    except sqlite3.Error as e:
        if log_func:
            log_func(f'drnu service: VACUUM failed on {db}: {e}')
        return False


def cleanup_cache(cache_path: Path, expire_hours: int, log_func: Optional[Callable] = None) -> bool:
    """Delete expired responses and VACUUM the cache db.

    Returns True when the cleanup ran and the marker file was refreshed.
    Never raises: failures are logged and reported as False so the service
    loop simply retries on its next pass.
    """
    db = cache_db_path(cache_path)
    marker = cache_path / MARKER_FILE
    if not db.exists() or not marker.exists():
        # no cache yet, or a cache the addon will wipe on next start
        return False

    try:
        session = requests_cache.CachedSession(str(cache_path / CACHE_PREFIX), backend='sqlite')
        try:
            if expire_hours >= 0:
                cutoff = datetime.utcnow() - timedelta(hours=expire_hours)
                session.cache.remove_old_entries(cutoff)
        finally:
            session.close()
            del session
            gc.collect()
    except Exception as e:
        if log_func:
            log_func(f'drnu service: cache cleanup failed: {e}')
        return False

    if not vacuum_db(db, log_func):
        return False

    # requests_cleaned keeps the addon from repeating its own pass; the
    # vacuum marker records when the VACUUM itself last ran
    (cache_path / MARKER_FILE).write_text(str(datetime.now()))
    (cache_path / VACUUM_MARKER_FILE).write_text(str(datetime.now()))
    return True


def run_cleanup(get_setting: Callable[[str], str], cache_path: Path,
                log_func: Optional[Callable] = None) -> bool:
    """One service cleanup pass, gated on the addon's recache settings."""
    if get_setting('recache.enabled') != 'true':
        return False
    if not cleanup_due(cache_path, int(get_setting('recache.cleanup'))):
        return False
    return cleanup_cache(cache_path, int(get_setting('recache.expiration')), log_func)
