import flask
from datetime import datetime
from elotron_backend import *
from rankings import *

app = flask.Flask(__name__)

def _match_cmp(x, y, uname):
    if x[0] == uname:
        return -1
    if y[0] == uname:
        return 1
    return cmp(x[1], y[1])

def sort_match(match, uname):
    smatch = {}
    smatch['time'] = match['time']
    smatch['participants'] = sorted(match['participants'],
                                    cmp=lambda x, y: _match_cmp(x, y, uname))
    return smatch

def pretty_match(match):
    date = datetime.fromtimestamp(match['time'])
    match['date'] = date.strftime('%b-%m-%Y %H:%M:%S')
    return match

@app.route('/<uname>')
def user(uname=''):
    users = {u:get_display_name(u) for u in get_all_users()}
    matches = [pretty_match(sort_match(match, uname)) for match in get_matches()
               if (match['participants'][0][0] == uname or
                   match['participants'][1][0] == uname)]
    return flask.render_template('user.html', matches=matches,
                                 uname=uname, users=users,
                                 ranks=get_elo_ranks(get_matches()))


@app.route('/')
def index():
    return flask.render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
