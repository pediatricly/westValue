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
v4 - Replaces the messy series of print statements with a long templated string
to write the html more cleanly. The html is edited & copied from
portalHTMLtemplate_fromCGI.html (done in a .html to use color-cued editing)

portal
v4 - 2dec15 - identical to qualCGIscrape4, just a name change fork
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
import os.path
from string import Template
# import os, sys


###################################################################
### Define Globals Before Main try block
###################################
try: version = os.path.basename(__file__)
except: version = 'portal4'

# Temporary measure to get the old Qualtrics link going, careful, this overwrites the URL input
# qualID = "SE?Q_DL=4NiHEv4rRV75KUR_2rxLPgxEvdzAXOJ_MLRP_4IUOlBssXvaqJ8h&Q_CHL=gl"

EPApicker = 'http://www.pediatricly.com/cgi-bin/westValue/EPApicker2.py'
ResDirectory = 'http://www.pediatricly.com/cgi-bin/westValue/ResidentDirectory.py'

fieldnames = ['AmionRot', 'cleanRotName', 'Milestone Map Label']

cccMilestone = 'CCC' # Remembers the milestone group name for continuity clinic
rotationsDict = {}

rotsForLinksDict = {}

cccName = ''

resRotList = []

cssSheet = 'http://www.pediatricly.com/westVal/WVmain.css'
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
#####################################################################

"""
The URL into this needs:
?AmionL=__&AmionF=__&FName=__&pgy=__&qualID=__
http://pediatricly.com/cgi-bin/westValue/portal4.py?AmionL=Neely&AmionF=J&FName=Jessica&pgy=3&qualID=temp
"""
"""
Hiding these for local debugging:
"""
# Create instance of FieldStorage
form = cgi.FieldStorage()


# Get names from the URL
try:
    LName = form.getvalue('AmionL')
    # except: LName = None
    AmionF = form.getvalue('AmionF')
    #except: AmionF = None
    pgy = form.getvalue('pgy')
    #except: pgy = None
    FName = form.getvalue('FName')
    #FName = None

    # Store the Qualtrics link custom suffix
    qualID = form.getvalue('qualID')
    #except: qualID = None
    if LName == None or AmionF == None or FName == None:
        raise NameError
    cgiError = 0

    """
    LName = "Neely"
    AmionF = "J"
    AmionName = LName + '-' + AmionF
    pgy = 3
    FName = "Jessica"
    """

###################################################################
### Read the CSV list from active dir
### This should contain Amion rotation slots in first column, conventional rotation name in second
### and the critical milestone / EPA code in the third
###################################################################

    csvIn = 'rotationsIn.csv'

    with open(csvIn, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, quotechar=' ')
        for row in csvreader:
            if row[0] != '':
                if row[0] != fieldnames[0]: # Strip out the header row
                    rotationsDict[row[0]] = (row[1], row[2])
        # print "Read the initial " + csvIn + "into rotationsDict"

    for rotation in rotationsDict:
        tupule = rotationsDict[rotation]
        rotsForLinksDict[tupule[0]] = tupule[1]


# These lines then look up the "pretty" rotation name for continuity clinic
# One could probably just hardcode this, but this way the code is robust as long as CCC
# doesn't change
    for rotation in rotsForLinksDict:
        if rotsForLinksDict[rotation] == cccMilestone: cccName = rotation

#################################################################################
#####   Scraper Module
##### Look up the schedule in Amion and put rotations in a list
#################################################################################

    try:
        AmionLogin = {"login" : "ucsfpeds"}
        r = requests.post("http://amion.com/cgi-bin/ocs", data=AmionLogin)
