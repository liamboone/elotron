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
    users = {u:get_display_name(u) for u in get_all_users()}
    matches = [pretty_match(sort_match(match, uname)) for match in get_matches()
               if (match['participants'][0][0] == uname or
                   match['participants'][1][0] == uname or uname == '')]
    matches.reverse()
    ranks = {u:r for u,r in get_elo_ranks(get_matches()).items()}
    top_five = [(r,u) for u,r in ranks.items()]
    top_five.sort(reverse=True)
    top_five = top_five[:5]
    return flask.render_template('user.html', matches=matches,
                                 uname=uname, users=users,
                                 ranks=ranks, top_five=top_five,
                                 enumerate=enumerate)

@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'),
                               'ico/favicon.ico')

@app.route('/<uname>/stats')
def stats(uname=''):
    matches = get_matches()
    rank_history = [ranks for ranks in get_elo_ranks(matches, history=True)]
    urank = [{'elo':rank_history[0][uname], 'time':matches[0]['time']-1}]

    for i, ranks in enumerate(rank_history[1:]):
        urank.append({'elo':ranks[uname], 'time':matches[i]['time']})

    return json.dumps(urank)

@app.route('/add_match/<match_b64>')
def new_match(match_b64):
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
        add_match(match)
        return json.dumps(dump)
    except Exception as e:
        dump['error'].append(([], "Unknown error."))
        return json.dumps(dump)

if __name__ == '__main__':
    app.run()
