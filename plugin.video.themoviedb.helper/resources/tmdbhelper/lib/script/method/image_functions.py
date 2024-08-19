# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


def blur_image(blur_image=None, prefix='ListItem', **kwargs):
    from tmdbhelper.lib.monitor.images import ImageFunctions
    blur_img = ImageFunctions(method='blur', artwork=blur_image, prefix=prefix)
    blur_img.setName('blur_img')
    blur_img.start()


def image_colors(image_colors=None, prefix='ListItem', **kwargs):
    from tmdbhelper.lib.monitor.images import ImageFunctions
    image_colors = ImageFunctions(method='colors', artwork=image_colors, prefix=prefix)
    image_colors.setName('image_colors')
    image_colors.start()
