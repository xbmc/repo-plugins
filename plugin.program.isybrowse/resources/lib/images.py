import shared

# define image keys
__images__ = {
    'folder': 'folder_2.png',
    'node_on': 'node_on_2.png',
    'node_off': 'node_off_2.png',
    'node_0': 'node_0.png',
    'node_20': 'node_20.png',
    'node_40': 'node_40.png',
    'node_60': 'node_60.png',
    'node_80': 'node_80.png',
    'node_100': 'node_100.png',
    'group': 'group.png',
    'program': 'program_2.png',
    '__default__': 'DefaultFolder.png'}


def getImage(key):
    '''
    getImage(key)

    DESCRIPTION:
    This function parses an image key and
    returns the path to the image.
    '''
    try:
        img = shared.__media__ + __images__[key]
    except:
        img = __images__['__default__']

    return img
