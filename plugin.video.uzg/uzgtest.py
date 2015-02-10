import resources.lib.uzg

uzg = resources.lib.uzg.Uzg()

print uzg.get_overzicht()

print '\n\n'

print uzg.get_items('POMS_S_RKK_687752')

print '\n\n'

print uzg.get_play_url('RKK_1663974')

print '\n\n'

print uzg.get_ondertitel('RKK_1663974')
