#!/usr/bin/python
# I think this tells the server where to find the interpreter for this script

"""
First created 16 Oct 15
This is my first (well new first - it's been a while) foray into cgi
cgi is the old fashioned (apparently php is more in vogue) but relatively simple way
to use a script in almost any sort of code to generate a viewable, functional html file.

For westValue, the goal would be to look up the resident's schedule and so pre-set
various parameters in Qualtrics. I think works as such:
 - Residents have a unique URL that bakes in a unique ID (maybe passes it as &ID=___)?
 - ID either is their Amion name or looks up their Amion name in a dictionary
 - Script then scrapes Amion for today's schedule & finds resident's rotation
   - Probably use Requests & Beautiful Soup to scrape & parse (cf Evernote Code)
     - If scraping doesn't work, could store the Amion source somewhere & the script can
       point to it & look up the schedule that way
 - Script then generates an auto-link to the resident's Qualtrics survey
   - This can then either customize the URL for Qualtrics 
     or just pass the rotation in the URL (&Rotation=___) for Qualtrics to embed
     
     
1. Getting my cgi primer from a nice, very basic tutorial: 
https://www.youtube.com/watch?v=Ct_aAWRcwdg

2. And then learning some from the Python tutorial:
http://anh.cs.luc.edu/python/hands-on/3.1/handsonHtml/dynamic.html
Looked cool but it uses python 3 which I don't know, am not sure I want to
learn & doesn't seem to be configured on my webhost (doesn't run even when
I use the code straight from the tutorial...

3. This tutorial has some simple stuff that may do the trick for me:
http://www.tutorialspoint.com/python/python_cgi_programming.htm
Includes using the GET method to grab variables from a URL!

"""

"""
Script guts mostly go here
"""

"""
Tutorial 3 says:
Here is a simple URL, which passes two values to hello_get.py program using GET method.
/cgi-bin/hello_get.py?first_name=ZARA&last_name=ALI

I'm adapting to a first version at least to get the Amion search query
testCGI2.py?resLName=Davis&resFIn=M
(I think the Davis-M used by Amion may break the URL with the '-'
"""

import cgi, cgitb

# Debugging - has the webserver print a traceback instead of just a page
# not found error if there's an error in the code
cgitb.enable()

# cgi.escape() I think this is a security feature to keep people from 
# entering code into input fields

# Create instance of FieldStorage
form = cgi.FieldStorage()

LName = form.getvalue('resLName') 
# Create a variable name that pulls the resLName from the URL
FIn = form.getvalue('resFIn') 

"""
HTML mostly goes here
"""

print "Content-type:text/html\r\n\r\n"
# Need this header to start off the html file
print "<html>"
print "<head>"
print "<title>westValue - CGI Test</title>"
print "</head>"
print "<body>"
print "Hello World"
print "<h2>Welcome %s-%s! Let us begin the scraping!</h2>" % (LName, FIn)
print "</body>"
print "</html>"