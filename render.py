#!/usr/bin/python

import sys

import jirunder_arrest
from jirunder_arrest import easydict, escape_html, html_header

from jirunder_arrest import render_jira_markup, parse_request_uri

_render_test_html = u"""\
<!DOCTYPE html>
<html>
<head>
<title>jirunder-arrest - Render Test</title>
<style>
  .rbox {{ max-width: 600px  }}
  .rbox {{ border: solid 1px }}
  .rbox {{ padding: 1em      }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>

<form action="">
<label for="jml_ta">JIRA Markup Text:</label>
<br/>
<textarea id="jml_ta" name="jml" rows="24" cols="80">{_jml}</textarea>
<br/>
<input type="submit" value="Preview">
</form>

<hr/>

<div class='rbox'>
{_rendered}
</div>

</body>
</html>"""


def get_render_page_html(jml):
    e = easydict({})
    if jml:
        issue = 'SOFTWARE-1234'  # arbitrarily
        url,h,e._rendered = render_jira_markup(issue, jml)
        e._jml = escape_html(jml)
    else:
        e._rendered = ''
        e._jml = ''

    return _render_test_html.format(**e)


def main(args):
    uri, params = parse_request_uri()
    jml = params and params.get('jml')
    print html_header()
    print get_render_page_html(params and params.get('jml'))

if __name__ == '__main__':
    main(sys.argv[1:])


