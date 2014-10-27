import flask
from datetime import datetime
from elotron_backend import *
from rankings import *
import numpy as np

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
    match['date'] = date.strftime('%b-%m-%Y %H:%M:%S')
    match['winner'] = np.argmax([score for player,score in match['participants']])
    return match

@app.route('/')
@app.route('/<uname>')
def user(uname=''):
    users = {u:get_display_name(u) for u in get_all_users()}
    matches = [pretty_match(sort_match(match, uname)) for match in get_matches()
               if (match['participants'][0][0] == uname or
                   match['participants'][1][0] == uname or uname == '')]
    matches = reversed(matches)
    return flask.render_template('user.html', matches=matches,
                                 uname=uname, users=users,
                                 ranks=get_elo_ranks(get_matches()),
                                 enumerate=enumerate)

if __name__ == '__main__':
    app.debug = True
    app.run()
