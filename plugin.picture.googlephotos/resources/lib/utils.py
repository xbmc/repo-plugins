from urllib import parse
import pickle
import os


def build_url(base_url, query: dict, qs=None) -> str:
    '''
    Options: query to be encoded
    qs to be modified with items from the query dict
    Assumes single value for a key
    Returns a url
    '''
    if qs:
        qdict = dict(parse.parse_qsl(qs))
        for key, val in query.items():
            qdict[key] = val
        return base_url + '?' + parse.urlencode(qdict)
    return base_url + '?' + parse.urlencode(query)

def join_path(*args):
    '''
    Joins path parts and strips extra slashes
    '''
    return '/'.join(s.strip('/') for s in args)
def sleep_time(time=300):
    '''
    Input: Time to complete authentication
    Return: time to sleep(in msec) 
    '''
    return (time * 10)

# Portability not guaranteed
# check xbmcvfs


def loadData(path):
    # For caching links
    if not os.path.exists(path):
        return None
    data = []
    with open(path, 'rb') as fr:
        try:
            while True:
                data.append(pickle.load(fr))
        except EOFError:
            pass
    return data


def storeData(path, db: dict):
    # Appends data to file
    dbfile = open(path, 'ab')
    # source, destination
    pickle.dump(db, dbfile)
    dbfile.close()


def buildFilter(__addon__):
    is_date_filter_applied = __addon__.getSettingBool('date_filter')
    start_date = __addon__.getSettingString('start_date')
    end_date = __addon__.getSettingString('end_date')
    media_type = __addon__.getSettingString('media_filter')
    content_type = __addon__.getSettingString('content_filter')
    favourites = __addon__.getSettingBool('favourites')
    filters = {}
    if (is_date_filter_applied and (start_date < end_date)):
        sd = start_date.split('-')
        ed = end_date.split('-')
        filters['dateFilter'] = {
            "ranges": [
                {
                    "startDate": {
                        "year": sd[0],
                        "month": sd[1],
                        "day": sd[2]
                    },
                    "endDate":{
                        "year": ed[0],
                        "month": ed[1],
                        "day": ed[2]
                    }
                }
            ]
        }

    if media_type != 'All Media':
        filters['mediaTypeFilter'] = {
            'mediaTypes': [
                media_type.upper().replace(' ', '_')
            ]
        }

    if content_type != 'None':
        filters['contentFilter'] = {
            'includedContentCategories': [
                content_type.upper()
            ]
        }

    if favourites:
        filters['featureFilter'] = {
            "includedFeatures": [
                'FAVOURITES'
            ]
        }

    return filters
