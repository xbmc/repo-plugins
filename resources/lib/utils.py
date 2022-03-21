from urllib import parse


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


