from __future__ import absolute_import
from collections import namedtuple
import requests
from xbmcswift2 import xbmc

GameState = namedtuple(u'GameState',
    [u'inning_num',
     u'inning_half',
     u'runners_on',
     u'outs',
     u'away_score',
     u'home_score',
     u'away_team',
     u'home_team',
     u'new_batter',
     u'balls',
     u'strikes'])

def get_games(date):
    scoreboard_url = u'http://gd2.mlb.com/components/game/mlb/{0}/master_scoreboard.json'.format(date.strftime(u'year_%Y/month_%m/day_%d'))
    scoreboard = requests.get(scoreboard_url).json()
    games = scoreboard[u'data'][u'games'][u'game']
    game_states = list()
    for game in games:
        game_status = game[u'status']
        # Game is over
        if game_status[u'status'] != u'In Progress':
            continue

        # Game is inbetween innings
        # TODO figure out mid-inning commercial break. figured out pitching change:
        # pbp: {
        # last: "Pitching Change: Kyle Crick replaces Albert Suarez. "
        # }
        if game_status[u'inning_state'] == u'Middle' or game_status[u'inning_state'] == u'End':
            continue

        inning_num = int(game_status[u'inning'])
        inning_half = convert_inning_half(game_status[u'inning_state'])
        runners_on_base = convert_runners_on_base(game[u'runners_on_base'])
        outs = int(game_status[u'o'])
        away_score = int(game[u'linescore'][u'r'][u'away'])
        home_score = int(game[u'linescore'][u'r'][u'home'])
        away_team = game[u'away_name_abbrev']
        home_team = game[u'home_name_abbrev']

        balls = int(game_status['b'])
        strikes = int(game_status['s'])
        new_count = (strikes == 0 and balls == 0)
        walk = balls == 4
        k = strikes == 3
        new_batter = new_count or walk or k

        state = GameState(
            inning_num,
            inning_half,
            runners_on_base,
            outs,
            away_score,
            home_score,
            away_team,
            home_team,
            new_batter,
            balls,
            strikes)
        game_states.append(state)

    return game_states

def convert_runners_on_base(runners_on_base):
    runners_on = list()
    if u'runner_on_1b' in runners_on_base:
        runners_on.append(u'1')
    if u'runner_on_2b' in runners_on_base:
        runners_on.append(u'2')
    if u'runner_on_3b' in runners_on_base:
        runners_on.append(u'3')

    return runners_on

def convert_inning_half(inning_state):
    if inning_state == u'Bottom':
        return u'bot'
    elif inning_state == u'Top':
        return u'top'
    else:
        return inning_state

def best_games(date, leverage_index_csv):
    import leverage_index

    index_table = leverage_index.StaticTableLeverageIndex(leverage_index_csv)
    games = get_games(date)
    leverage_indices = [{
                            "leverage_index": index_table.get(game.inning_num, game.inning_half, game.runners_on, game.outs, game.away_score, game.home_score),
                            "state": game
                        } for game in games]
    if len(leverage_indices) == 0:
        xbmc.log("No games")
        return None
    else:
        best_games = sorted(leverage_indices, key=lambda x: x['leverage_index'], reverse=True)
        xbmc.log("{0}".format(best_games))
        xbmc.log("Best game is {0}".format(best_games[0]))
        return best_games
