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


def sleep_time(time=300):
    '''
    Input: Time to complete authentication
    Return: time to sleep 
    '''
    return time // 100


def loadData(path):
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
