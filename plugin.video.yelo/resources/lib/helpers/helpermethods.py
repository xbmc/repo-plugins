import re
import time


def regex(query, url):
    try:
        return re.findall(r"%s" % (query), url)[0]
    except IndexError:
        return None


def get_timestamp():
    return int(time.time())


def make_request(req_instance, method, url, headers=None, data=None, json=None, allow_redirects=False, cookies=None,
                 verify=True):
    if method.upper() == "POST":
        r = req_instance.post(url=url,
                              data=data,
                              headers=headers,
                              json=json,
                              allow_redirects=allow_redirects,
                              cookies=cookies,
                              verify=verify)
    elif method.upper() == "GET":
        r = req_instance.get(url=url,
                             data=data,
                             headers=headers,
                             json=json,
                             allow_redirects=allow_redirects,
                             cookies=cookies,
                             verify=verify)
    else:
        r = None

    return r
