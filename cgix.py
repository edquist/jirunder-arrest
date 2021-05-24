#!/usr/bin/python

import os
import re
import sys

from easydict import easydict

def mk_query_string(data):
    itemstrs = sorted( (k, str(v)) for k,v in data.items() )
    return '?' + '&'.join(map('='.join, itemstrs))


def escape_html(txt, quot=False):
    txt = txt.replace('&', '&amp;')
    txt = txt.replace('<', '&lt;')
    txt = txt.replace('>', '&gt;')
    if quot:
        txt = txt.replace('"', '&quot;')
    return txt


def html_header():
    return "Content-Type: text/html; charset=utf-8\r\n\r"


def m_hexchr(m):
    return chr(int(m.group(1), 16))


def unescape_qp(s):
    if '+' in s: s = s.replace('+', ' ')
    if '%' in s: s = re.sub(ur'%([0-9a-fA-F]{2})', m_hexchr, s)
    if '\r\n' in s: s = s.replace('\r\n', '\n')
    return s


def parse_qp(qp):
    if qp:
        return dict( map(unescape_qp, x.split('=', 1)) for x in qp.split('&') )


def parse_uri(uri):
    if uri is None:
        return None, None
    if '?' in uri:
        path, qp = uri.split('?', 1)
        qpd = parse_qp(qp)
        return path, easydict(qpd)
    else:
        return uri, None


def parse_request_uri():
    uri = os.environ.get("REQUEST_URI")
    return parse_uri(uri)


def get_postdata():
    clen = os.environ.get("CONTENT_LENGTH")
    if clen is not None:
        return sys.stdin.read(int(clen))


def get_postdata_params():
    pd = get_postdata()
    return parse_qp(pd)


def get_request_method():
    return os.environ.get("REQUEST_METHOD")


def quote_attr_val(val):
    if isinstance(val, int):
        return "%s" % val  # or: val = "%s" % val
    if "'" in val:
        return '"%s"' % escape_html(val, quot=True)
    else:
        return "'%s'" % escape_html(val)


def escape_attr(kv):
    key, val = kv
    key = key.lower()  # Class -> "class"
    return (key if val is None else
           '{key}={val}'.format(key=key, val=quote_attr_val(val)))


def mktag(_name, _body=None, _attrs=None, **_kw):
    attrs = _attrs or []
    attrs += sorted(_kw.items())
    tagline = _name
    if attrs:
        attrtxt = '; '.join(map(escape_attr, attrs))
        tagline += " " + attrtxt
    if _body is None:
        return "<%s />" % tagline
    else:
        return "<{tagline}>{_body}</{tagline}>".format(**locals())


class Tag:
    def __init__(self, tag):
        self.tag = tag

    def __call__(self, *_a_, **_kw_):
        return mktag(self.tag, *_a_, **_kw_)

    def __str__(self):
        return self()


# ... #

__all__ = [
    "Tag",
    "escape_html",
    "get_postdata",
    "get_postdata_params",
    "get_request_method",
    "html_header",
    "mk_query_string",
    "parse_qp",
    "parse_request_uri",
    "parse_uri",
    "unescape_qp",
]

