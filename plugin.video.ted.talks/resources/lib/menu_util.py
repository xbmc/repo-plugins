def create_context_menu(getLS):
    context_menu = []
    context_menu += [(getLS(30097), 'Action(queue)')]
    context_menu += [('Toggle watched', 'Action(ToggleWatched)')]
    return context_menu
