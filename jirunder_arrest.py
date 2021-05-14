#!/usr/bin/python

# import os
# import re
import sys
import json
# import getopt
# import getpass
import urllib2
# import operator
# import subprocess

_usage = """\
# xxx: [PASS=...] {script} [-u USER[:PASS]] [-d passfd] [-H] COMMAND [args...]
usage: {script} ISSUE
"""

apiurl = 'https://opensciencegrid.atlassian.net/rest/api/2'

GET    = 'GET'
PUT    = 'PUT'
POST   = 'POST'
PATCH  = 'PATCH'
DELETE = 'DELETE'

class Options:
    authstr = None
    show_headers = False

options = Options()


def add_json_header(req):
    req.add_header("Content-Type", "application/json")


def add_auth_header(req):
    if options.authstr:
        req.add_header("Authorization", "Basic %s" % options.authstr)


def uri_ify(data):
    return '?' + '&'.join(map('='.join, sorted(data.items())))


def call_api(method, path, data):
    if data:
        if method == GET:
            path = path + uri_ify(data)
            data = None
        else:
            data = json.dumps(data)

    url = apiurl + path

    req = urllib2.Request(url, data)
    add_auth_header(req)
    add_json_header(req)
    req.get_method = lambda : method
    resp = urllib2.urlopen(req)
    headers = resp.headers
    return url, headers, json.loads(resp.read())


def get_issue(issue, **kw):
    return call_api(GET, "/issue/" + issue, kw)


def main(args):
    if len(args) != 1:
        usage("Missing ISSUE")

    issue, = args

    url,h,j = get_issue(issue, expand='renderedFields')
    pp = json.dumps(j, sort_keys=1, indent=2)
    print "Headers for <%s>" % url
    print "---"
    print h
    print "---"
    print
    print pp


def usage(msg=None):
    if msg:
        print >>sys.stderr, msg + "\n"

    s = os.path.basename(__file__)
    print _usage.format(script=s)
    sys.exit()


if __name__ == '__main__':
    main(sys.argv[1:])


