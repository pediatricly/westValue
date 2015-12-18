#! /usr/bin/python26

"""
Requests Tester
A mini script to experiment with getting the damn import functions to work on pediatricly's cgi-bin

"""
import sys
import cgi, cgitb
# Debugging - has the webserver print a traceback instead of just a page
# not found error if there's an error in the code
cgitb.enable()

# cgi.escape() I think this is a security feature to keep people from 
# entering code into input fields

import requests
payload = {"login" : "ucsfpeds"}
r = requests.post("http://amion.com/cgi-bin/ocs", data=payload)
html = r.text # This is outputting the html of the actual schedule landing page

"""
HTML mostly goes here
"""

print "Content-type:text/html\r\n\r\n"
# Need this header to start off the html file
print "<html>"
print "<head>"
print "<title>westValue - Requests Import Tester</title>"
print "</head>"
print "<body>"
print "Hello World"
print """
Here is your link: <br>
"""
print html
print sys.path
print "</body>"
print "</html>"

