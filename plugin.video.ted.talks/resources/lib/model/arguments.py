import urllib.parse

def parse_arguments(custom_args):
    args_map = {}
    if custom_args:
        args = custom_args[1:].split('&')
        for arg in args:
            if len(arg) > 0:
                split = arg.split('=')
                args_map[split[0]] = urllib.parse.unquote_plus(split[1])
    return args_map