#! /usr/bin/python26

"""
First started 20 Oct 15
by Michael Scahill, mdscahill@gmail.com
Part of the "West-Value" consulting project to develop an alternative to eValue using
Qualtrics.
This code is hoped to scrape Amion for rotation info that can be fed into the westValue
cgi portal and thence into Qualtrics.

The general flow:

 - resident has a custom link to cgi portal that includes their Amion name (or some code
 that corresponds to it in a dict or something)
 - cgi feeds that code into scraper which uses probably Requests
 - scraper logs into amion.com using pw = ucsfpeds
 - scraper finds resident's name in the html, uses regex to find the rotation next to
 their name
 - rotation, or a corresponding code stored in dict, is output into a url that gets
 fed into Qualtrics
 - need some sort of fallback where a blank/generic rotation code is fed to Qualtrics if
 there is an error or the scraper can't find the rotation
   - this will happen whenever: resident is not on that day (weekend evaluation entry) or
   if there's any change to the Amion format.
     - Could be issues in years to come when the rotation codes get changed around. May
     want to develop a small set of "rotation buckets" - wards, ER, ICU, outpt, primary -
     that the scraper actually feeds to Qualtrics. Can then group the many amion codes
     (PURPLE1-Day, -Nite...) into corresponding clinical contexts.

Major Versions:
This is a continuation / summation of qualcgi1 & scraper4.

Scraper Versions:
v1 - get the amion login working using Requests
v2 - get Beautiful Soup + Regex to pull out the actual rotation
v3 - Planned to merge with qualcgi but ended up being a clean up of old regex experiments. v2
     has a bunch of failed tinkerings with notes. v3 cleans them out.
     v3 then gets the regex to work on both rotation & resident then figures out how to combine
     them.
     At first, combined them as tupules -> dict but this had issues.
     Switched to list of lists. v3 archives these experiments.
v4 - Clears out the tupule, dict experiments. Start cleaning the rotation & resident text of
     extraneous crap.
     The Amion target in html and other reference data are kept here, cleared out for the
     summation into qualCGIscrape1

qualCGIscrape
v1 - merge qualcgi1 with scraper into effectively the finished product. Produces basic html with
a custom Qualtrics link.
v2 - realized that passing rotation & milestone into Qualtrics then confirming it there would
be a nightmare. v2 starts the re-work to confirm that in CGI interface & pass a definitive
rotation & milestone group to Qualtrics. Started 12nov15
v3 - realized that coding the mapping of milestone groups to EPA into Qualtrics
would also be a nightmare especially if it changes. (This is the matrix of EPAs
& milestones with X in cells that Dan created for Mike in early Nov15.)
Qualtrics could perhaps handle this with JS but seemed simpler to select an
EPA here in the CGI with a second page. Thus, v3 changes the links from Qualtrics
to this new, second CGI selection page called EPApicker.py
"""

"""
Resources:
Tutorial 1: https://www.youtube.com/watch?v=eRSJSKG4mDA
The actual documentation: http://docs.python-requests.org/en/latest/user/quickstart/

"""

"""
What I'm working on - the Amion HTML stuff:

Truncated, the full detail is still in scraper4
-------------------------------
	<form name=AmionLogin action="cgi-bin/ocs" method=post>

These are the login network data:
---------------------------------
General:
Remote Address:204.10.66.120:80
Request URL:http://amion.com/cgi-bin/ocs
Request Method:POST
Status Code:200 OK

Form Data:
Login:ucsfpeds

"""


#################################################################################
#####   CGI Setup
#####   from the qualcgi1.py file. Put this first so you capture errors
#################################################################################

import cgi, cgitb
# Debugging - has the webserver print a traceback instead of just a page
# not found error if there's an error in the code
cgitb.enable()

# cgi.escape() I think this is a security feature to keep people from
# entering code into input fields

#==================================================================================
import requests
import re
import csv
# import os, sys


