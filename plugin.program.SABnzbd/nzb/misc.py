import os

def _get_path(file):
    cur_dir = os.getcwd()
    cur_dir = cur_dir.replace(';', '')
    return os.path.join(cur_dir, file)

def check_attribute(obj, key, default):
    try:
        return getattr(obj, key)
    except:
        return default
    
def check_dict_key(dictionary, key, default):
    try:
        return dictionary[key]
    except:
        return default