import xbmc


def on_keyboard_input(title, default='', hidden=False):
    keyboard = xbmc.Keyboard(default, title, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        return True, keyboard.getText()

    return False, ''