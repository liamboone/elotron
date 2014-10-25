import flask
from elotron_backend import *

app = flask.Flask(__name__)

@app.route('/')
def index():
    return "\n".join(map(get_display_name, get_all_users()))
    return flask.render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
