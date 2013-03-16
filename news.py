# -*- coding: utf-8 -*-
from lamson.encoding import properly_decode_header
import nntplib
import flask

app = flask.Flask(__name__)


def get_encoding(s, num):
    return [entry[1].split(";")[1][9:] for entry in
            s.xhdr('Content-Type', num)[1]]


@app.route('/')
def index():
    s = nntplib.NNTP("news.epita.fr")
    groups = sorted(entry[0] for entry in s.list()[1])
    s.quit()
    return flask.render_template('index.html', groups=groups)


@app.route('/<group>')
def get_group(group):
    s = nntplib.NNTP("news.epita.fr")
    _, _, first, last, _ = s.group(group)
    subjects = s.xhdr("subject", first + "-" + last)[1]
    subjects = [(num, properly_decode_header(title)) for
            (num, title) in subjects]
    subjects.reverse()
    return flask.render_template('subjects.html', subjects=subjects)


@app.route('/<group>/<num>')
def get_message(group, num):
    s = nntplib.NNTP('news.epita.fr')
    s.group(group)
    encoding = get_encoding(s, num)
    if len(encoding) != 1:
        encoding = 'utf-8'
    else:
        encoding = encoding[0]
    #message = [properly_decode_header(line) for line in s.body(num)[3]]
    message = [line.decode(encoding, 'replace') for line in s.body(num)[3]]
    return flask.render_template('message.html', message=message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