"""
The URL into this needs:
?AmionL=__&AmionF=__&FName=__&pgy=__&qualID=__
http://pediatricly.com/cgi-bin/westValue/qualCGIscrape3.py?AmionL=Neely&AmionF=J&FName=Jessica&pgy=3&qualID=temp
"""
"""
Hiding these for local debugging:
"""
# Create instance of FieldStorage
form = cgi.FieldStorage()


# Get names from the URL
LName = form.getvalue('AmionL')
AmionF = form.getvalue('AmionF')
AmionName = LName + '-' + AmionF
pgy = form.getvalue('pgy')
FName = form.getvalue('FName')

# Store the Qualtrics link custom suffix
qualID = form.getvalue('qualID')

"""
LName = "Neely"
AmionF = "J"
AmionName = LName + '-' + AmionF
pgy = 3
FName = "Jessica"
"""

# Temporary measure to get the old Qualtrics link going, careful, this overwrites the URL input
qualID = "SE?Q_DL=4NiHEv4rRV75KUR_2rxLPgxEvdzAXOJ_MLRP_4IUOlBssXvaqJ8h&Q_CHL=gl"

# Pre-set the Qualtrics url base
EPApicker = 'http://www.pediatricly.com/cgi-bin/westValue/EPApicker.py' # It looks like the base could be longer but
# keeping it short seems safer

fieldnames = ['AmionRot', 'cleanRotName', 'Milestone Map Label']

###################################################################
### Read the CSV list from active dir
### This should contain Amion rotation slots in first column, conventional rotation name in second
### and the critical milestone / EPA code in the third
###################################################################

rotationsDict = {}
csvIn = 'rotationsIn.csv'

with open(csvIn, 'rb') as csvfile:
	csvreader = csv.reader(csvfile, quotechar=' ')
	for row in csvreader:
		if row[0] != '':
			if row[0] != fieldnames[0]: # Strip out the header row
				rotationsDict[row[0]] = (row[1], row[2])
	# print "Read the initial " + csvIn + "into rotationsDict"

rotsForLinksDict = {}
for rotation in rotationsDict:
	tupule = rotationsDict[rotation]
	rotsForLinksDict[tupule[0]] = tupule[1]

cccMilestone = 'CCC' # Remembers the milestone group name for continuity clinic

# These lines then look up the "pretty" rotation name for continuity clinic
# One could probably just hardcode this, but this way the code is robust as long as CCC
# doesn't change
cccName = ''
for rotation in rotsForLinksDict:
	if rotsForLinksDict[rotation] == cccMilestone: cccName = rotation

#################################################################################
#####   Scraper Module
##### Look up the schedule in Amion and put rotations in a list
#################################################################################

AmionLogin = {"login" : "ucsfpeds"}
r = requests.post("http://amion.com/cgi-bin/ocs", data=AmionLogin)
# print(r.text) # This is outputting the html of the actual schedule landing page
html = r.content # And this stores that html as a string

resRotList = []

