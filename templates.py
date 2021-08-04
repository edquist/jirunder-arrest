#!/usr/bin/python


homerow = u"""\
<div class="homerow">
<a href="." class="hbb nu2">home</a> |
<a href="?login=please" class="hbb nu2">login</a>
</div>
"""

user_homerow = u"""\
<div class="homerow">
<a href="." class="hbb nu2">home</a> |
<a href="?user={_userid}" class="hbb nu2 nw">my issues</a> |
<a href="?login=please" class="hbb nu2">login</a>
</div>
"""

issue_html1 = u"""\
<!DOCTYPE html>
<html>
<head>
<title>{key} : {_summary}</title>
<link rel="stylesheet" type="text/css" href="main.css" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
{_homerow}
<hr/>
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
<td>{_status}</td>
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

<div class="desc">
{renderedFields.description}
</div>

"""

issue_html_links1 = """\
<hr/>

<h3>Issue Links</h3>

<table class="ilt">
"""

issue_html_links2 = """\
<tr>
<td class='nw sml'>{_type}:<td>
<th class='nw'><a href="?issue={key}">{key}</a></th>
<td>|<td>
<td>{fields.priority.name}<td>
<td>|<td>
<td class='nw'>{_status}<td>
<td>|<td>
<td>{fields.summary}<td>
</tr>
"""

issue_html_links3 = """\
</table>

<br/>

"""

issue_html_epic_links1 = """\
<hr/>

<h3>Epic Links</h3>

<table>
"""

issue_html_epic_links2 = """\
<tr>
<td>{_assignee}<td>
<td>|<td>
<th class='nw'><a href="?issue={key}">{key}</a></th>
<td>|<td>
<td>{fields.priority.name}<td>
<td>|<td>
<td class='nw'>{_status}<td>
<td>|<td>
<td>{fields.summary}<td>
</tr>
"""

issue_html_epic_links3 = """\
</table>

<br/>

"""

issue_html_comments = """\
<hr/>

<h3>Comments ({fields.comment.total})</h3>

<div>

"""

issue_html_comment = u"""\
<h4>
{created} | {author.displayName}
</h4>
<div class="comm">
{body}
</div>
<hr/>
"""

issue_html_add_comment = u"""\
<form method="post" action="" target="_blank">
<input type="hidden" name="comment" value="{key}" />
<input type="hidden" name="summary" value="{_summary}" />
<input type="submit" value="Add Comment" class="acb" />
</form>
"""

issue_html3 = u"""\
</div>

</body>
</html>
"""

issue_status_button = u"""\
<form method="post" action="">
<input type="hidden" name="transition" value="{key}" />
<input type="hidden" name="status" value="{_status}" />
<input type="hidden" name="summary" value="{_summary}" />
<input type="submit" value="{_status}" class="hbb" />
</form>
"""



user_issue_html_links1 = """\
<!DOCTYPE html>
<html>
<head>
<title>Issues for {_user}</title>
<link rel="stylesheet" type="text/css" href="main.css" />
<style>
  table {{ text-align: left       }}
  table {{ font-family: monospace }}
  .nw   {{ white-space: nowrap    }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
{_homerow}
<hr/>

<h3>
Issues for {_user}:
</h3>

<table>
"""

user_issue_html_links2 = """\
<tr>
<td>{fields.priority.name}<td>
<td>|<td>
<td class='nw'>{_status}<td>
<td>|<td>
<th class='nw'><a href="?issue={key}">{key}</a></th>
<td>:<td>
<td>{fields.summary}<td>
</tr>
"""

user_issue_html_links3 = """\
</table>

</body>
</html>

"""


add_comment_html = u"""\
<!DOCTYPE html>
<html>
<head>
<title>{key} :: Add Comment</title>
<link rel="stylesheet" type="text/css" href="main.css" />
<style>
  .rbox {{ max-width: 600px  }}
  .rbox {{ border: solid 1px }}
  .rbox {{ padding: .5em 1em }}

  .inh {{
    border-color: inherit;
    background-color: inherit;
    color: inherit;
  }}
  .btn {{
    padding: .5em 1em;
  }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
{_homerow}
<hr/>

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
<textarea id="jml_ta" name="jml" rows="20" cols="80" class="inh">\
{_jml}\
</textarea>

<p>
<input type="submit" class="inh btn" name="action" value="Preview" />
<input type="submit" class="inh btn" name="action" value="Add" />
<input type="submit" class="inh btn" form="cancelform" value="Cancel" />
</p>

</form>

<p>
<label for="users_i">@ user:</label>
<input list="users_dl" id="users_i" class="inh" />
<datalist id="users_dl">
{_user_lookup}
</datalist>
</p>


<hr/>

<h3>Preview</h3>

<div class='{_rbox}'>
{_rendered}
</div>

</body>
</html>
"""


user_lookup_option = u"""\
<option>[{name}|~accountid:{id}]</option>
"""


user_select_option = u"""\
<option value="{id}" {_selected}>{name}</option>
"""

user_select = u"""\
<select form="userform" id="user_tb" name="user" >
<option value="" disabled {_none_selected}>Select User</option>
{_user_select_options}
</select>
"""


issue_transition = u"""\
<!DOCTYPE html>
<html>
<head>
<title>{key} :: Workflow Transition</title>
<link rel="stylesheet" type="text/css" href="main.css" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
{_homerow}
<hr/>

<h2>
{key} : {_summary}
</h2>

<h3>[ {_status} ]</h3>

<p>Transition:</p>

<form method="post" action="">
<input type="hidden" name="transition" value="{key}" />
<p>
{_transition_radios}
</p>
<p>
<input type="submit" value="Go!" />
</p>
</form>

</body>
</html>
"""

