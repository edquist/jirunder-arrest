#!/usr/bin/python

import os
import re
import sys

from easydict import easydict

def mk_query_string(data):
    return '?' + '&'.join(map('='.join, sorted(data.items())))


def escape_html(txt, quot=False):
    txt = txt.replace('&', '&amp;')
    txt = txt.replace('<', '&lt;')
    txt = txt.replace('>', '&gt;')
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


# ... #

__all__ = [
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

