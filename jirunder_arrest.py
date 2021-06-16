#!/usr/bin/python

import os
import re
import sys
import json
# import getopt
# import getpass
import urllib2
import operator
# import subprocess

from cgix     import *
from easydict import easydict, easydict_av
from gzippy   import gunzip
import cookies
import templates

_usage = """\
usage: {script} ISSUE
   or: QUERY_STRING="issue=TICKET-NUM" {script}  # CGI
"""

jira_url = 'https://opensciencegrid.atlassian.net'

cook_key = "cloud.session.token"

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


def package_request_data(method, path, data):
    if data:
        if method == GET:
            path = path + mk_query_string(data)
            data = None
        else:
            if isinstance(data, dict):
                data = json.dumps(data)
    return path, data


def mk_request(method, path, data):
    url = jira_url + path

    req = urllib2.Request(url, data)
    add_auth_header(req)
    add_json_header(req)
    add_gzip_header(req)
    add_cookie_header(req)

    req.get_method = lambda : method

    return req


def call_api(method, path, data):
    path, data = package_request_data(method, path, data)

    req = mk_request(method, path, data)

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
        data = easydict(json.loads(data)) if data else None

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
        jql = "assignee=%s+AND+statusCategory+!=+Done" % user,
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
    path = "/rest/api/3/user/search"
    maxResults=200
    kw = dict(query=query, maxResults=maxResults, **kw)
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


def get_transitions(issue, **kw):
    path = "/rest/api/2/issue/%s/transitions" % issue
    # can: expand=transitions.fields for field transitions
    return call_api(GET, path, kw)


def post_transition(issue, transition_id, **kw):
    path = "/rest/api/2/issue/%s/transitions" % issue
    e = easydict_av()
    e.transition.id = str(transition_id)
    e.update(kw)
    return call_api(POST, path, e)


def get_assignee_name(assignee):
    unassigned_html = "<span class='unas'>Unassigned</span>"
    return assignee.displayName if assignee else unassigned_html


_status_nicknames = {
    "Selected for Development" : "Slated",
    "In Progress"              : "InProg",
    "Development Complete"     : "DevCmp",
    "Ready for Testing"        : "RFT",
    "Ready for Release"        : "RFR",
    "Review Code"              : "Review",
}


def get_status_nick(name):
    return _status_nicknames.get(name, name)


def get_transition_issue_html(issue, status, summary):
    resp = get_transitions(issue)
    if not resp_ok(resp):
        return templates.cookies_required_html  # well, maybe other errors
    e = get_resp_data(resp)
    e.key = issue
    e._summary = summary
    e._status = status
    e._transition_radios = "".join(
        templates.issue_transition_radio.format(**t) for t in e.transitions )
    return templates.issue_transition.format(**e)


def get_transition_issue_html__params(p):
    issue = p.transition
    if p.transition_id:
        return get_transition_issue_response_html(issue, p.transition_id)
    else:
        return get_transition_issue_html(issue, p.status, p.summary)


def get_transition_issue_response_html(issue, transition_id):
    resp = post_transition(issue, transition_id)
    return get_post_response_html(issue, resp)


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


def user_issue_sortkey(x):
    return (x.fields.status.statusCategory.id, -int(x.fields.priority.id),
            x.fields.status.id, issuekey(x.key))


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
    return get_post_response_html(issue, resp)


def get_post_response_html(issue, resp):
    if resp_ok(resp):
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
    elif resp:
        return get_error_page_html(resp)
    else:
        return templates.cookies_required_html


_user_lookup_json = "user-lookup.json"
def get_user_lookup():
    lookup = json.load(open(_user_lookup_json))
    items = sorted(lookup.items(), key=operator.itemgetter(1))
    return [ {'id': k, 'name': v} for k,v in items ]


def update_user_lookup():
    try:
        w = open(_user_lookup_json, "w")
        d = { u.accountId: u.displayName for u in get_users()
              if u.accountType == 'atlassian' }
        print >>w, json.dumps(d, sort_keys=True, indent=2)
    except IOError:
        pass


def get_user_lookup_options_html():
    uu = get_user_lookup()
    return ''.join( templates.user_lookup_option.format(**u) for u in uu )


