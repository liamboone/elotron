import json
import flask
from datetime import datetime
from elotron_backend import *
from rankings import *
from itertools import product
import numpy as np
import base64 as b64
import sys

app = flask.Flask(__name__)

def _match_cmp(x, y, uname):
    if x[0] == uname:
        return 1
    if y[0] == uname:
        return -1
    return cmp(x[1], y[1])

def sort_match(match, uname):
    smatch = {}
    smatch['time'] = match['time']
    smatch['participants'] = sorted(match['participants'],
                                    cmp=lambda x, y: _match_cmp(x, y, uname),
                                    reverse=True)
    return smatch

def pretty_match(match):
    date = datetime.fromtimestamp(match['time'])
    match['date'] = date.strftime('%b-%d-%Y %H:%M:%S')
    match['winner'] = np.argmax([score for player,score in match['participants']])
    return match

@app.route('/')
@app.route('/<uname>')
def user(uname=''):
    leaderboard_len = get_config('leaderboard_length', 10)
    matches_per_page = get_config('matches_per_page', 24)
    new_player_period = get_config('new_player_period', 0)

    admin = False
    if uname.endswith("    "):
        uname = uname[:-4]
        admin = True
    users = {u:get_display_name(u) for u in get_all_users()}

    match_history = get_matches()

    matches = []
    differential = []

    # Get the match history for this user or all users, depending
    # on which page we're on
    for i, match in enumerate(match_history):
        if (match['participants'][0][0] == uname or
            match['participants'][1][0] == uname or
            uname == ''):
            matches.append(pretty_match(sort_match(match, uname)))

    # Get rank history for this user or all users
    players = []
    if uname == '':
        players = get_all_users()
    else:
        players = [uname]

    # This call returns the rank updates from any matches in the match history
    # which involve players in the player list
    states, times = zip(*get_elo_ranks(match_history, history=True, players=players))
    for s in states:
        differential.append({u:(s[u]['rank_change'], round(s[u]['post_match_rank'])) for u in players})

    # This call returns the final state of all players in the match history
    cur_state, cur_time = get_elo_ranks(match_history, history=False, players=[])
    
    matches.reverse()
    differential.reverse()
    differential = differential[:(matches_per_page+1)]
    ranks = {u:round(cur_state[u]['post_match_rank']) for u in get_all_users()}
    leaderboard = [(round(cur_state[u]['post_match_rank']), u, cur_state[u]['num_matches']) for u in get_all_users()] 
    leaderboard.sort(reverse=True)
    return flask.render_template('user.html',
                                 matches=matches[:matches_per_page],
                                 leaderboard=leaderboard[:leaderboard_len],
                                 uname=uname, users=users, ranks=ranks,
                                 admin=admin, differential=differential,
                                 new_player_period=new_player_period,
                                 enumerate=enumerate)

@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'),
                               'ico/favicon.ico')

def matchstr(match):
    participants = sorted(match['participants'], key=lambda x: x[1])
    return ["{}: {}".format(get_display_name(p[0]), p[1])
            for p in participants]


@app.route('/<uname>/stats')
def stats(uname=''):
    matches = get_matches()
    urank = []
    states, times = zip(*get_elo_ranks(matches, history=True, players=[uname]))
    for i, state in enumerate(states):
        date = datetime.fromtimestamp(times[i])
        datestr = date.strftime('%m/%d/%YT%H:%M:%S')
        match = sort_match(state[uname]['last_match'], uname)

        p1n = uname
        p1s = match['participants'][0][1]
        p1e = round(state[p1n]['pre_match_rank'])

        p2n = match['participants'][1][0]
        p2s = match['participants'][1][1]
        p2e = round(state[p2n]['pre_match_rank'])

        urank.append({'date':datestr,
                      'player1': get_display_name(p1n),
                      'player1score': p1s,
                      'player1elo': p1e,
                      'player2': get_display_name(p2n),
                      'player2score': p2s,
                      'player2elo': p2e})
    return json.dumps(urank)

@app.route('/allstats')
def allstats():
    users = get_all_users()
    points = {u:{v:0 for v in users if u != v} for u in users}
    games = {u:{v:0 for v in users if u != v} for u in users}

    for match in get_matches():
        (p1, s1), (p2, s2) = match['participants']
	games[p1][p2] += 1
	games[p2][p1] += 1
        points[p1][p2] = ((games[p1][p2]-1)*points[p1][p2] + s1) / games[p1][p2]
        points[p2][p1] = ((games[p2][p1]-1)*points[p2][p1] + s2) / games[p2][p1]

    userPairs = [tuple(sorted((u,v)))
                 for u,v in product(users, users) if u != v]
    userPairs = set(userPairs) # Remove duplicates

    data = [{'player1': get_display_name(u),
             'player2': get_display_name(v),
             'pointsTaken': points[u][v],
             'pointsGiven': points[v][u]}
            for u,v in userPairs]

    return json.dumps(data)

@app.route('/add_match/<match_b64>')
def new_match(match_b64):
    month = int(flask.request.args.get('month','0'))
    day = int(flask.request.args.get('day','0'))
    player1, score1, player2, score2 = b64.b64decode(match_b64).split(';')
    dump = {'error': []}
    bad_match = False

    try: #test score1
        score1 = int(score1)
    except ValueError:
        dump['error'].append((['score1'],
                              '"{}" is not an integer.'.format(score1)))
        bad_match = True

    try: #test score2
        score2 = int(score2)
    except ValueError:
        dump['error'].append((['score2'],
                              '"{}" is not an integer.'.format(score2)))
        bad_match = True

    if player1 == player2:
        dump['error'].append((['player1', 'player2'],
                              "Matches must have distinct opponents."))
        bad_match = True

    if bad_match:
        return json.dumps(dump)

    match = [(player1, score1), (player2, score2)]
    try:
        if month > 0 and day > 0:
            add_match_on_day(match, month, day)
        else:
            add_match(match)
    except DuplicateError:
        pass
    except Exception as e:
        dump['error'].append(([], str(e)))

    return json.dumps(dump)

if __name__ == '__main__':
    app.run(debug=False)
