''' Entry code for plugin.program.rtorrent '''

import sys
import xbmc
import resources.lib.functions as f

xbmc.log("Arguments: "+sys.argv[2])

PARAMS = f.get_params()

mode = PARAMS.get('mode', None)

if mode is None:
    import resources.lib.mode_main as loader
    loader.main()
elif mode == 'files':
    import resources.lib.mode_files as loader
    loader.main(PARAMS['digest'], PARAMS['numfiles'])
elif mode == 'action':
    import resources.lib.mode_action as loader
    loader.main(**PARAMS)
elif mode == 'play':
    import resources.lib.mode_play as loader
    loader.main(PARAMS['digest'], PARAMS['file_hash'])
