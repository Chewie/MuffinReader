# -*- coding: utf-8 -*-
from lamson.encoding import properly_decode_header
import collections
import nntplib
import flask
import re


app = flask.Flask(__name__)


EMAIL_RE = re.compile(
    u'(?P<prefix>\s|<)'
    u'(?P<user>[a-zA-Z.-_]+)'
    u'(?P<domain>@[a-zA-Z.-_]+)'
    u'(?P<suffix>\s|>)'
)


Group = collections.namedtuple('Group', 'name count')
def nntp_to_group(entry):
    return Group(
        name=entry[0],
        count=max(0, int(entry[1]) - int(entry[2]))
    )

def mask_email(line):
    for match in EMAIL_RE.finditer(line):
        user_start = match.start('user')
        user_end = match.end('user')
        user_length = user_end - user_start
        line = line[:user_start] + u'.' * user_length + line[user_end:]
    return line

def get_encoding(s, num):
    return [entry[1].split(";")[1][9:] for entry in
            s.xhdr('Content-Type', num)[1]]


@app.route('/')
def index():
    s = nntplib.NNTP("news.epita.fr")
    groups = sorted(nntp_to_group(entry) for entry in s.list()[1])
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

    # Decode lines from their original charset to Unicode.
    encoding = get_encoding(s, num)
    if len(encoding) != 1:
        encoding = 'utf-8'
    else:
        encoding = encoding[0]
    # And mask email addresses in the same time.
    lines = [
        mask_email(line.decode(encoding, 'replace'))
        for line in s.body(num)[3]
    ]

    return flask.render_template('message.html', message=message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
