import flask
from elotron_backend import *

app = flask.Flask(__name__)

@app.route('/<uname>')
def user(uname=''):
    users = {u:get_display_name(u) for u in get_all_users()}
    matches = [match for match in get_matches()
               if (match['participants'][0][0] == uname or
                   match['participants'][1][0] == uname)]
    return flask.render_template('user.html', matches=matches,
                                 uname=uname, users=users)


@app.route('/')
def index():
    return flask.render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
