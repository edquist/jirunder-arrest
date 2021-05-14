#!/usr/bin/python

# import os
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
  div {{ max-width: 800px }}
  table {{ text-align: left }}
</style>
</head>
<body>
<h1>
{key} : {fields.summary}
</h1>

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
<th>updated</th>
<td>{renderedFields.updated}</td>
</tr>
<th>components</th>
<td>{_components}</td>
</tr>
<tr>
<th>labels</th>
<td>{_labels}</td>
</tr>
</table>

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

def issue_to_html(j):
    e = easydict(j)
    components = u', '.join( c.name for c in e.fields.components )
    labels     = u', '.join(e.fields.labels)
    html = _issue_html1.format(_components=components, _labels=labels, **e)
    for c in e.renderedFields.comment.comments:
        html += _issue_html2.format(**c)
    html += _issue_html3
    html = re.sub(ur'<img .*?/>', '', html)

    return html


def main(args):
    if len(args) != 1:
        usage("Missing ISSUE")

    issue, = args

    url,h,j = get_issue(issue, expand='renderedFields')
    pp = json.dumps(j, sort_keys=1, indent=2)
#   print "Headers for <%s>" % url
#   print "---"
#   print h
#   print "---"
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


