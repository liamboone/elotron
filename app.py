import json
import flask
from datetime import datetime
from elotron_backend import *
from rankings import *
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
    matches_per_page = get_config('matches_per_page', 25)

    admin = False
    if uname.endswith("    "):
        uname = uname[:-4]
        admin = True
    users = {u:get_display_name(u) for u in get_all_users()}

    matches = []
    differential = []
    rank_history = get_elo_ranks(get_matches(), True)

    rank_history = [{u:round(rank[u]) for u in get_all_users()}
                    for rank in rank_history]

    for i, match in enumerate(get_matches()):
        if (match['participants'][0][0] == uname or
            match['participants'][1][0] == uname or
            uname == ''):
            matches.append(pretty_match(sort_match(match, uname)))
            differential.append({u:(rank_history[i+1][u] - rank_history[i][u],
                                    rank_history[i+1][u])
                                 for u in get_all_users()})

    matches.reverse()
    differential.reverse()
    differential = differential[:(matches_per_page+1)]
    ranks = {u:r for u,r in rank_history[-1].items()}
    leaderboard = [(r,u) for u,r in ranks.items()]
    leaderboard.sort(reverse=True)
    return flask.render_template('user.html',
                                 matches=matches[:matches_per_page],
                                 leaderboard=leaderboard[:leaderboard_len],
                                 uname=uname, users=users, ranks=ranks,
                                 admin=admin, differential=differential,
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
    rank_history = [ranks for ranks in get_elo_ranks(matches, history=True)]
    rank_history = [{u:round(rank[u]) for u in get_all_users()}
                    for rank in rank_history]

    date = datetime.fromtimestamp(matches[0]['time']-1)
    datestr = date.strftime('%b %d')
    urank = [{'elo':rank_history[0][uname],
              'time':matches[0]['time']-1,
              'num':0,
              'date':datestr,
              'match':''}]

    n = 0

    for i, ranks in enumerate(rank_history[1:]):
        date = datetime.fromtimestamp(matches[i]['time'])
        datestr = date.strftime('%b %d')
        participants = [p[0] for p in matches[i]['participants']]
        if uname in participants:
            n += 1
            urank.append({'elo':ranks[uname],
                          'time':matches[i]['time'],
                          'num':n,
                          'date':datestr,
                          'match':matchstr(matches[i])})

    return json.dumps(urank)

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
    app.run()
