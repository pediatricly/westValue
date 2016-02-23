#! /usr/bin/python26

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

#===============================================================================
import csv

"""
The URL into this needs:
?Rotation=__&Milestone=__&LName=__&FName=__&pgy=__&qualID=__
http://pediatricly.com/cgi-bin/westValue/EPApicker.py?Rotation=TCU&Milestone=TCU&AmionL=Neely&AmionF=J&FName=Jessica&pgy=3&qualID=temp
"""
# Hiding these for local debugging:
# Create instance of FieldStorage
form = cgi.FieldStorage()


# Get names from the URL. These are set in qualCGIscrape
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
Rotation = "TCU"
Milestone = "TCU"
"""

# Temporary measure to get the old Qualtrics link going, careful, this overwrites the URL input
qualID = "SE?Q_DL=4NiHEv4rRV75KUR_2rxLPgxEvdzAXOJ_MLRP_4IUOlBssXvaqJ8h&Q_CHL=gl"

# Pre-set the Qualtrics url base
qualbase = 'https://ucsf.co1.qualtrics.com/' # It looks like the base could be longer but
# keeping it short seems safer

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

urlBase = qualbase + qualID
urlSuffix = '?'
rotDataListStub = ([['LName', LName], ['FName', FName], ['pgy', pgy],
                    ['Rotation', Rotation]])

###################################################################
### Read the CSV mapping of milestones to EPA from active dir
###################################################################
milestonesList = []
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

# print milestonesList
# print headers

headedMilestones = []
for row in milestonesList:
    if row[0] == Milestone:
        for i, cell in enumerate(row):
            # print i
            mini = [headers[i], cell]
            headedMilestones.append(mini)

descriptionList = []
csvIn2 = 'EPA_descriptions.csv'

with open(csvIn2, 'rb') as csvfile:
    csvreader = csv.reader(csvfile, quotechar='"')
    for row in csvreader:
        if row[0] != 'EPA Number':
            descriptionList.append(row)

# print descriptionList


epaList = []
for row in headedMilestones:
    if row[1] == 'X':
        epaNum = row[0]
        epaNum = epaNum[3:]
        epaList.append(epaNum)


###################################################################
### HTML Starts Here
###################################################################
print "Content-type:text/html\r\n\r\n"
# Need this header to start off the html file

print """<!DOCTYPE html>
<head>
	<meta charset="UTF-8">
"""
print "<title>westValue - EPA Picker for %s %s</title>" % (FName, LName)

print '<link rel="icon" type="image/jpg" href ="http://www.pediatricly.com/images/westPic.jpg"/>'



# print "<html>"
# print "<head>"
"""
Now that there are a few pages to be made (this, admin, landingpage...) will want a css
"""

print "</head>"
print "<body>"

###################################################################
### Match the resident from URL to rotation in Amion, output URL to Qualtrics with EPA
###################################################################
print """
<figure><img src="http://www.pediatricly.com/images/westPic.jpg" alt="westValue Icon"/></figure><h1>westValue! The EPA Picker</h1>
<p>Finally, let's pick an entrustable professional activity (EPA) for feedback.<p>
"""

print "<h2>(Step 3/3) Pick an EPA</h2>"
print "<p>Click any link below for a 4-question Qualtrics form customized for <b>%s %s</b> and for whichever EPA you choose.<br>" % (FName, LName)
print 'If you are trying to evaluate <i>a different resident</i>, please return to <a href="http://www.pediatricly.com/cgi-bin/westValue/landingpage.py">The Landing Page</a>.</p>'

print "<h3>These are the <i>suggested</i> EPAs for %s:</h3>" % Rotation
print "<p>"
for epa in epaList:
    # print 'EPA #%s<br>' % epa
    description = ''
    for item in descriptionList:
        if item[0] == epa:
            description = item[1]
    # print "EPA %s description has to go here %s<br>" % (epa, description)
    epaUrl =  urlGen2(urlBase, rotDataListStub, ['EPA', epa], urlSuffix)
    print '<a href="%s">EPA #%s: %s</a><br>' % (epaUrl, epa, description)
print '</p>'

print "<h3>These are the <i>rest</i> of the EPAs:</h3>"
print "<p>"
for group in headedMilestones:
    first = group[0]
    if first[:3] == 'EPA':
        epa = first[3:]
        if epa not in epaList:
            description = ''
            for item in descriptionList:
                if item[0] == epa:
                    description = item[1]
    # print "EPA %s description has to go here %s<br>" % (epa, description)
            epaUrl =  urlGen2(urlBase, rotDataListStub, ['EPA', epa], urlSuffix)
            print '<a href="%s">EPA #%s: %s</a><br>' % (epaUrl, epa, description)
print '</p>'

print "</body>"
print "</html>"

"""
CAREFUL - qualID is itself a URL with encoded variables and so it contains =?&
It seems to work ok despite this but worth keep an eye on.
"""
