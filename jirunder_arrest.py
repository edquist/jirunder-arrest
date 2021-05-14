#!/usr/bin/python

import os
import re
import sys
import json
# import getopt
# import getpass
import urllib2
# import operator
# import subprocess

from easydict import easydict

_usage = """\
# xxx: [PASS=...] {script} [-u USER[:PASS]] [-d passfd] [-H] COMMAND [args...]
usage: {script} ISSUE
   or: REQUEST_URL=...?issue=TICKET-NUM {script}  # CGI
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


def escape_html(txt, quot=False):
    txt = txt.replace('&', '&amp;')
    txt = txt.replace('<', '&lt;')
    txt = txt.replace('>', '&gt;')
    return txt


_issue_html1 = u"""\
<!DOCTYPE html>
<html>
<head>
<style>
  div   {{ max-width: 800px }}
  table {{ text-align: left }}
  .fr   {{ float: right     }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
<h1>
{key} : {_summary}
</h1>

<div class='fr'>
<table>
<tr>
<th>assignee</th>
<td>{fields.assignee.displayName}</td>
</tr>
<tr>
<th>reporter</th>
<td>{fields.reporter.displayName}</td>
</tr>
<tr>
<th>created</th>
<td>{renderedFields.created}</td>
</tr>
<tr>
<th>updated</th>
<td>{renderedFields.updated}</td>
</tr>
<tr>
<th>components</th>
<td>{_components}</td>
</tr>
<tr>
<th>labels</th>
<td>{_labels}</td>
</tr>
</table>
</div>

<h2>Description</h2>

<div>
{renderedFields.description}
</div>

<hr/>

<h2>Comments</h2>

<div>

"""

_issue_html2 = u"""\
<h3>
{created} | {author.displayName}
</h3>
<div>
{body}
</div>
<hr/>
"""

_issue_html3 = u"""\
</div>

</body>
</html>
"""

_ignorepats = [
    ur' *<img .*?/>',
    ur' *<span [^>]*jira-macro-single-issue-export-pdf[^>]*>[^<]*</span>',
    ur'\s+(?=</a>)',
]

def issue_to_html(j):
    e = easydict(j)
    e._components = u', '.join( c.name for c in e.fields.components )
    e._labels     = u', '.join(e.fields.labels)
    e._summary    = escape_html(e.fields.summary)
    html = _issue_html1.format(**e)
    for c in e.renderedFields.comment.comments:
        html += _issue_html2.format(**c)
    html += _issue_html3
    for pat in _ignorepats:
        html = re.sub(pat, u'', html)
    return html


_landing_html = u"""\
<!DOCTYPE html>
<html>
<body>
Try sticking a "?issue=SOFTWARE-4000" after the URL.
</body>
</html>
"""
def landing_page():
    return _landing_html

def html_header():
    return "Content-Type: text/html; charset=utf-8\r\n\r"

def main(args):
    if len(args) == 1:
        issue, = args
        if not re.match(r'^[A-Z]+-[0-9]+$', issue):
            usage("Bad ISSUE")
        dump_issue_json(issue)
        return

    if args:
        usage("Extra arg")

    uri, params = parse_request_uri()
    if not uri:
        usage("Missing ISSUE")

    if not params or 'issue' not in params:
        print html_header()
        print landing_page().encode("utf-8")
        return

    url,h,j = get_issue(params.issue, expand='renderedFields')
    print html_header()
    print issue_to_html(j).encode("utf-8")



def dump_issue_json(issue):
    url,h,j = get_issue(issue, expand='renderedFields')
    pp = json.dumps(j, sort_keys=1, indent=2)
#   print "Headers for <%s>" % url
#   print "---"
#   print h
#   print "---"
    print
    print pp


def m_hexchr(m):
    return chr(int(m.group(1), 16))

def unescape_uri(s):
    return re.sub(ur'%([0-9a-f]{2})', m_hexchr, s) if '%' in s else s


def parse_uri(uri):
    if uri is None:
        return None, None
    if '?' in uri:
        path, qp = uri.split('?', 1)
        qpd = dict( map(unescape_uri, x.split('=', 1)) for x in qp.split('&') )
        return path, easydict(qpd)
    else:
        return uri, None


def parse_request_uri():
    uri = os.environ.get("REQUEST_URI")
    return parse_uri(uri)


def usage(msg=None):
    if msg:
        print >>sys.stderr, msg + "\n"

    s = os.path.basename(__file__)
    print _usage.format(script=s)
    sys.exit()


if __name__ == '__main__':
    main(sys.argv[1:])


