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

from cgix     import *
from easydict import easydict
from gzippy   import gunzip
import cookies

_usage = """\
# xxx: [PASS=...] {script} [-u USER[:PASS]] [-d passfd] [-H] COMMAND [args...]
usage: {script} ISSUE
   or: QUERY_STRING="issue=TICKET-NUM" {script}  # CGI
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


def call_api(method, path, data):
    if data:
        if method == GET:
            path = path + mk_query_string(data)
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
    try:
        resp = urllib2.urlopen(req)
    except urllib2.HTTPError as err:
        resp = err
    return resp


def get_resp_data(resp):
    data = resp.read()
    if resp.headers.get('Content-Encoding') == 'gzip':
        data = gunzip(data)
    if resp.headers.gettype() == 'application/json':
        data = easydict(json.loads(data))

    return data


def resp_ok(resp):
    return resp and not isinstance(resp, urllib2.HTTPError)


def resp_data_if_ok(resp):
    return get_resp_data(resp) if resp_ok(resp) else None


def auth_call_api(*a, **kw):
    return call_api(*a, **kw) if options.cookies else None


def load_cached_issue(issue):
    fn = issue + ".json"
    if os.path.exists(fn):
        return easydict(json.load(open(fn)))


def get_issue(issue, **kw):
    path = "/rest/api/2/issue/" + issue
    return call_api(GET, path, kw)


def get_user_issues(user, **kw):
    path = '/rest/api/2/search'
    e = easydict(
      # jql = "assignee=%s+AND+status+!=+Closed+AND+status+!=Done" % user,
        jql = "assignee=%s+AND+status+not+in+(Closed,+Done,+Abandoned)" % user,
        maxResults = 100,
        **kw
    )
    return call_api(GET, path, e)


def get_epic(issue, **kw):
    path = "/rest/agile/1.0/epic/" + issue
    return auth_call_api(GET, path, kw)


def get_epic_issues(issue, **kw):
    path = "/rest/agile/1.0/epic/%s/issue" % issue
    return auth_call_api(GET, path, kw)


def get_username(**kw):
    path = "/rest/auth/latest/session"
    resp = auth_call_api(GET, path, kw)
    return resp_data_if_ok(resp)


def get_users(query="", **kw):
    path = "https://opensciencegrid.atlassian.net/rest/api/3/user/search"
    kw = dict(query=query, **kw)
    resp = auth_call_api(GET, path, kw)
    return resp_data_if_ok(resp)


def post_comment(issue, body):
    path = "/rest/api/2/issue/%s/comment" % issue
    data = {'body': body}
    return auth_call_api(POST, path, data)


def update_description(issue, body):
    path = "/rest/api/2/issue/%s/comment" % issue
    data = {"update": {"description": [{"set": body}]}}
    return auth_call_api(PUT, path, data)


def render_jira_markup(issue, jml):
    path = "/rest/api/1.0/render"
    data = {"rendererType"     : "atlassian-wiki-renderer",
            "unrenderedMarkup" : jml,
            "issueKey"         : issue}
    return call_api(POST, path, data)


def get_assignee_name(assignee):
    unassigned_html = "<span class='unas'>Unassigned</span>"
    return assignee.displayName if assignee else unassigned_html


_status_nicknames = {
    "Selected for Development" : "Slated",
    "In Progress"              : "InProg",
    "Development Complete"     : "DevCmp",
    "Ready for Testing"        : "RFT",
    "Ready for Release"        : "RFR",
}

_backlog_statuses = ["Backlog", "Open", "To Do"]

def get_status_nick(name):
    return _status_nicknames.get(name, name)


def get_epic_issues_html(issue):
    resp = get_epic_issues(issue, fields="summary,status,priority,assignee")
                                            #,issuetype
    if resp_ok(resp):
        e = get_resp_data(resp)
        html = _issue_html_epic_links1
        for el in e.issues:
            el._assignee = get_assignee_name(el.fields.assignee)
            el._status = get_status_nick(el.fields.status.name)
            html += _issue_html_epic_links2.format(**el)
        html += _issue_html_epic_links3
        return html
    else:
        return ''


def add_user_issue_fields(isu):
    isu._status = get_status_nick(isu.fields.status.name)
    return _user_issue_html_links2.format(**isu)


def issuekey(issue):
    project, issuenum = issue.split('-')
    return project, int(issuenum)


def is_backlogged(x):
    return x.fields.status.name in _backlog_statuses

def user_issue_sortkey(x):
    return (-is_backlogged(x), -int(x.fields.priority.id), x.fields.status.id,
            issuekey(x.key))


def get_user_issues_html(user):
    resp = get_user_issues(user)
    e = get_resp_data(resp)

    html = _user_issue_html_links1.format(_user=user)
    for isu in sorted(e.issues, reverse=True, key=user_issue_sortkey):
        html += add_user_issue_fields(isu)
    html += _user_issue_html_links3

    return html



def get_add_comment_response_html(issue, body):
    resp = post_comment(issue, body)
    url = resp.geturl()
    resp_data = get_resp_data(resp)
    e = easydict()
    e._url = escape_html(url, quot=True)
    e._headers = escape_html(str(resp.headers))
    e._body = json.dumps(resp_data, sort_keys=1, indent=2)
    e._code = resp.getcode()
    e._msg = resp.msg
    e.key = issue
    return _post_response_html.format(**e)


def get_add_comment_html(params):
    e = easydict()
    e.key = params.comment
    e._summary = params.summary

    if params.jml and params.action == 'Add':
        return get_add_comment_response_html(e.key, params.jml)

    if params.jml:
        resp = render_jira_markup(e.key, params.jml)
        e._rendered = get_resp_data(resp)
        e._jml = escape_html(params.jml)
    else:
        e._rendered = ''
        e._jml = ''

    return _add_comment_html.format(**e)



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


_issue_html1 = u"""\
<!DOCTYPE html>
<html>
<head>
<title>{key} : {_summary}</title>
<style>
  body  {{ max-width:   800px  }}
  body  {{ margin-left:   3em  }}
  body  {{ margin-bottom: 3em  }}
  table {{ text-align: left    }}
  .fr   {{ float: right        }}
  .nw   {{ white-space: nowrap }}
  .unas {{ opacity: 0.5; font-style: italic }}
  a.user-hover {{ text-decoration: underline }}
  table.coltab {{ font-family: monospace }}
  table.coltab th {{ padding-right: 1em }}
  .confluenceTable, .confluenceTh, .confluenceTd {{
      border: 1px solid grey;
      border-collapse: collapse;
      padding: 2px 4px;
  }}

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

