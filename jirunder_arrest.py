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
import cookies

_usage = """\
# xxx: [PASS=...] {script} [-u USER[:PASS]] [-d passfd] [-H] COMMAND [args...]
usage: {script} ISSUE
   or: REQUEST_URI=...?issue=TICKET-NUM {script}  # CGI
"""

jira_url = 'https://opensciencegrid.atlassian.net'

GET    = 'GET'
PUT    = 'PUT'
POST   = 'POST'
PATCH  = 'PATCH'
DELETE = 'DELETE'

class Options:
    authstr = None
    show_headers = False
    cookies = None

options = Options()


def add_json_header(req):
    req.add_header("Content-Type", "application/json")


def add_gzip_header(req):
    req.add_header("Accept-Encoding", "gzip")


def add_auth_header(req):
    if options.authstr:
        req.add_header("Authorization", "Basic %s" % options.authstr)


def add_cookie_header(req):
    url = req.get_full_url()
    if options.cookies:
        val = cookies.cookie_header_val(options.cookies, url)
        if val:
            req.add_header("Cookie", val)


def uri_ify(data):
    return '?' + '&'.join(map('='.join, sorted(data.items())))


def gunzip(data):
    import StringIO, gzip
    sio = StringIO.StringIO(data)
    return gzip.GzipFile(fileobj=sio).read()


def call_api(method, path, data):
    if data:
        if method == GET:
            path = path + uri_ify(data)
            data = None
        else:
            if isinstance(data, dict):
                data = json.dumps(data)

    url = jira_url + path

    req = urllib2.Request(url, data)
    add_auth_header(req)
    add_json_header(req)
    add_gzip_header(req)
    add_cookie_header(req)

    req.get_method = lambda : method
    resp = urllib2.urlopen(req)
    headers = resp.headers

    # in python 3.2:
    #    import gzip
    #    o = gzip.decompress(resp.read())

    #return url, headers, json.loads(resp.read())
    resp_data = resp.read()
    if headers.get('Content-Encoding') == 'gzip':
        resp_data = gunzip(resp_data)
    if headers.gettype() == 'application/json':
        resp_data = json.loads(resp_data)

    return url, headers, resp_data


def try_call_api(*a, **kw):
    try:
        return call_api(*a, **kw)
    except urllib2.HTTPError:
        return None, None, None


def auth_try_call_api(*a, **kw):
    if options.cookies:
        return try_call_api(*a, **kw)
    else:
        return None, None, None


def load_cached_issue(issue):
    fn = issue + ".json"
    if os.path.exists(fn):
        return json.load(open(fn))


def get_issue(issue, **kw):
    path = "/rest/api/2/issue/" + issue
    return call_api(GET, path, kw)


def get_user_issues(user, **kw):
    path = '/rest/api/2/search'
    e = easydict(dict(
        jql        = "assignee=%s+AND+status+!=+Closed" % user,
        maxResults = 100,
        **kw
    ))
    return try_call_api(GET, path, e)


def get_epic(issue, **kw):
    path = "/rest/agile/1.0/epic/" + issue
    return auth_try_call_api(GET, path, kw)


def get_epic_issues(issue, **kw):
    path = "/rest/agile/1.0/epic/%s/issue" % issue
    return auth_try_call_api(GET, path, kw)


def get_username(**kw):
    path = "/rest/auth/latest/session"
    url,h,j = auth_try_call_api(GET, path, kw)
    return j


def post_comment(issue, body):
    path = "/rest/api/2/issue/%s/comment" % issue
    data = {'body': body}
    return auth_try_call_api(POST, path, data)


def update_description(issue, body):
    path = "/rest/api/2/issue/%s/comment" % issue
    data = {"update": {"description": [{"set": body}]}}
    return auth_try_call_api(PUT, path, data)


def render_jira_markup(issue, jml):
    path = "/rest/api/1.0/render"
    data = {"rendererType"     : "atlassian-wiki-renderer",
            "unrenderedMarkup" : jml,
            "issueKey"         : issue}
    return try_call_api(POST, path, data)


def get_assignee_name(assignee):
    unassigned_html = "<span class='unas'>Unassigned</span>"
    return assignee.displayName if assignee else unassigned_html


_status_nicknames = {
    "Selected for Development" : "Slated",
    "In Progress"              : "Active",
    "Development Complete"     : "Dev Complete",
    "Ready for Testing"        : "RFT",
    "Ready for Release"        : "RFR",
}


def get_status_nick(name):
    return _status_nicknames.get(name, name)


