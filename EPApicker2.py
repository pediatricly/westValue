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

#===============================================================================
import csv
import os.path
from string import Template

try: version = os.path.basename(__file__)
except: version = 'EPApicker2'

###################################################################
### Setup the Qulatrics URL generation
###################################################################
def urlGen2(base, stubList, EPA, suffix):
# Loop to format the URL with form data 'url?varName=_var_&var2=_var2_'
	dataList = []
	for item in stubList:
		dataList.append(item)
	dataList.append(EPA)

	for urlVar, varName in dataList:
		# print urlVar
		suffix = suffix + urlVar + '=' + str(varName) + '&'

	if suffix[-1] == '&': suffix = suffix[:-1] # Clip off the last &
	urlOut = base + suffix # Assemble the final custom Qualtrics URL
	return urlOut

###################################################################
### Define Globals Before Main try block
####################################################################

# Pre-set the Qualtrics url base
qualbase = 'https://ucsf.co1.qualtrics.com/SE/?SID=SV_1ST78nRrIv74UaF' # It looks like the base could be longer but
# keeping it short seems safer
ResDirectory = 'http://www.pediatricly.com/cgi-bin/westValue/ResidentDirectory.py'

cssSheet = 'http://www.pediatricly.com/westVal/WVmain.css'
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
# Get names from the URL. These are set in portal#.py
    LName = form.getvalue('LName')
    FName = form.getvalue('FName')
    pgy = form.getvalue('pgy')
    Rotation = form.getvalue('Rotation')
    Milestone = form.getvalue('Milestone')

# Store the Qualtrics link custom suffix
    qualID = form.getvalue('qualID')

    """
    LName = "Neely"
    pgy = 3
    FName = "Jessica"
    Rotation = "SFN"
    Milestone = "SFN"
# qualID = "SE?Q_DL=4NiHEv4rRV75KUR_2rxLPgxEvdzAXOJ_MLRP_4IUOlBssXvaqJ8h&Q_CHL=gl"
    """
    if LName == None or qualID == None or FName == None or Rotation == None or Milestone == None:
        raise NameError
    cgiError = 0

# Temporary measure to get the old Qualtrics link going, careful, this overwrites the URL input
    # qualID = "SE?Q_DL=4NiHEv4rRV75KUR_2rxLPgxEvdzAXOJ_MLRP_4IUOlBssXvaqJ8h&Q_CHL=gl"

    urlBase = qualbase # + qualID
    urlSuffix = '&'
    rotDataListStub = ([['LName', LName], ['FName', FName], ['pgy', pgy],
                        ['Rotation', Rotation]])

###################################################################
### Read the CSV mapping of milestones to EPA from active dir
###################################################################
    milestonesList = [] # Holds all the Milestone rows with X for relevant EPAs
    headers = []
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
    csvIn2 = 'EPA_descriptions.csv'

    with open(csvIn2, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, quotechar='"')
        for row in csvreader:
            if row[0] != 'EPA Number':
                descriptionList.append(row)

# print descriptionList


    epaList = [] # This is the list of suggested EPAs based on CGI Milestone var
    for row in headedMilestones:
        if row[1] == 'X':
            epaNum = row[0]
            epaNum = epaNum[3:]
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

    for epa in epaList:
        description = ''
        for item in descriptionList:
            if item[0] == epa:
                description = item[1]
        epaUrl =  urlGen2(urlBase, rotDataListStub, ['EPA', epa], urlSuffix)
        suggestEPAurlHTML += '<li><a href="%s">EPA #%s: %s</a></li>' % (epaUrl, epa, description)

    for group in headers:
        # first = group[0]
        if group[:3] == 'EPA':
            epa = group[3:]
            if epa not in epaList:
                description = ''
                for item in descriptionList:
                    if item[0] == epa:
                        description = item[1]
        # print "EPA %s description has to go here %s<br>" % (epa, description)
                epaUrl =  urlGen2(urlBase, rotDataListStub, ['EPA', epa], urlSuffix)
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
        <b>Sorry!</b> We don't currently have suggested EPAs for <strong>$Rotation</strong> - our bad.<br>
        Please choose any EPA from the links below and, if you get a chance, please email Marcela to let her know which rotation caused the issue so we can fix it.
        '''

    suggestFinalHTML = Template(suggestTemplate).safe_substitute(
        Rotation=Rotation, suggestEPAurlHTML=suggestEPAurlHTML)

    templateFH = open('EPApickerHTMLtemplate.html', 'r')
    htmlTemplate = templateFH.read()

    templateVars = dict(cssSheet=cssSheet, FName=FName, LName=LName,
                        Rotation=Rotation, suggestFinalHTML=suggestFinalHTML,
                        restEPAurlHTML=restEPAurlHTML, version=version,
                        ResDirectory=ResDirectory)

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

    """
    CAREFUL - qualID is itself a URL with encoded variables and so it contains =?&
    It seems to work ok despite this but worth keeping an eye on.
    """


except NameError:
    cgiError = 1

    cgiErrTemplateFH = open('epaCGIerrTemplate.html', 'r')
    cgiErrTemplate = cgiErrTemplateFH.read()
    print "Content-type:text/html\r\n\r\n"
    print Template(cgiErrTemplate).safe_substitute(version=version,
                                                   cssSheet=cssSheet,
                                                   ResDirectory=ResDirectory)