def get_add_comment_html(params):
    e = easydict()
    e.key = params.comment
    e._summary = params.summary

    if params.jml and params.action == 'Add':
        return get_add_comment_response_html(e.key, params.jml)

    e._user_lookup = get_user_lookup_options_html()

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
        return issue_key_link(issue, title, 'boxy nu2 nw')
    else:
        return '-'


def set_fancy_issue_status(e):
    res = e.fields.resolution
    e._resolution  = ' / ' + res.name if res else ''
    e._status = "{fields.status.name}{_resolution}".format(**e)
    if options.cookies:
        e._status = templates.issue_status_button.format(**e)


def issue_to_html(e):
    e._fixversions = cjoin(names(e.fields.fixVersions)) or '-'
    e._components  = cjoin(names(e.fields.components)) or '-'
    e._labels      = cjoin(e.fields.labels) or '-'
    e._summary     = escape_html(e.fields.summary)
    e._assignee    = get_assignee_name(e.fields.assignee)
    e._epic        = get_epic_name(e.fields.customfield_10630)
    e._sprint      = cjoin(names(e.fields.customfield_10530 or [])) or '-'

    set_fancy_issue_status(e)

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


def get_error_page_html(resp):
    if not resp:
        return templates.cookies_required_html

    url = resp.geturl()
    body = get_resp_data(resp)
    e = easydict()
    e._url     = escape_html(url, quot=True)
    e._headers = escape_html(str(resp.headers))
    e._body    = json.dumps(body, sort_keys=1, indent=2)
    e._code    = resp.getcode()
    e._msg     = resp.msg
    e._emsgs   = "\n".join(body.errorMessages or [])

    return templates.error_page_html.format(**e)


def get_issue_html(issue):
    e = load_cached_issue(issue)
    if not e:
        resp = get_issue(issue, expand='renderedFields')
        if not resp_ok(resp):
            return get_error_page_html(resp)
        e = get_resp_data(resp)
    return issue_to_html(e)


def landing_page():
    return templates.landing_html.format()


def login_page(params):
    e = easydict()
    e._token = escape_html(params.token) if params.token else ''
    html = templates.login_page.format(**e)

    secure = not served_over_localhost()

    if params.token:
        hdr = cookies.set_cookie_header(cook_key, params.token, secure=secure)
        # XXX: path=...
        return hdr, html
    else:
        return html


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
    if   not params        : return landing_page()
    elif params.login      : return login_page(params)
    elif params.comment    : return get_add_comment_html(params)
    elif params.transition : return get_transition_issue_html__params(params)
    elif params.user       : return get_user_issues_html(params.user)
    elif params.issue      : return get_issue_html(params.issue)
    else                   : return landing_page()


def mk_jira_cookie(name, value):
    return cookies.Cookie(
        domain     = cookies.urlparse(jira_url).domain
      , subdomains = False
      , path       = '/'
      , https_only = True
      , expires    = 0
      , name       = name
      , value      = value
    )


def load_cookies():
    options.cookies = cookies.try_read_cookies('cookie.txt')

    c = get_cgi_cookies()
    if cook_key in c:
        options.cookies = [mk_jira_cookie(cook_key, c[cook_key])]


def go_CGI():
    params = get_params()

    load_cookies()
    send_data(get_cgi_html(params))


def go_ISSUE(issue):
    if not re.match(r'^[A-Z]+-[0-9]+$', issue):
        usage("Bad ISSUE: '%s'" % issue)
    dump_issue_json(issue)

def go_RENDER(jml):
    issue = 'SOFTWARE-1234'  # arbitrarily
    resp = render_jira_markup(issue, jml)
    html = get_resp_data(resp)
    print html


def main(args):
    if 'QUERY_STRING' in os.environ:
        go_CGI()

    elif len(args) == 1:
        go_ISSUE(args[0])

    elif len(args) == 2 and args[0] == '--render':
        go_RENDER(args[1])

    elif args:
        usage("Extra arg")

    else:
        usage("Missing QUERY_STRING")


if __name__ == '__main__':
    main(sys.argv[1:])