issue_transition_radio = u"""\
<input type="radio" id="{id}" name="transition_id" value="{id}" />
<label for="{id}">{name}</label><br/>
"""


post_response_html = u"""\
<!DOCTYPE html>
<html>
<head>
<title>POST response</title>
<style>
  .ms   {{ font-family: monospace }}
</style>
</head>
<body>
<h2 class="ms">{_code} {_msg}</h2>

<p>
Back to <a href="?issue={key}">{key}</a>
</p>

<h3>POST response</h3>
<a href="{_url}">{_url}</a>
<br/>
<h4>Headers</h4>
<pre>{_headers}</pre>
<h4>Body</h4>
<pre>{_body}</pre>
</body>
</html>
"""


error_page_html = u"""\
<!DOCTYPE html>
<html>
<head>
<title>Error: {_code} {_msg}</title>
<style>
  .ms   {{ font-family: monospace }}
</style>
</head>
<body>

<h2 class="ms">Error: {_code} {_msg}</h2>

<pre>
{_emsgs}
</pre>

<h4>API URL</h4>
<pre>
{_url}
</pre>

<h4>Response</h4>
<pre>{_body}</pre>

<h4>Headers</h4>
<pre>{_headers}</pre>

</body>
</html>
"""


landing_html = u"""\
<!DOCTYPE html>
<html>
<head>
<title>jirunder-arrest!</title>
<link rel="stylesheet" type="text/css" href="main.css" />
<style>
 .cen {{ text-align: center }}
</style>
</head>
<body>
{_homerow}
<hr/>

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
<td class="cen"><label for="user_tb">User:</label></td>
<td>
{_user_select}
</td>
<td><input form="userform" type="submit" value="Get Issues" /></td>
</tr>
</table>

<p>
...
</p>

<p>
<a href="?login=please">Cookie Login</a>
</p>
</body>
</html>
"""

cookies_required_html = u"""\
<!DOCTYPE html>
<html>
<body>
Fail: cookies required
</body>
</html>
"""

login_extrahelp = u"""
<p class="sml">
Auth is required for editing jira issues, adding comments, and a couple other
things like listing "epic links".  Otherwise most read-only actions work
without auth.
</p>
<p class="sml">
This site uses the cloud.session.token cookie for atlassian.net
in order to make authenticated jira api calls.  This lets you piggy-back
off your existing jira login without having to enter a password here.
(And without this site having to implement oauth, with all the hoops
atlassian makes you do to get an api token.)
</p>
<p class="sml">
By pasting your cloud.session.token below and clicking Set Cookie,
this site will instruct your browser to use your cookie for
the current <a href=".">site</a> (as a session cookie, or, at your option,
as a persistent cookie until it expires).  This site does not save or track
your cookie or session information; it only forwards the cookie you provide
to jira when making api calls, while generating cgi pages.
</p>
<p class="sml">
To obtain your <tt>cloud.session.token</tt> cookie:
</p>
<p class="sml">
<em>In Firefox:</em>
</p>
<ul class="sml">
  <li>Log in to <a href="{_jira}/login">jira</a></li>
  <li>Open the Storage Inspector (Shift+F9)</li>
  <li>Expand "Cookies" and find the entry for your jira domain<br/>
      ({_jira})</li>
  <li>Locate the cookie with the Name "cloud.session.token"</li>
  <li>Double-click the Value, and copy it (Ctrl+C)</li>
  <li>Return to this page and paste into the text area below</li>
  <li>Click the Set Cookie button</li>
</ul>

<p class="sml">
<em>In Chromium / Chrome:</em>
</p>
<ul class="sml">
  <li>Log in to <a href="{_jira}/login">jira</a></li>
  <li>Open the cookie settings in a new tab (chrome://settings/cookies)</li>
  <li>Under "Site", find "atlassian.net" (you can also Search for it)</li>
  <li>Click to expand the row for "atlassian.net"</li>
  <li>Click the cookie for "cloud.session.token"</li>
  <li>Select the value next to Content, and copy it (Ctrl+C)</li>
  <li>Return to this page and paste into the text area below</li>
  <li>Click the Set Cookie button</li>
</ul>
"""

login_page = u"""\
<!DOCTYPE html>
<html>
<head>
<title>Cookie Mon Star :: Login</title>
<link rel="stylesheet" type="text/css" href="main.css" />
<style>
  .btt  {{ font-family: monospace }}
  .btt  {{ font-weight: bold      }}

  .sml  {{ font-size: small }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
{_homerow}
<hr/>

<h2>C is for Cookie</h2>

<h3>That's good enough for me.</h3>

<hr/>

<p class="sml">
(log in to <a href="{_jira}/login">jira</a>,
copy your cloud.session.token cookie for atlassian.net from your browser,
and paste it here)
&nbsp;
(<a href="?login=help" class="nu"><em>what?!</em></a>)
</p>

{_extrahelp}

<p class="btt">cloud.session.token:</p>

<form method="post" action="">
<p>
<textarea id="token_ta" name="token" rows="15" cols="80">{_token}</textarea>
</p>
<p>

<input type="radio" id="session_radio" name="expiry" value="session" />
<label for="session_radio">Session-only</label><br/>
<input type="radio" id="persist_radio" name="expiry" value="persist" checked />
<label for="persist_radio">Persist until expiry {_expiry_date}</label><br/>

</p>

<p>
<input type="submit" value="Set Cookie" />
</p>
</form>

</body>
</html>
"""

