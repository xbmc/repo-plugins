# define default params
__params__ = {
    'addr': None,
    'type': None,
    'cmd': None,
    'parent': None,
    'browsing': None}


def ParseUrl(url):
    '''
    ParseUrl(url)

    DESCRIPTION:
    This function reads a URL containing GET data and
    seperates the path and each parameter. The input is
    a string containing the URL and the output is a
    dictionary with two keys, path and params. The params
    entry contains a dictionary with an entry for each
    parameter where the keys are the parameter names.
    '''
    # initialize
    output = {}
    url = url.split('?')

    # store path
    output['path'] = url[0]

    # parse parameters
    output['params'] = {}
    if len(url) > 1:
        params = url[1].split('&')
        for param in params:
            param = param.split('=')
            p_name = param[0].strip()
            if len(param) > 0:
                p_val = param[1].strip()
            else:
                p_val = ''
            output['params'][p_name] = p_val

    # set undefined params to default
    for key in __params__.keys():
        if key not in output['params'].keys():
            output['params'][key] = __params__[key]

    return output


def CreateUrl(base, **params):
    '''
    CreateUrl(base, **params)

    DESCRIPTION:
    This function encodes GET data in a URL. The first
    input is the base path. The rest of the inputs
    should be input by name. The name used for input
    will be the name assigned in the URL. The output
    will be the complete URL.
    '''
    url = base
    first = True

    for param in params.keys():
        if params[param] is not None:
            if first:
                url += '?'
                first = False
            else:
                url += '&'
            url += param + '=' + str(params[param])

    return url
