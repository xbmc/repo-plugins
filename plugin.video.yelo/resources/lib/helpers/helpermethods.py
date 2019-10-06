import re

def regex(query, url):
    try:
        return re.findall(r"%s" % (query), url)[0]
    except IndexError:
        return None

