#! /usr/bin/python26

"""
EPApicker is the 2nd CGI page of the westValue system. The planned flow is:
    - Custom resident links lands at portal (aka qualCGIscraper)
    - Resident & rotation confirmed there, piped via URL to EPApicker
    - EPA picker shows suggested EPAs by rotation (read from Milestone_Map.csv)
    - EPA picker presents custom Qualtrics survey links that pipe in all that
    info including the critical EPA# to Qualtrics
    - Qualtrics then shows just the question block for that EPA and stores the
    resident name, rotation

Major versions:
v1 - 18nov15 - first pass, built in a day that created the functional html
v2 - 2dec15 - Had just switched portal v4 to an html string.Template. This does
the same and brings the html up to speed with semantic tags & css link
As of 11dec15, adds failsafe so the full list of EPAs is displayed if Milestone
isn't found in Milestone_Map. (This was briefly called EPApicker3 but changed
back to v2 to spare the links.)

"""

#''' #Comment out this line to turnon CGI
################################################################################
#####   CGI Setup
#####   from the qualcgi1.py file. Put this first so you capture errors
################################################################################
import cgi, cgitb
# Debugging - has the webserver print a traceback instead of just a page
# not found error if there's an error in the code
cgitb.enable()

# cgi.escape() I think this is a security feature to keep people from
# entering code into input fields
# Create instance of FieldStorage
form = cgi.FieldStorage()
#''' #Comment out this line to turnon CGI
#===============================================================================
import csv
import os.path
import urllib
from string import Template

try: version = os.path.basename(__file__)
except: version = 'EPApicker2'

###################################################################
### Define Globals Before Main try block
####################################################################

# Pre-set the Qualtrics url base
qualBase = 'https://ucsf.co1.qualtrics.com/SE/'
ResDirectory = 'http://www.pediatricly.com/cgi-bin/westValue/ResidentDirectory.py'
portal = 'http://www.pediatricly.com/cgi-bin/westValue/portal4.py'
cssSheet = 'http://www.pediatricly.com/westVal/WVmain.css'
title = 'The EPA Selector'
frameHTML = 'frame.html'
mainTemplate = 'EPApickerHTMLtemplate.html'
"""
The URL into this needs:
?Rotation=__&Milestone=__&LName=__&FName=__&pgy=__&qualID=__
http://pediatricly.com/cgi-bin/westValue/EPApicker2.py?Rotation=TCU&Milestone=TCU&LName=Neely&FName=Jessica&pgy=3&qualID=temp
# Hiding these for local debugging:
"""

###################################################################
### Try to read from CGI, give brief error HTML way at bottom if fail
####################################################################

try:
# Indent de-indent starting this line to turn off the CGI try
# Get names from the URL. These are set in portal#.py
    #''' #Comment this section to turn off CGI
    AmionName = form.getvalue('AmionName')
    LName = form.getvalue('LName')
    FName = form.getvalue('FName')
    pgy = form.getvalue('pgy')
    Rotation = form.getvalue('Rotation')
    Milestone = form.getvalue('Milestone')

# Store the Qualtrics link custom suffix
    qualID = form.getvalue('qualID')
    #''' #Comment this section to turn off CGI

    """
    AmionName = 'Neely-J'
    LName = "Neely"
    pgy = 3
    FName = "Jessica"
    Rotation = "SFN3"
    Milestone = "SFN3"
    qualID = "SV_8CwPK9m2RELdyS1"
    """

    if LName == None or qualID == None or FName == None or Rotation == None or Milestone == None:
        raise NameError

    residentD = {'SID' : qualID, 'AmionName' : AmionName, 'LName' : LName, 'FName' : FName,
                'pgy' : pgy, 'Rotation' : Rotation}
    backD = {'AmionName' : AmionName, 'qualID' : qualID}
    linkBack = portal + '?' + urllib.urlencode(backD)

###################################################################
### Read the CSV mapping of milestones to EPA from active dir
###################################################################
    milestonesList = []
# Holds all the Milestone rows with X for relevant EPAs
    headers = []
# First row of the Milestone_Map:
# ['Milestone Map Label', 'GROUP', 'EPA1',...]
    csvIn = 'Milestone_Map.csv'
    with open(csvIn, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, quotechar='"')
        #quotechar sets the char Python uses to ignore commas within a cell
        #This has been troublesome with Excel which hides a seemingly random
        #selection of '" around such cells. Might be an easier solution.
        #But I tried using | to no avail
        for row in csvreader:
            milestonesList.append(row)
            if row[0] == 'Milestone Map Label': headers = row

    '''
    print "milestonesList:"
    print milestonesList
    print "headers:"
    print headers
    '''

    headedMilestones = [] # This is the row from Milestone_Map for CGI Milestone
