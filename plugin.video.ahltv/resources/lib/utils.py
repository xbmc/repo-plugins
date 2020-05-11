import pytz, time
import os
import calendar
from datetime import date, datetime, timedelta
from io import BytesIO
from resources.lib.globals import ROOTDIR, ADDON_PATH_PROFILE, ICON
try:
    from urllib import quote  # Python 2.X
    from urllib import urlopen
except ImportError:
    from urllib.parse import quote  # Python 3+
    from urllib.request import urlopen
import sys
import xbmc

def eastern_to_local(eastern_time):
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    timestamp = calendar.timegm(utc_time.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    # Convert it from UTC to local time
    assert utc_time.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_time.microsecond)

def local_to_eastern():
    eastern = pytz.timezone('US/Eastern')
    local_to_utc = datetime.now(pytz.timezone('UTC'))

    eastern_hour = local_to_utc.astimezone(eastern).strftime('%H')
    eastern_date = local_to_utc.astimezone(eastern)
    # Don't switch to the current day until 4:01 AM est
    if int(eastern_hour) < 3:
        eastern_date = eastern_date - timedelta(days=1)

    local_to_eastern = eastern_date.strftime('%Y-%m-%d')
    return local_to_eastern

def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

def string_to_date(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date

def get_game_icon(homeId, homeImgPath, awayId, awayImgPath):
    # Check if game image already exists
    image_path = ADDON_PATH_PROFILE + 'game_icons/' + str(awayId) + '_at_' + str(homeId) + '.png'
    file_name = os.path.join(image_path)
    if not os.path.isfile(file_name):
        try:
            create_game_icon(homeImgPath, awayImgPath, image_path)
        except:
            image_path = ICON
            pass

    return image_path


def create_game_icon(homeSrcImg, awaySrcImg, image_path):
    try:
        from PIL import Image
    except:
        try:
            from pil import Image
        except:
            xbmc.log("PIL not available")
            sys.exit()

    bg = Image.open(ROOTDIR + '/resources/media/game_icon_bg.png')
    size = 200, 200

    img_file = urlopen(homeSrcImg)
    im = BytesIO(img_file.read())
    home_image = Image.open(im)
    home_image.thumbnail(size, Image.ANTIALIAS)
    home_image = home_image.convert("RGBA")

    img_file = urlopen(awaySrcImg)
    im = BytesIO(img_file.read())
    away_image = Image.open(im)
    away_image.thumbnail(size, Image.ANTIALIAS)
    away_image = away_image.convert("RGBA")

    bg.paste(away_image, (0, 60), away_image)
    bg.paste(home_image, (200, 60), home_image)

    if not os.path.exists(os.path.dirname(image_path)):
        try:
            os.makedirs(os.path.dirname(image_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    bg.save(image_path)

def log(msg, error = False):
    """
    Log an error
    @param msg The error to log
    @param error error severity indicator
    """
    try:
        import xbmc
        full_msg = "plugin.video.ahltv: {}".format(msg)
        xbmc.log(full_msg, level=xbmc.LOGERROR if error else xbmc.LOGDEBUG)
    except:
        print(msg)