# print(r.text) # This is outputting the html of the actual schedule landing page
        html = r.content # And this stores that html as a string

        fullTable1 = re.findall("^<TR><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
        fullTable2 = re.findall("^<TR class=grbg><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
        fullTable3 = re.findall("^<TR><td></font><font color=#\w\w\w\w\w\w>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)

        listofTables = [fullTable1, fullTable2, fullTable3]
        for subTable in listofTables:
            for rotation, resident in subTable:
                rotation = re.sub(r'&nbsp;', '', rotation)
                resident = re.sub(r'[=\*\+]', '', resident)
                tempList = [rotation, resident]
                resRotList.append(tempList)
    except: pass

    urlBase = EPApicker
    urlSuffix = '?'
    rotDataListStub = ([['LName', LName], ['FName', FName], ['pgy', pgy],
                        ['qualID', qualID]])

    currRot = 'Other' # Initialize in the global namespace



###################################################################
### Build String Variables to Write HTML
###################################################################


# Set these locally for html debugging:
# currRotName = "Well_Baby"
# currMilestone = "NNN"

###################################################################
### Match the resident from URL to rotation in Amion, output URL to EPApicker
###################################################################

# Build the html string for current rotation lookup
    currRotHTML = ""
    currRotName = ""
    currMilestone = "Unknown"

    AmionName = LName + '-' + AmionF
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

        currRotHTML += 'Amion lists %s on <strong>%s</strong> today.<br>\n' % (FName, currRotName)
        currRotHTML += ('<ul><li><b>To give feedback for %s <a href ="%s">click here to pick an EPA</a></li></ul></b>\n'
                % (currRotName, currRotUrl))
        # currRotHTML += currRotUrl + '<br>\n' #This is temp output just for debugging
    except:
        currRotHTML += ("Sorry! Amion does't have %s listed today. (This happens on days off, electives, etc.) But fear not!<br>\n") % FName


# Build the current & CoC urls
    currRotUrl = urlGen(urlBase, rotDataListStub, ['Rotation', currRotName],
    ['Milestone', currMilestone], urlSuffix)
    cccUrl = urlGen(urlBase, rotDataListStub, ['Rotation', cccName],
            ['Milestone', cccMilestone], urlSuffix)

# Create a long html-format string of the other (non-current/CoC) links
    otherRotLinks = ""
    for rotation in sorted(rotsForLinksDict):
        # print 'Rotation: "%s" Milestone: "%s" <br>' % (rotation, rotsForLinksDict[rotation])
        if rotation != cccName and rotation != currRotName:
            rotUrl = urlGen(urlBase, rotDataListStub, ['Rotation', rotation],
                ['Milestone', rotsForLinksDict[rotation]], urlSuffix)
            otherRotLinks += '<li><a href ="%s">%s</a></li>\n' % (rotUrl, rotation)

###################################################################
### Use the string.Template to store custom HTML as a big string
###################################################################
    templateFH = open('portalHTMLtemplate.html', 'r')
    htmlTemplate = templateFH.read()

    templateVars = dict(cssSheet=cssSheet, FName=FName, LName=LName,
                        currRotName=currRotName, currRotUrl=currRotUrl,
                        cccUrl=cccUrl, otherRotLinks=otherRotLinks,
                        currRotHTML=currRotHTML, version=version,
                        ResDirectory=ResDirectory)

    finalHTML = Template(htmlTemplate).safe_substitute(templateVars)

# Save for local debugging, not CGI
# outfile2 =  open("wvHTML/cgiPortal_templated.html", 'w')
# outfile2.write(finalHTML)

###################################################################
### For CGI, print the final templated HTML
###################################################################

    print "Content-type:text/html\r\n\r\n"
# Need this header to start off the html file in CGI (not when saving html)

    print finalHTML


except NameError:
    cgiError = 1

    cgiErrTemplateFH = open('portalCGIerrTemplate.html', 'r')
    cgiErrTemplate = cgiErrTemplateFH.read()
    print "Content-type:text/html\r\n\r\n"
    print Template(cgiErrTemplate).safe_substitute(version=version,
                                                   cssSheet=cssSheet,
                                                   ResDirectory=ResDirectory)











    """
    Stored for potential offline use:
    listofListsStore = [['KW&nbsp;Int-Short&nbsp;', 'Guslits-E='], ['KN Call&nbsp;', 'Harper-L'], ['RedBMT-Nite&nbsp;', 'Knappe-A*'], ['PICU-Day&nbsp;', 'Bent-M'], ['PICU Nite&nbsp;', 'Maurer-L'], ['ICN Int-Short&nbsp;', 'Caffarelli-M'], ['ICN Sr-Bridge Long', 'Wu-L*'], ['ICN Sr-Short&nbsp;', 'Truong-B='], ['Pacific Sr-Nite&nbsp;', 'Ort-K'], ['SFO-Int&nbsp;Swing&nbsp;', 'Iacopetti-C'], ['SFO-SCR&nbsp;', 'LaRocca-T='], ['SFO-Sr Day&nbsp;', 'Davenport-J'], ['SFO-Sr Nite&nbsp;', 'FP2: DeMarchis-Emilia'], ['SFN-Int Day&nbsp;', 'FP1: Gomez, Teresa'], ['SFGH-Sr Nite', 'Balkin-E='], ['SFW-Int Day&nbsp;', 'FP1: Cuervo, Catalina'], ['CHO 7a-4p', 'Sofia Kerbawy'], ['CHO&nbsp;3p-12a', 'Armando Huaringa'], ['CHO&nbsp;6p-3a', 'Callie Titcomb'], ['CHO&nbsp;10p-7a', 'UCSF Vaisberg'], ['TCU-Day', 'Hammoudi-T'], ['TCU-ID', 'Vinh-L*'], ['WB', 'Yang-E='], ['KW2&nbsp;', 'Links-B*'], ['BMT&nbsp;', 'Johnson-Kerner-B'], ['PICU-Day', 'Crouch-E='], ['PICU-Day', 'Neely-J'], ['UCW3-Nite&nbsp;', 'Goudy-B='], ['ICN Int-Short', 'Singal-P'], ['ICN Sr-Long&nbsp;', 'Brajkovic-I='], ['ICN Sr-Short&nbsp;', 'Laguna-M'], ['SFO-Int Day', 'EM1: Padrez-Kevin'], ['SFO-Int Nite', 'Spiegel-E'], ['SFO-Sr Day&nbsp;', 'Sundby-T'], ['SFO-Sr Swing&nbsp;', 'FP3: Chang, Steven'], ['SFN Sr Day&nbsp;', 'Thompson-D'], ['SFN-Int Day', 'Nash-D'], ['SFW R2 Day&nbsp;', 'Boddupalli-G'], ['SFGH-Int Nite&nbsp;', 'Wohlford-E'], ['CHO&nbsp;3p-12a', 'Scott Sutton'], ['CHO&nbsp;3p-12a', 'Betty Shum'], ['CHO&nbsp;10p-7a', 'Ruchi Punatar'], ['TCU-Day', 'Kodali-S'], ['TCU-Nite', 'Keller-S='], ['WB', 'Chen-D*'], ['RED', 'Braun-L='], ['PURPLE1-Day', 'Schwartz-R'], ['PURPLE1-Nite&nbsp;', 'Simmons-R'], ['ORANGE1-Day&nbsp;', 'Burnett-H='], ['ORANGE1-Day', 'Argueza-B*'], ['ORANGE3-Day&nbsp;', 'Pantell-M*']]

    """









#End