def get_epic_issues_html(issue):
    url,h,j = get_epic_issues(issue, fields="summary,status,priority,assignee")
                                            #,issuetype
    if j:
        e = easydict(j)
        html = _issue_html_epic_links1
        for el in e.issues:
            el._assignee = get_assignee_name(el.fields.assignee)
            el._status = get_status_nick(el.fields.status.name)
            html += _issue_html_epic_links2.format(**el)
        html += _issue_html_epic_links3
        return html
    else:
        return ''


def add_issuelink_fields(ili, _type):
    ili._type = _type
    ili._status = get_status_nick(ili.fields.status.name)
    return _issue_html_links2.format(**ili)


def get_issuelinks_html(e):
    html = _issue_html_links1
    for il in e.fields.issuelinks:
        if 'outwardIssue' in il:
            html += add_issuelink_fields(il.outwardIssue, il.type.outward)
        if 'inwardIssue' in il:
            html += add_issuelink_fields(il.inwardIssue, il.type.inward)
    html += _issue_html_links3
    return html


def escape_html(txt, quot=False):
    txt = txt.replace('&', '&amp;')
    txt = txt.replace('<', '&lt;')
    txt = txt.replace('>', '&gt;')
    return txt


_issue_html1 = u"""\
<!DOCTYPE html>
<html>
<head>
<title>{key} : {_summary}</title>
<style>
  div   {{ max-width: 800px    }}
  table {{ text-align: left    }}
  .fr   {{ float: right        }}
  .nw   {{ white-space: nowrap }}
  .unas {{ opacity: 0.5; font-style: italic }}
  a.user-hover {{ text-decoration: underline }}
  table.coltab {{ font-family: monospace }}
  table.coltab th {{ padding-right: 1em }}

  a.nu         , a.nu2         {{ color: inherit             }}
  a.nu:link    , a.nu2:link    {{ text-decoration: none      }}
  a.nu:visited , a.nu2:visited {{ text-decoration: none      }}
  a.nu:hover                   {{ text-decoration: underline }}
  a.nu2:hover                  {{ text-decoration: none      }}

  .boxy {{ border-style: solid }}
  .boxy {{ border-width:  1px  }}
  .boxy {{ border-radius: 3px  }}
  .boxy {{ padding:   1px 4px  }}

  div.panelContent pre {{
    overflow-x: auto;
    overflow-y: auto;
    max-height: 400px;
    margin-left: 3em;
    padding: 1em;
    border: 1px dotted;
    border-radius: 3px;
  }}

  .zzzzz {{
    white-space: pre-wrap;
    padding-left: 3em;
    text-indent: -2em;
  }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
<h2>
{key} : {_summary}
</h2>

<div>
<table style='margin-left: 2em'>
<tr>

<td>
<table class='coltab'>

<tr>
<th>type</th>
<td>{fields.issuetype.name}</td>
</tr>

<tr>
<th>priority</th>
<td>{fields.priority.name}</td>
</tr>

<tr>
<th>components</th>
<td>{_components}</td>
</tr>

<tr>
<th>labels</th>
<td>{_labels}</td>
</tr>

<tr>
<th>epic link</th>
<td>{_epic}</td>
</tr>

<tr>
<th>sprint</th>
<td>{_sprint}</td>
</tr>
</table>
</td>

<td width='5%'> </td>

<td>

<table class='coltab'>
<tr>
<th>status</th>
<td>{fields.status.name}{_resolution}</td>
</tr>

<tr>
<th>fix verions</th>
<td>{_fixversions}</td>
</tr>

<tr>
<th>assignee</th>
<td>{_assignee}</td>
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
</table>

</td>
</tr>
</table>

</div>

<hr/>

<h3>Description</h3>

<div>
{renderedFields.description}
</div>

"""

_issue_html_links1 = """\
<hr/>

<h3>Issue Links</h3>

<table>
"""

_issue_html_links2 = """\
<tr>
<td class='nw'>{_type}:<td>
<th><a href="?issue={key}">{key}</a></th>
<td>|<td>
<td>{fields.priority.name}<td>
<td>|<td>
<td class='nw'>{_status}<td>
<td>|<td>
<td>{fields.summary}<td>
</tr>
"""

_issue_html_links3 = """\
</table>

<br/>

"""

_issue_html_epic_links1 = """\
<hr/>

<h3>Epic Links</h3>

<table>
"""

_issue_html_epic_links2 = """\
<tr>
<td>{_assignee}<td>
<td>|<td>
<th><a href="?issue={key}">{key}</a></th>
<td>|<td>
<td>{fields.priority.name}<td>
<td>|<td>
<td class='nw'>{_status}<td>
<td>|<td>
<td>{fields.summary}<td>
</tr>
"""

