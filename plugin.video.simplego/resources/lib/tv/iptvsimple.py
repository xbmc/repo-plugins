"""Our own IPTV Simple instance: its settings file, pointed at the files iptvfiles writes.

Other instances are never written (why IPTV Manager was ruled out: it copies one settings
file over every instance file).
"""

import glob
import os
import re
from xml.sax.saxutils import escape
from xml.sax.saxutils import unescape

from resources.lib.tv import iptvfiles

IPTV_SIMPLE = "pvr.iptvsimple"


def update_instance(iptv_simple_profile, m3u_path, epg_path, create=False, colours=True):
    """Create our IPTV Simple instance (create=True) or bring its file paths up to date.

    Only MANAGED settings are enforced; the rest start at a default and are the user's.
    Returns True when the file changed, i.e. IPTV Simple must restart to read it.
    """
    path = instance_file(iptv_simple_profile, m3u_path)
    wanted = dict(_instance_defaults(m3u_path, epg_path, colours))
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            current = dict(re.findall(r'<setting id="([^"]+)"[^>]*>([^<]*)</setting>', f.read()))
        current = {k: unescape(v) for k, v in current.items()}
        settings = dict(current)
        for key, value in wanted.items():
            if key in MANAGED or key not in settings:
                settings[key] = value
        if settings == current:
            return False
    elif create:
        settings = wanted
    else:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(_settings_xml(settings.items()))
    return True


def instance_file(iptv_simple_profile, our_m3u):
    """Return the path of our IPTV Simple instance file: the existing one, or the next free number.

    An instance is ours only if it already points at our playlist.
    """
    numbers = []
    for path in sorted(glob.glob(os.path.join(iptv_simple_profile, "instance-settings-*.xml"))):
        m = re.search(r"instance-settings-(\d+)\.xml$", path)
        if not m:
            continue
        numbers.append(int(m.group(1)))
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if our_m3u in text:
            return path
    return os.path.join(iptv_simple_profile, "instance-settings-%d.xml" % (max(numbers or [0]) + 1))


# Instance settings the add-on keeps up to date; the rest are IPTV Simple's own once created.
MANAGED = ("kodi_addon_instance_name", "m3uPathType", "m3uPath", "epgPathType", "epgPath", "genresPathType", "genresPath")


def _instance_defaults(m3u_path, epg_path, colours=True):
    return [
        ("kodi_addon_instance_name", iptvfiles.INSTANCE_NAME),
        ("kodi_addon_instance_enabled", "true"),
        ("m3uPathType", "0"),
        ("m3uPath", m3u_path),
        # Hourly re-read of the local files: the service's fetches show within the hour.
        ("m3uRefreshMode", "1"),
        ("m3uRefreshIntervalMins", "60"),
        ("epgPathType", "0"),
        ("epgPath", epg_path),
        ("epgCache", "true"),
        ("logoPathType", "1"),
        # DVB mapping for colours only; useEpgGenreText keeps the Hungarian text shown.
        ("genresPathType", "0"),
        ("genresPath", epg_path.rsplit("/", 1)[0] + "/" + (iptvfiles.GENRE_MAP if colours else iptvfiles.GENRE_MAP_PLAIN)),
        ("useEpgGenreText", "true"),
        ("catchupEnabled", "true"),
    ]


def _settings_xml(settings):
    body = "".join('    <setting id="%s">%s</setting>\n' % (k, escape(v)) for k, v in settings)
    return '<settings version="2">\n%s</settings>\n' % body
