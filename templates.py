#!/usr/bin/python


issue_html1 = u"""\
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

issue_html_links1 = """\
<hr/>

<h3>Issue Links</h3>

<table>
"""

issue_html_links2 = """\
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
<th><a href="?issue={key}">{key}</a></th>
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
<div>
{body}
</div>
<hr/>
"""

issue_html_add_comment = u"""\
<form method="post" action="" target="_blank">
<input type="hidden" name="comment" value="{key}" />
<input type="hidden" name="summary" value="{_summary}" />
<input type="submit" value="Add Comment" />
</form>
"""

issue_html3 = u"""\
</div>

</body>
</html>
"""




user_issue_html_links1 = """\
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

user_issue_html_links2 = """\
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


post_response_html = u"""\
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


error_page_html = u"""\
<html>
<head>
<title>ERROR</title>
<style>
  .ms   {{ font-family: monospace }}
</style>
</head>
<body>

<h2 class="ms">{_code} {_msg}</h2>

<p>
API URL: {_url}
</p>

<h4>Headers</h4>
<pre>{_headers}</pre>

<h4>Response</h4>
<pre>{_body}</pre>

</body>
</html>
"""


landing_html = u"""\
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

cookies_required_html = u"""\
<html>
<body>
Fail: cookies required
</body>
</html>
"""