_issue_html_epic_links3 = """\
</table>

<br/>

"""

_issue_html_comments = """\
<hr/>

<h3>Comments ({fields.comment.total})</h3>

<div>

"""

_issue_html_comment = u"""\
<h4>
{created} | {author.displayName}
</h4>
<div>
{body}
</div>
<hr/>
"""

_issue_html3 = u"""\
</div>

</body>
</html>"""

_ignorepats = [
    ur' *<img .*?/>',
    ur' *<span [^>]*jira-macro-single-issue-export-pdf[^>]*>[^<]*</span>',
    ur'\s+(?=</a>)',
]

_subs = [
    (ur'<span class="jira-issue-macro[^>]*>\s*'
     ur'<a href="' + jira_url + ur'/browse/([A-Z]+-[0-9]+)"([^>]*)>'
     ur'\s*([^<]*)\s*</a>\s*</span>', ur'<a href="?issue=\1"\2>\3</a>'),
    (ur'<a href="[^"]*" class="user-hover" [^>]*>([^<]*)</a>',
     ur'<a class="user-hover">\1</a>'),
]

def names(seq):
    return ( x.name for x in seq )

def cjoin(seq):
    return u', '.join(seq)

def issue_key_link(issue, title=None, classes=None):
    attrs = ['href="?issue={issue}"']
    if classes:
        attrs += ['class="{classes}"']
    fmt = '<a %s>{title}</a>' % ' '.join(attrs)
    return fmt.format(issue=issue, title=title, classes=classes)


def get_epic_name(issue):
    if issue:
        url,h,j = get_epic(issue)
        title = easydict(j).name if j else issue
        return issue_key_link(issue, title, 'boxy nu2')
    else:
        return '-'


def issue_to_html(j):
    e = easydict(j)
    e._fixversions = cjoin(names(e.fields.fixVersions)) or '-'
    e._components  = cjoin(names(e.fields.components)) or '-'
    e._labels      = cjoin(e.fields.labels) or '-'
    e._summary     = escape_html(e.fields.summary)
    e._assignee    = get_assignee_name(e.fields.assignee)
    e._resolution  = ' / ' + e.fields.resolution.name if e.fields.resolution \
                                                      else ''
    e._epic        = get_epic_name(e.fields.customfield_10630)
    e._sprint      = cjoin(names(e.fields.customfield_10530 or [])) or '-'

    html = _issue_html1.format(**e)

    if e.fields.issuelinks:
        html += get_issuelinks_html(e)

    if e.fields.issuetype.name == 'Epic':
        html += get_epic_issues_html(e.key)

    # if e.fields.comment.total != len(e.renderedFields.comment.comments): ...
    html += _issue_html_comments.format(**e)
    for c in e.renderedFields.comment.comments:
        html += _issue_html_comment.format(**c)
    html += _issue_html3
    for pat in _ignorepats:
        html = re.sub(pat, u'', html)
    for pat, repl in _subs:
        html = re.sub(pat, repl, html)
    return html


_landing_html = u"""\
<!DOCTYPE html>
<html>
<body>
Try sticking a <code>?issue=SOFTWARE-4000</code> after the URL.
</body>
</html>"""
def landing_page():
    return _landing_html

def html_header():
    return "Content-Type: text/html; charset=utf-8\r\n\r"


def dump_issue_json(issue):
    url,h,j = get_issue(issue, expand='renderedFields')
    pp = json.dumps(j, sort_keys=1, indent=2)
#   print "Headers for <%s>" % url
#   print "---"
#   print h
#   print "---"
#   print
    print pp


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


def usage(msg=None):
    if msg:
        print >>sys.stderr, msg + "\n"

    s = os.path.basename(__file__)
    print _usage.format(script=s)
    sys.exit()


def main(args):
    if len(args) == 1:
        issue, = args
        if not re.match(r'^[A-Z]+-[0-9]+$', issue):
            usage("Bad ISSUE")
        dump_issue_json(issue)
        return

    if len(args) == 2 and args[0] == '--render':
        jml = args[1]
        issue = 'SOFTWARE-1234'  # arbitrarily
        url,h,html = render_jira_markup(issue, jml)
        print html
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

    j = load_cached_issue(params.issue)
    options.cookies = cookies.try_read_cookies('cookie.txt')
    if not j:
        url,h,j = get_issue(params.issue, expand='renderedFields')
    print html_header()
    print issue_to_html(j).encode("utf-8")


if __name__ == '__main__':
    main(sys.argv[1:])


