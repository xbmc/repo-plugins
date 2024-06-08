# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

def make_node(name=None, icon=None, path=None, **kwargs):
    from json import loads
    from xbmcgui import Dialog
    from tmdbhelper.lib.addon.plugin import get_infolabel, get_localized
    from tmdbhelper.lib.files.futils import get_files_in_folder, read_file
    from tmdbhelper.lib.addon.consts import NODE_BASEDIR
    from tmdbhelper.lib.files.futils import dumps_to_file

    name = name or get_infolabel('Container.ListItem.Label') or ''
    icon = icon or get_infolabel('Container.ListItem.Icon') or ''
    path = path or get_infolabel('Container.ListItem.FolderPath') or ''
    item = {'name': name, 'icon': icon, 'path': path}

    basedir = NODE_BASEDIR
    files = get_files_in_folder(basedir, r'.*\.json')

    x = Dialog().select(get_localized(32504).format(name), [f for f in files] + [get_localized(32495)])
    if x == -1:
        return
    elif x == len(files):
        file = Dialog().input(get_localized(551))
        if not file:
            return
        meta = {
            "name": file,
            "icon": "",
            "list": []}
        file = f'{file}.json'
    else:
        file = files[x]
        data = read_file(basedir + file)
        meta = loads(data) or {}
    if not meta or 'list' not in meta:
        return

    removals = []
    for x, i in enumerate(meta['list']):
        if path != i['path']:
            continue
        if not Dialog().yesno(f'{name}', get_localized(32492).format(name, file)):
            return
        removals.append(x)

    if removals:
        for x in sorted(removals, reverse=True):
            del meta['list'][x]
        text = get_localized(32493).format(name, file)
    else:
        meta['list'].append(item)
        text = get_localized(32494).format(name, file)

    dumps_to_file(meta, basedir, file, join_addon_data=False)
    Dialog().ok(f'{name}', text)