_issue_html_add_comment = u"""\
<form method="post" action="" target="_blank">
<input type="hidden" name="comment" value="{key}" />
<input type="hidden" name="summary" value="{_summary}" />
<input type="submit" value="Add Comment" />
</form>
"""

_issue_html3 = u"""\
</div>

</body>
</html>
"""




_user_issue_html_links1 = """\
<!DOCTYPE html>
<html>
<head>
<title>Issues for {_user}</title>
<style>
  table {{ text-align: left       }}
  table {{ font-family: monospace }}
  .nw   {{ white-space: nowrap    }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
<h3>
Issues for {_user}:
</h3>

<table>
"""

_user_issue_html_links2 = """\
<tr>
<td>{fields.priority.name}<td>
<td>|<td>
<td class='nw'>{_status}<td>
<td>|<td>
<th><a href="?issue={key}">{key}</a></th>
<td>:<td>
<td>{fields.summary}<td>
</tr>
"""

_user_issue_html_links3 = """\
</table>

</body>
</html>

"""


_add_comment_html = u"""\
<!DOCTYPE html>
<html>
<head>
<title>{key} :: Add Comment</title>
<style>
  body  {{ max-width:   800px  }}
  body  {{ margin-left:   3em  }}
  body  {{ margin-bottom: 3em  }}

  .rbox {{ max-width: 600px  }}
  .rbox {{ border: solid 1px }}
  .rbox {{ padding: .5em 1em }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>

<h2>
{key} : {_summary}
</h2>

<hr/>

<h3>Add Comment</h3>

<form id="cancelform" action="">
<input type="hidden" name="issue" value="{key}" />
</form>

<form method="post" action="">
<input type="hidden" name="comment" value="{key}" />
<input type="hidden" name="summary" value="{_summary}" />
<textarea id="jml_ta" name="jml" rows="20" cols="80">{_jml}</textarea>
<br/>
<input type="submit" name="action" value="Preview">
<input type="submit" name="action" value="Add">
<input type="submit" form="cancelform" value="Cancel" />
</form>

<hr/>

<h3>Preview</h3>

<div class='rbox'>
{_rendered}
</div>

</body>
</html>
"""


