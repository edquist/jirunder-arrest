#!/usr/bin/python

import json
import jirunder_arrest
j = json.load(open("SOFTWARE-4210.json"))
h = jirunder_arrest.issue_to_html(j)
w = open("o2.html","w")
print >>w, h.encode("utf-8")
w.close()

