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
import templates

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
        html = templates.issue_html_epic_links1
        for el in e.issues:
            el._assignee = get_assignee_name(el.fields.assignee)
            el._status = get_status_nick(el.fields.status.name)
            html += templates.issue_html_epic_links2.format(**el)
        html += templates.issue_html_epic_links3
        return html
    else:
        return ''


def add_user_issue_fields(isu):
    isu._status = get_status_nick(isu.fields.status.name)
    return templates.user_issue_html_links2.format(**isu)


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

    html = templates.user_issue_html_links1.format(_user=user)
    for isu in sorted(e.issues, reverse=True, key=user_issue_sortkey):
        html += add_user_issue_fields(isu)
    html += templates.user_issue_html_links3

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
    return templates.post_response_html.format(**e)


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

    return templates.add_comment_html.format(**e)



def add_issuelink_fields(ili, _type):
    ili._type = _type
    ili._status = get_status_nick(ili.fields.status.name)
    return templates.issue_html_links2.format(**ili)


def get_issuelinks_html(e):
    html = templates.issue_html_links1
    for il in e.fields.issuelinks:
        if 'outwardIssue' in il:
            html += add_issuelink_fields(il.outwardIssue, il.type.outward)
        if 'inwardIssue' in il:
            html += add_issuelink_fields(il.inwardIssue, il.type.inward)
    html += templates.issue_html_links3
    return html




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

    html = templates.issue_html1.format(**e)

    if e.fields.issuelinks:
        html += get_issuelinks_html(e)

    if e.fields.issuetype.name == 'Epic':
        html += get_epic_issues_html(e.key)

    # if e.fields.comment.total != len(e.renderedFields.comment.comments): ...
    html += templates.issue_html_comments.format(**e)
    for c in e.renderedFields.comment.comments:
        html += templates.issue_html_comment.format(**c)
    html += templates.issue_html_add_comment.format(**e)
    html += templates.issue_html3
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
    return templates.landing_html

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


