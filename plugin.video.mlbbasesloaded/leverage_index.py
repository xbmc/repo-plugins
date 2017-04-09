from __future__ import with_statement
from __future__ import absolute_import
import csv
from collections import defaultdict
from io import open
from itertools import imap

class StaticTableLeverageIndex(object):
    u""" Uses a static CSV file to compute leverage index

    >>> # Happy path test
    >>> index = StaticTableLeverageIndex('resources/li.csv')
    >>> index.get(7, 'bot', [u'3'], 2, 5, 5)
    2.6
    >>> # Test when run differential is outside range [-4, +4]
    >>> index.get(7, 'bot', [u'3'], 2, 1, 12) == index.get(7, 'bot', [u'3'], 2, 1, 5)
    True
    >>> index.get(7, 'bot', [u'3'], 2, 12, 1) == index.get(7, 'bot', [u'3'], 2, 5, 1)
    True
    >>> # Test no one on
    >>> index.get(7, 'bot', [], 0, 1, 1)
    1.5
    >>> # Test extra innings
    >>> index.get(9, 'bot', [], 0, 1, 1) == index.get(12, 'bot', [], 0, 1, 1)
    True
    """
    def __init__(self, li_table_filepath):
        # Structure of self.li_table is:
        # self.li_table[inning_num][inning_half][runners_on][outs][run_differential] = leverage_index
        # where runners_on looks like "_ 2 _" or "_ _ _" or "1 2 _"
        self.li_table = self._init_li_table(li_table_filepath)

    def _init_li_table(self, li_table_filepath):
        # Fields are: inning_num,inning_half,runners_on,outs,-4,-3,-2,-1,0,+1,+2,+3,+4 where "-3" means home team is down by 3
        li_table = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        with open(li_table_filepath, 'r', encoding='utf-8') as f:
            # Skip comment lines starting with '#'
            li_table_csv = csv.reader(filter(lambda row: row[0] != '#', f))
            for row in li_table_csv:
                _3to2list = list(row)
                inning_num, inning_half, runners_on, outs, run_differential, = _3to2list[:4] + [_3to2list[4:]]
                # Convert each run differential key from str to float
                run_differential = list(imap(float, run_differential))
                li_table[int(inning_num)][inning_half][runners_on][int(outs)] = run_differential
        return li_table

    def get(self, inning_num, inning_half, runners_on, num_outs, away_score, home_score):
        assert inning_half == u'top' or inning_half == u'bot'
        assert inning_num > 0
        assert len(runners_on) <= 3
        assert 0 <= num_outs and num_outs < 3
        assert away_score >= 0 and home_score >= 0
        return self._get_impl(inning_num, inning_half, runners_on, num_outs, away_score, home_score)

    def _get_impl(self, inning_num, inning_half, runners_on, num_outs, away_score, home_score):
        run_differential_index = self._get_run_differential(away_score, home_score) + 4
        runners_on_str = self._convert_runners_on(runners_on)
        inning_num_index = min(inning_num, 9)

        return self.li_table[inning_num_index][inning_half][runners_on_str][num_outs][run_differential_index]

    def _get_run_differential(self, away_score, home_score):
        MINIMUM = -4
        MAXIMUM = 4
        differential = home_score - away_score
        clamped_differential = max(MINIMUM, min(differential, MAXIMUM))
        return clamped_differential

    def _convert_runners_on(self, runners_on):
        assert all(type(x) is unicode for x in runners_on)

        runners_on_str = unicode()
        runners_on_str += u'1 ' if u'1' in runners_on else u'_ '
        runners_on_str += u'2 ' if u'2' in runners_on else u'_ '
        runners_on_str += u'3'  if u'3' in runners_on else u'_'
        return runners_on_str

if __name__ == u'__main__':
    import doctest
    doctest.testmod()
