def on_keyboard_input(title, default='', hidden=False):
    print '[' + title + ']'
    print "Returning 'Hello World'"
    #var = raw_input("Please enter something: ")
    var = u'Hello World'
    if var:
        return True, var

    return False, ''