fullTable1 = re.findall("^<TR><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
fullTable2 = re.findall("^<TR class=grbg><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
fullTable3 = re.findall("^<TR><td></font><font color=#\w\w\w\w\w\w>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)

listofTables = [fullTable1, fullTable2, fullTable3]
for subTable in listofTables:
	for rotation, resident in subTable:
		rotation = re.sub(r'&nbsp;', '', rotation)
		resident = re.sub(r'[=\*]', '', resident)
		tempList = [rotation, resident]
		resRotList.append(tempList)

###################################################################
### Setup the Qulatrics URL generation
###################################################################
def urlGen(base, stubList, rot2, milestone2, suffix):
# Loop to format the URL with form data 'url?varName=_var_&var2=_var2_'
	dataList = []
	for item in stubList:
		dataList.append(item)
	dataList.append(rot2)
	dataList.append(milestone2)

	for urlVar, varName in dataList:
		# print urlVar
		suffix = suffix + urlVar + '=' + str(varName) + '&'

	if suffix[-1] == '&': suffix = suffix[:-1] # Clip off the last &
	urlOut = base + suffix # Assemble the final custom Qualtrics URL
	return urlOut

urlBase = EPApicker
urlSuffix = '?'
rotDataListStub = ([['LName', LName], ['FName', FName], ['pgy', pgy],
                    ['qualID', qualID]])

currRot = 'Other' # Initialize in the global namespace



###################################################################
### New Rotation confirm functions
###################################################################
"""
OK, this needs a whole new & exciting feature set for v2
Realized that Qualtrics will get very cumbersome if it has to confirm the rotation look up
& EPA/milestone grouping. Going to do that here so that it's in one place; this way Qualtrics
can "trust" the rotation & EPA group that come from CGI.
This upgrades this CGI script from basically a silent auto-link into some actual dynamic html.

In more detail, to do:
	- This link was customized for _ resident, if this is for someone else, click here for
	landingPage.html (needs to be built with links back into qualCGI for qResident)
	- Change here is your link to "Amion says you are on __ today. If that's the rotation
	for eval, click here (same URL as in v1)
	- "If not, here is a table of other rotations, starting with CoC, to go into Qualtrics
	for those. This will need a for loop through the rotations dict + CoC

"""

###################################################################
### HTML Starts Here
###################################################################

print "Content-type:text/html\r\n\r\n"
# Need this header to start off the html file
print "<html>"
print "<head>"
print "<title>westValue - Feedback Portal for %s %s</title>" % (FName, LName)
"""
Now that there are a few pages to be made (this, admin, landingpage...) will want a css
"""

print "</head>"
print "<body>"

###################################################################
### Match the resident from URL to rotation in Amion, output URL to Qualtrics with EPA
###################################################################
print """
<h1>Welcome to westValue!</h1>
<p>The new, coolest things in medical training feedback are <a href="https://www.abp.org/entrustable-professional-activities-epas">Entrustable Professional Activities (EPAs)</a>. 17 EPAs cover broad domains of pediatrics. E.g., EPA #3 is "care of the well newborn". The idea is that trainees gradually learn to be entrusted with all these activities independently. westValue uses <i>very short</i> Qualtrics surveys to track trainee progress.</p>
"""

print "<h2>Right Resident?</h2>"
print "<p> It is, of course, critical to have the right resident. Qualtrics links on this page have been customized for <b>%s %s</b>.<br>" % (FName, LName)
print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If that is whom you want to evaluate, great! Please proceed.<br>"
print '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If you are looking for another trainee, please go to the <a href="http://www.pediatricly.com/cgi-bin/westValue/landingpage.html">Landing Page</a></p>'

print "<h2>Right Rotation?</h2>"
print "<p>We have customized Qualtrics links by rotation for 2 reasons.<br>"
print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;First, we want residents to know in what setting feedback was received.<br>"
print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Second, we want residents to get feedback spread across all the EPAs while making it very easy for you to pick a relevant one. (e..g, EPA 3 for Well Baby but not Adol.)</p>"

print "<p>westValue is now looking up the good Doctor %s's schedule in Amion...</p>" % LName
print "<h3>Today's Rotation</h3>"
try:
	for resRotPair in resRotList:
		# print resRotPair
		if AmionName == resRotPair[1]:
			currRot = resRotPair[0]
	currTupule = rotationsDict[currRot]
	currRotName = currTupule[0]
	currMilestone = currTupule[1]

	currRotUrl = urlGen(urlBase, rotDataListStub, ['Rotation', currRotName],
		['Milestone', currMilestone], urlSuffix)

	print 'Amion lists %s on <b>%s</b> today.' % (FName, currRotName)
	print ('<b>To give feedback for %s <a href ="%s">click here to enter Qualtrics</a><br></b>'
			% (currRotName, currRotUrl))
	print currRotUrl + '<br>'
except:
	print ("Sorry! Amion does't have %s listed today. (This happens on days off, electives, etc.) But fear not!<br>") % FName

# Start with a prominent CoC link.
print "<h3>Continuity Clinic</h3>"
cccUrl = urlGen(urlBase, rotDataListStub, ['Rotation', cccName],
		['Milestone', cccMilestone], urlSuffix)
print 'Click here if this is feedback from <a href ="%s">Continuity Clinic</a>' % cccUrl

# Loop through dict of (Pretty Name, Milestone) to output links for all the rotations in csv
print "<h3>Other Rotations</h3>"
print "Here are the all the other rotations for feedback:<br>"
print '(Remember, all these are specific for %s %s)<br>' % (FName, LName)

for rotation in sorted(rotsForLinksDict):
	# print 'Rotation: "%s" Milestone: "%s" <br>' % (rotation, rotsForLinksDict[rotation])
	rotUrl = urlGen(urlBase, rotDataListStub, ['Rotation', rotation],
		['Milestone', rotsForLinksDict[rotation]], urlSuffix)
	print '<a href ="%s">%s</a><br>' % (rotUrl, rotation)
print "</body>"
print "</html>"





"""
Stored for potential offline use:
listofListsStore = [['KW&nbsp;Int-Short&nbsp;', 'Guslits-E='], ['KN Call&nbsp;', 'Harper-L'], ['RedBMT-Nite&nbsp;', 'Knappe-A*'], ['PICU-Day&nbsp;', 'Bent-M'], ['PICU Nite&nbsp;', 'Maurer-L'], ['ICN Int-Short&nbsp;', 'Caffarelli-M'], ['ICN Sr-Bridge Long', 'Wu-L*'], ['ICN Sr-Short&nbsp;', 'Truong-B='], ['Pacific Sr-Nite&nbsp;', 'Ort-K'], ['SFO-Int&nbsp;Swing&nbsp;', 'Iacopetti-C'], ['SFO-SCR&nbsp;', 'LaRocca-T='], ['SFO-Sr Day&nbsp;', 'Davenport-J'], ['SFO-Sr Nite&nbsp;', 'FP2: DeMarchis-Emilia'], ['SFN-Int Day&nbsp;', 'FP1: Gomez, Teresa'], ['SFGH-Sr Nite', 'Balkin-E='], ['SFW-Int Day&nbsp;', 'FP1: Cuervo, Catalina'], ['CHO 7a-4p', 'Sofia Kerbawy'], ['CHO&nbsp;3p-12a', 'Armando Huaringa'], ['CHO&nbsp;6p-3a', 'Callie Titcomb'], ['CHO&nbsp;10p-7a', 'UCSF Vaisberg'], ['TCU-Day', 'Hammoudi-T'], ['TCU-ID', 'Vinh-L*'], ['WB', 'Yang-E='], ['KW2&nbsp;', 'Links-B*'], ['BMT&nbsp;', 'Johnson-Kerner-B'], ['PICU-Day', 'Crouch-E='], ['PICU-Day', 'Neely-J'], ['UCW3-Nite&nbsp;', 'Goudy-B='], ['ICN Int-Short', 'Singal-P'], ['ICN Sr-Long&nbsp;', 'Brajkovic-I='], ['ICN Sr-Short&nbsp;', 'Laguna-M'], ['SFO-Int Day', 'EM1: Padrez-Kevin'], ['SFO-Int Nite', 'Spiegel-E'], ['SFO-Sr Day&nbsp;', 'Sundby-T'], ['SFO-Sr Swing&nbsp;', 'FP3: Chang, Steven'], ['SFN Sr Day&nbsp;', 'Thompson-D'], ['SFN-Int Day', 'Nash-D'], ['SFW R2 Day&nbsp;', 'Boddupalli-G'], ['SFGH-Int Nite&nbsp;', 'Wohlford-E'], ['CHO&nbsp;3p-12a', 'Scott Sutton'], ['CHO&nbsp;3p-12a', 'Betty Shum'], ['CHO&nbsp;10p-7a', 'Ruchi Punatar'], ['TCU-Day', 'Kodali-S'], ['TCU-Nite', 'Keller-S='], ['WB', 'Chen-D*'], ['RED', 'Braun-L='], ['PURPLE1-Day', 'Schwartz-R'], ['PURPLE1-Nite&nbsp;', 'Simmons-R'], ['ORANGE1-Day&nbsp;', 'Burnett-H='], ['ORANGE1-Day', 'Argueza-B*'], ['ORANGE3-Day&nbsp;', 'Pantell-M*']]

"""














#End
