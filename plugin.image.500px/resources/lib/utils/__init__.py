

def print_ret_val(f):
    def decorated(*args, **kwargs):
        ret = f(*args, **kwargs)
        print "%s returned value %s" % (f.__name__, ret)
        return ret

    return decorated