#!usr/bin/python26

"""
First started 4 Nov 15
by Michael Scahill, mdscahill@gmail.com
Part of the "West-Value" consulting project to develop an alternative to eValue using
Qualtrics.
This code is hoped to scrape Amion for the list of rotation names. Those names can then be matched
to the 'milestones' that then map to EPAs for Qualtrics. 

The general flow:

 - Look for a csv or txt file that contains the working version of the rotationsDict
 - Scrape Amion (ideally over a week) to grab all the active rotation names
 - Output a new csv or txt file that adds in any Amion names that weren't in the original so they
can be filled in (probably manually)

Major Versions:
v1 - Adapted from scraper4 to get the rotation names
v2 - Finished the dict work & just cleaned out some old stuff (lists & holdovers from scraper)
"""


"""
What I'm working on - the Amion HTML stuff:

The login page looks like this:
-------------------------------
<table cellspacing=0 cellpadding=0 border=0><tr>
	<td width=350 style='padding-left:20;'><img border=0 src="../oci/banner_logo.gif" width=289 height=42></td>
	<td>
	<table width=250 cellspacing=0 cellpadding=0 border=0><tr>
		<form name=AmionLogin action="cgi-bin/ocs" method=post>
		<td align=right style="padding-right:10;">
		<input type=text maxlength=28 name=Login size=18 style="border: 1px solid #90ff90;"><input type=submit class=button value=" Login " style="width:72px; height:23px;"></td>
		</form>

These are the login network data:
---------------------------------
General:
Remote Address:204.10.66.120:80
Request URL:http://amion.com/cgi-bin/ocs
Request Method:POST
Status Code:200 OK

Response Headers:
Connection:Keep-Alive
Content-Length:51276
Content-Type:text/html
Date:Tue, 20 Oct 2015 22:34:40 GMT
Keep-Alive:timeout=3, max=100
Server:Apache
X-Powered-By:PleskLin
X-Robots-Tag:noindex, nofollow, noarchive

Request Headers:
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:en-US,en;q=0.8,es;q=0.6
Cache-Control:max-age=0
Connection:keep-alive
Content-Length:14
Content-Type:application/x-www-form-urlencoded
Host:amion.com
Origin:http://amion.com
Referer:http://amion.com/
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36

Form Data:
Login:ucsfpeds


The target code of the actual schedule looks like this in html 
(around line 258 in the amion code):
------------------------------------
<TR><td>KW&nbsp;Int-Short&nbsp;<IMG SRC="../oci/pnohu4.gif" WIDTH=13 HEIGHT=13 BORDER=0 
TITLE="8:00a to 5:00p"></TD><td >&nbsp;</td><td><a class=plain 
href='./ocs?Fi=!527189calwaudangbu&Ps=134&Ui=15*3407*
Guslits-E=&Mo=10-15&Sbcid=6'><b><nobr>Guslits-E=</b></a></TD>
<td >&nbsp;</td><td class=gr>R1</TD><td class=gr><x>

CAREFUL that the last row of the table starts:
<TR class=grbg><td>WB
as opposed to the standard <TR><td> above
"""

#==================================================================================

import requests
import re
import csv
import os

# listofLists = [] # This gathers [rotation, resident] in a big list of lists from all the Amion
# line formats
# This is a holdover from scraper.py, probably don't need it in admin.

# AmRotationList = [] # This is a list of strings with just the rotation names.

fieldnames = ['AmionRot', 'cleanRotName', 'Milestone Map Label']
###################################################################
### Read whatever CSV list is in active dir
###################################################################

# rotationsInList = []
rotationsDict = {}
csvIn = 'rotationsIn.csv'

with open(csvIn, 'rb') as csvfile:
	csvreader = csv.reader(csvfile, quotechar=' ')
	for row in csvreader:
		if row[0] != '':
			if row[0] != fieldnames[0]: 
				rotationsDict[row[0]] = (row[1], row[2])
				# rotationsInList.append(row[0:3])
	print "Read the initial " + csvIn + "into rotationsDict"

###################################################################
### Look up the schedule in Amion and put rotations in a list
###################################################################

payload = {"login" : "ucsfpeds"}
r = requests.post("http://amion.com/cgi-bin/ocs", data=payload)
# print(r.text) # This is outputting the html of the actual schedule landing page
html = r.content # And this stores that html as a string

newRotations = []

# soup = BeautifulSoup(r.content)
# Ended up not using BeautifulSoup


"""
These re.findall statements search the html of the Amion landing page & pull out a list of 
rotation, resident pairs from the day's call schedule.
There are 3 of them because there are 3 different ways the call schedule is written in HTML 
depending on the text color & whether that red diamond icon is next to the name (not even sure
what that damn icon means).
"""
fullTable1 = re.findall("^<TR><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
fullTable2 = re.findall("^<TR class=grbg><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
fullTable3 = re.findall("^<TR><td></font><font color=#\w\w\w\w\w\w>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
#---------------------------------------------------------


"""
This loop puts those 3 findall results into 1 big list of the day's call schedule. It also trims
out some of the garbage text from the html.
In the admin.py version, it also updates the dict of rotation names so the master rotation : 
milestone / EPA map can be updated.
"""

listofTables = [fullTable1, fullTable2, fullTable3]
for subTable in listofTables:
	for rotation, resident in subTable:
		rotation = re.sub(r'&nbsp;', '', rotation)
		# resident = re.sub(r'[=\*]', '', resident)
		# tempList = [rotation, resident]
		# listofLists.append(tempList)
		if rotation not in rotationsDict:
			rotationsDict[rotation] = ('', '') 
			# Add rotations in Amion not in the initial csv to the dict
			# This happens with changes to the block schedule & on days when the 
			# long / short shifts are different from whenever the initial list made
			newRotations.append(rotation)
			# Note a list of these new rotations
		# AmRotationList.append(rotation)

print ("Looked up today's Amion & added " + str(len(newRotations)) + " new rotation slot names")

###################################################################
### Write the list to CSV
'''
I tried using csv.DictWriter for this but it was cumbersome with value = tupule
Works fine using normal csv.writer with a loop to open up the tupules.
'''
###################################################################

csvOut = 'rotationsOut.csv'

with open(csvOut, 'wb') as csvfile:
	writer = csv.writer(csvfile)
	writer.writerow(fieldnames)
	for key in sorted(rotationsDict.keys()):
		tupule = rotationsDict[key]
		row = [key, tupule[0], tupule[1]]
		writer.writerow(row)
	if len(newRotations) > 0:
		print "Wrote these new rotation slot names to " + csvOut
		print ("Check " + str(os.getcwd()) + 
		""" and fill in the full names & EPA milestones for these new rotation slots. Then save as rotationsIn.csv & upload back to that directory""")
	else: print "No new rotation slots in Amion today. You're all set."











#End
