#!/usr/bin/python

import collections
import re

_http_only_pfx = '#HttpOnly_'
_cookie_fields = 'domain subdomains path https_only expires name value'.split()
Cookie = collections.namedtuple('cookie', _cookie_fields)

_url_fields = 'proto domain port path qstr'.split()
Url = collections.namedtuple('Url', _url_fields)

def urlparse(url):
    m = re.match(r'^(\w+)://([^/:]+)(?::(\d+))?(/[^?]*|)(\?.*)?$', url)
    if m:
        return Url(*m.groups())

def cookie_match(c, u):
    if c.https_only and u.proto != 'https':
        return False
    if not u.path.startswith(c.path):
        return False
    # XXX: ignores c.expires
    if c.subdomains:
        return u.domain.endswith(c.domain)
    else:
        return u.domain == c.domain


def line2cookie(line):
    return Cookie(*line.rstrip('\n').split('\t'))


def _read_cookies_gen(fn):
    for line in open(fn):
        if line.startswith(_http_only_pfx):
            line = line[len(_http_only_pfx):]
        if line.startswith('#'):
            continue
        line = line.rstrip('\n')
        if line:
            yield line2cookie(line)


def try_read_cookies(fn):
    try:
        return list(_read_cookies_gen(fn))
    except IOError:
        return None


def cookies_kv(cookies, url):
    u = urlparse(url)
    return [ (c.name, c.value) for c in cookies if cookie_match(c, u) ]


def cookies_kc(cookies, url):
    u = urlparse(url)
    return [ (c.name, c) for c in cookies if cookie_match(c, u) ]


def get_cookie(cookies, url, name):
    return dict(cookies_kc(cookies, url)).get(name)


def cookie_header_val(cookies, url):
    kv = cookies_kv(cookies, url)
    return '; '.join(map('='.join,kv))

