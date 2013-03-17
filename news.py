# -*- coding: utf-8 -*-

from lamson.encoding import properly_decode_header
import flask

import collections
import email.header
import nntplib
import re


app = flask.Flask(__name__)


EMAIL_RE = re.compile(
    u'(?P<prefix>\s|<)'
    u'(?P<user>[-a-zA-Z._]+)'
    u'(?P<domain>@[-a-zA-Z._]+)'
    u'(?P<suffix>\s|>)'
)


Group = collections.namedtuple('Group', 'name count')
def nntp_to_group(entry):
    return Group(
        name=entry[0],
        count=max(0, int(entry[1]) - int(entry[2]) + 1)
    )

Header = collections.namedtuple('Header', 'name content')
def nntp_to_header_name(line):
    return line.lower().split(': ', 1)[0]
def nntp_to_header_content(line):
    return ''.join(
        part.decode(encoding or 'ascii', 'replace')
        for part, encoding
        in email.header.decode_header(line.split(': ', 1)[1])
    )

def mask_email(line):
    for match in EMAIL_RE.finditer(line):
        user_start = match.start('user')
        user_end = match.end('user')
        user_length = user_end - user_start
        line = line[:user_start] + u'.' * user_length + line[user_end:]
    return line

class Line(object):
    # These tags maps CSS span classes.
    QUOTE = 'quote'
    QUOTE_QUOTE = 'quote_quote'
    SIGNATURE = 'signature'

    QUOTE_PREFIXES = (u'>', u'|')
    QUOTE_QUOTE_PREFIXES = (u'>>', u'||', u'>|', u'|>')

    def __init__(self, text, starts=None, ends=None):
        self.text = text
        self.starts = starts
        self.ends = ends

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

    # Decode headers, and mask emails in it.
    headers_set = ('subject', 'from', 'date')
    headers = [
        Header(
            name=nntp_to_header_name(line).capitalize(),
            content=mask_email(nntp_to_header_content(line))
        )
        for line in s.head(num)[3]
        if nntp_to_header_name(line) in headers_set
    ]

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

    # Tag lines to recognize quotes and signatures.
    message = []
    state = None
    for line in lines:
        # By default, do not change the state
        new_state = state
        if state == Line.SIGNATURE:
            # After a signature mark, everything belongs to the signature
            pass
        elif state in (None, Line.QUOTE, Line.QUOTE_QUOTE):
            if line[0:2] in Line.QUOTE_QUOTE_PREFIXES:
                new_state = Line.QUOTE_QUOTE
            elif line[0:1] in Line.QUOTE_PREFIXES:
                new_state = Line.QUOTE
            elif line == u'-- ':
                new_state = Line.SIGNATURE
            else:
                new_state = None
        else:
            assert False, 'Wrong state: %s' % state
        starts = None
        if new_state != state:
            if state is not None:
                message[-1].ends = state
            starts = new_state
        message.append(Line(line, starts))
        state = new_state
    # Close any remaining tag.
    if state != None:
        message[-1].ends = state

    return flask.render_template(
        'message.html',
        headers=headers, message=message
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
