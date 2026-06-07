import sys

import invidious_plugin

import xbmc
import xbmcplugin


def main():
    plugin = invidious_plugin.InvidiousPlugin.from_argv()

    xbmcplugin.setContent(plugin.addon_handle, "videos")

    return plugin.run()


if __name__ == "__main__":
    sys.exit(main())