# List of lists corresponding to the row of blanks & Xs from Milestone_Map for
# the CGI milestone:
# [['Milestone Map Label', 'SFN3'], ['GROUP', '3'], ['EPA1', ''], ['EPA2', ''],
# ['EPA3', 'X'],...]
    for row in milestonesList:
        if row[0] == Milestone:
            for i, cell in enumerate(row):
                # print i
                mini = [headers[i], cell]
                headedMilestones.append(mini)
    '''
    print "headedMilestones: "
    print headedMilestones
    '''

    descriptionList = []
# List of lists with EPA # string & description string
# [['1', "Provide consult...'], ['2', 'Provide rec...]]
    csvIn2 = 'EPA_descriptions.csv'
    with open(csvIn2, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, quotechar='"')
        for row in csvreader:
            if row[0] != 'EPA Number':
                descriptionList.append(row)


    activeEPAs = []
# List ['3', '4'...] of active EPA numbers
    csvIn3 = 'activeEPAs.csv'
    with open(csvIn3, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, quotechar='"')
        for row in csvreader:
            if row[1] == 'X' or row[1] == 'x':
                activeEPAs.append(row[0])

    epaList = []
# This is the list of suggested EPAs based on CGI Milestone var
# ['3', '5', '15',...]
    for row in headedMilestones:
        if row[1] == 'X' or row[1] == 'x':
            epaNum = row[0]
            epaNum = epaNum[3:]
            if epaNum in activeEPAs:
                epaList.append(epaNum)
    '''
    print "epaList:"
    print epaList
    '''

###################################################################
### Build String Variables to Write HTML
###################################################################

    suggestEPAurlHTML = ""
    restEPAurlHTML = ""

# Build HTML for the suggested EPAs using epaList
    for epa in epaList:
        description = ''
        for item in descriptionList:
            if item[0] == epa:
                description = item[1]
        residentD1 = residentD
        residentD1['EPA'] = epa
        epaUrl =  qualBase + '?' + urllib.urlencode(residentD1)
        suggestEPAurlHTML += '<li><a href="%s">EPA #%s: %s</a></li>' % (epaUrl, epa, description)

# Build HTML for the rest of the active EPAs using activeEPAs
    for epa in activeEPAs:
        if epa not in epaList:
            description = ''
            for item in descriptionList:
                if item[0] == epa:
                    description = item[1]
            residentD1 = residentD
            residentD1['EPA'] = epa
            epaUrl =  qualBase + '?' + urllib.urlencode(residentD1)
            restEPAurlHTML += '<li><a href="%s">EPA #%s: %s</a></li>' % (epaUrl, epa, description)

###################################################################
### Use the string.Template to store custom HTML as a big string
###################################################################
    if epaList != []: # Is empty when Milestone piped not found in Milestone_Map
        suggestTemplate = '''
        We have suggested a few EPAs common on <strong>$Rotation</strong>, but you can choose whichever you like.<br>
        <h3>These are the <i>suggested</i> EPAs for $Rotation:</h3>
                    <ul>
                    $suggestEPAurlHTML
                    </ul>
        '''
    else:
        suggestTemplate = '''
        <div id="sorry">Sorry!</div> We don't currently have suggested EPAs for <strong>$Rotation</strong> - our bad.<br>
        Please choose any suitable EPA from the links below.
        '''

    suggestFinalHTML = Template(suggestTemplate).safe_substitute(
        Rotation=Rotation, suggestEPAurlHTML=suggestEPAurlHTML)

    templateVars = dict(linkBack=linkBack, FName=FName,
                        LName=LName, Rotation=Rotation,
                        suggestFinalHTML=suggestFinalHTML,
                        restEPAurlHTML=restEPAurlHTML,
                        ResDirectory=ResDirectory)
    with open(mainTemplate, 'r') as temp:
        htmlTemp = temp.read()
        main = Template(htmlTemp).safe_substitute(templateVars)

    templateVars = dict(cssSheet=cssSheet, title=title, version=version,
                        main=main)
    with open(frameHTML, 'r') as templateFH:
        htmlTemplate = templateFH.read()
        finalHTML = Template(htmlTemplate).safe_substitute(templateVars)

# Save for local debugging, not CGI
# outfile2 =  open("wvHTML/EPApicker_templated.html", 'w')
# outfile2.write(finalHTML)

###################################################################
### HTML Starts Here
###################################################################
    print "Content-type:text/html\r\n\r\n"
# Need this header to start off the html file
    print finalHTML

# Indent de-indent ending this line to turn off the CGI try

    """
    CAREFUL - qualID is itself a URL with encoded variables and so it contains =?&
    It seems to work ok despite this but worth keeping an eye on.
    """

except NameError:
    cgiErrTemplateFH = open('epaCGIerrTemplate.html', 'r')
    cgiErrTemplate = cgiErrTemplateFH.read()
    print "Content-type:text/html\r\n\r\n"
    print Template(cgiErrTemplate).safe_substitute(version=version,
                                                    cssSheet=cssSheet,
                                                    ResDirectory=ResDirectory)
#End
