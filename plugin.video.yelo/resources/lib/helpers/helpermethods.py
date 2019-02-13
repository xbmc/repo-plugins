import re

def regex(query, url):
    return re.findall(r"%s" % (query), url)[0]