_post_response_html = u"""\
<html>
<head>
<title>POST response</title>
<style>
  .ms   {{ font-family: monospace }}
</style>
</head>
<body>
<h2 class="ms">{_code} {_msg}</h2>
<h3>POST response</h3>
<a href="{_url}">{_url}</a>
<br/>
<h4>Headers</h4>
<pre>{_headers}</pre>
<h4>Body</h4>
<pre>{_body}</pre>

<p>
Back to <a href="?issue={key}">{key}</a>
</p>
</body>
</html>
"""


_landing_html = u"""\
<!DOCTYPE html>
<html>
<head>
<title>jirunder-arrest!</title>
<style>
 .cen { text-align: center }
</style>
</head>
<body>

<h2>jirunder-arrest !</h2>

<form id="viewform" action=""></form>
<form id="userform" action=""></form>

<table>
<tr>
<td><label for="issue_tb">Issue Key:</label></td>
<td><input form="viewform" type="text" id="issue_tb" name="issue" /></td>
<td><input form="viewform" type="submit" value="View Issue" /></td>
</tr>
<tr><td class="cen">or</td></tr>
<tr>
<td><label for="user_tb">Username:</label></td>
<td><input form="userform" type="text" id="user_tb" name="user" /></td>
<td><input form="userform" type="submit" value="Get Issues" /></td>
</tr>
</table>

</body>
</html>
"""



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
        resp = get_epic(issue)
        title = get_resp_data(resp).name if resp_ok(resp) else issue
        return issue_key_link(issue, title, 'boxy nu2')
    else:
        return '-'


def issue_to_html(e):
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
    html += _issue_html_add_comment.format(**e)
    html += _issue_html3
    for pat in _ignorepats:
        html = re.sub(pat, u'', html)
    for pat, repl in _subs:
        html = re.sub(pat, repl, html)
    return html


def get_issue_html(issue):
    e = load_cached_issue(issue)
    if not e:
        resp = get_issue(issue, expand='renderedFields')
        e = get_resp_data(resp)
    return issue_to_html(e)


def landing_page():
    return _landing_html

def dump_issue_json(issue):
    resp = get_issue(issue, expand='renderedFields')
    e = get_resp_data(resp)
    pp = json.dumps(e, sort_keys=1, indent=2)
#   print "Headers for <%s>" % resp.geturl()
#   print "---"
#   print resp.headers
#   print "---"
#   print
    print pp


def usage(msg=None):
    if msg:
        print >>sys.stderr, msg + "\n"

    s = os.path.basename(__file__)
    print _usage.format(script=s)
    sys.exit()


def get_cgi_html(params):
    if not params:
        return landing_page()

    elif params.comment:
        return get_add_comment_html(params)

    elif params.user:
        return get_user_issues_html(params.user)

    elif params.issue:
        return get_issue_html(params.issue)

    else:
        # nothing interesting was requested
        return landing_page()


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
        resp = render_jira_markup(issue, jml)
        html = get_resp_data(resp)
        print html
        return

    if args:
        usage("Extra arg")

    if 'QUERY_STRING' not in os.environ:
        usage("Missing QUERY_STRING")

    params = get_params()

    options.cookies = cookies.try_read_cookies('cookie.txt')
    send_data(get_cgi_html(params))


if __name__ == '__main__':
    main(sys.argv[1:])


