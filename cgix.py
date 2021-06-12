#!/usr/bin/python

import os
import re
import sys

from easydict import easydict
import gzippy

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


_html_header = "Content-Type: text/html; charset=utf-8"
_gzip_header = "Content-Encoding: gzip"

def send_data(data):
    headers = [_html_header]
    if not isinstance(data, bytes):
        data = data.encode("utf-8")
    if accepts_gzip():
        headers += [_gzip_header]
        data = gzippy.compress(data)
    headers += ['','']
    headertxt = "\r\n".join(headers)
    sys.stdout.write(headertxt + data)


def m_hexchr(m):
    return chr(int(m.group(1), 16))


def unescape_qp(s):
    if s:
        if '+' in s: s = s.replace('+', ' ')
        if '%' in s: s = re.sub(ur'%([0-9a-fA-F]{2})', m_hexchr, s)
        if '\r\n' in s: s = s.replace('\r\n', '\n')
    return s


def qp_split(qp):
    return qp.split('=', 1) if '=' in qp else (qp, None)


def parse_qs(qs):
    if qs:
        return dict( map(unescape_qp, qp_split(qp)) for qp in qs.split('&') )


def parse_uri(uri):
    if uri is None:
        return None, None
    if '?' in uri:
        path, qs = uri.split('?', 1)
        qpd = parse_qs(qs)
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


def accepts_gzip():
    enc = os.environ.get("HTTP_ACCEPT_ENCODING")
    return enc and "gzip" in enc.split(", ")


def get_postdata_params():
    pd = get_postdata()
    return parse_qs(pd)


def get_query_params():
    qs = os.environ.get("QUERY_STRING")
    return easydict(parse_qs(qs))


def get_params():
    qpd = get_query_params() or {}
    pdp = get_postdata_params() or {}
    return easydict(qpd, **pdp)


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
        attrtxt = ' '.join(map(escape_attr, attrs))
        tagline += " " + attrtxt
    if _body is None:
        return "<%s />" % tagline
    else:
        if isinstance(_body, (list, tuple)):
            _body = "\n" + "\n".join(_body) + "\n"
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
    "accepts_gzip",
    "escape_html",
    "get_params",
    "get_postdata",
    "get_postdata_params",
    "get_query_params",
    "get_request_method",
    "mk_query_string",
    "parse_qs",
    "parse_request_uri",
    "parse_uri",
    "send_data",
    "unescape_qp",
]

