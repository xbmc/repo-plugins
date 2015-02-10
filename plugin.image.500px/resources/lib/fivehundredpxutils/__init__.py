

def print_ret_val(f):
    def decorated(*args, **kwargs):
        ret = f(*args, **kwargs)
        return ret

    return decorated
