#! /usr/bin/python26

"""
First started 20 Oct 15
by Michael Scahill, mdscahill@gmail.com
Part of the "West-Value" consulting project to develop an alternative to eValue using
Qualtrics.
This code reads a csv file of basic data on all the residents* and produces
links to the portal page for each resident.
This is intended as a backup. The plan was to give each resident a custom URL
that goes directly to portal. ResidentDirectory.py provides an esacpe so that
if anything goes awry with the portal links, there is a way to switch or escape.

* There is some question about how to handle the csv file, really how to keep it
up to date every year. The residency MS-Access database I accessed on 7dec15
has a table that can be exported easily as a .txt (effectively a csv), but
the whole table includes a bunch of info that we wouldn't want to be accessible
on the internet. A few options:
    - Keep westValue on pediatricly. Only want to store otherwise public info on
    the server. Could setup a spreadsheet or just instructions to strip sensitive
    info from the csv. Could also setup admin.py to upload a file & strip out
    all but essential info so it's never stored. This would be cool but is
    probably too clever.
    - If westValue moves into a dept server, it could be secured behind the VPN
As a first pass, I think assuming the CSV is stripped is the way to go.

General Flow:
- It's almost a static page. CGI just reads the resident database from CSV &
populates HTML
- Read CSV file, try header detection

Major Versions:
v1 - 9dec15

"""
#===============================================================================
import re
import csv
import os.path
from string import Template
# import os, sys

###################################################################
### Define Globals Before Main try block
###################################
try: version = os.path.basename(__file__)
except: version = 'ResidentDirectory'

csvIn = 'Resident_Clean.csv'
AmionNameHeader = 'AmionName' # csv reader looks for this to find the header row
# This tolerates a miss-sorted sheet
LName = 'LName'
FName = 'FName'
pgy = 'pgy'
Email = 'Email'
AmionF = 'AmionF'
AmionL = 'AmionL'
Chief = 'Chief Resident'
headers = [] # Initialize, populated by reading the csv
headersDict = {}

residentsTable = []
residentsTableClean = []
urlBase = 'http://www.pediatricly.com/cgi-bin/westValue/portal4.py'
qualID = 'qualID'
temp = 'temp'
#This will need a look up or preset Qualtrics link eventually
urlVars = [AmionF, FName, AmionL, pgy, qualID]

urlList = []
links1 = ''
links2 = ''
links3 =''
cssSheet = 'http://www.pediatricly.com/westVal/WVmain.css'

###################################################################
### Read the CSV list from active dir
### Tolerates missorted sheets & extra columns
### Outputs residresidentsTableClean, a list of dicts
###################################################################

'''
The following loops find whichever line of the csv contains the headers
It searches for key text (eg 'first') and stores the column numbers where those
are found. The next loop utilizes these to get the data organized right.
This combo, while cumbersome, gives standardized var names & tolerates missorted
csv and csv with extra columns without storing that info.
'''

try:
    fh = open(csvIn, 'rb')
    csvreader = csv.reader(fh, quotechar=' ')
    for row in csvreader:
        if 'AmionName' in row:
            headers = row
    fh.close()

    for i, col in enumerate(headers):
        if 'Amion' in col or 'amion' in col:
            headersDict[AmionNameHeader] = i
        elif 'Last' in col or 'last' in col:
            headersDict[LName] = i
        elif 'First' in col or 'first' in col:
            headersDict[FName] = i
        elif 'Category' in col or 'category' in col:
            headersDict[pgy] = i
        elif 'Email' in col or 'email' in col:
            headersDict[Email] = i
        else: pass


    '''
    The following loop creates a list of dicts. Each dict is a resident.
    Each key, value pair is an item from headersDict and its corresponding value,
    respectively.
    data = list(csv.DictReader(csvfile)) #This works but keeps the non-std col names
    '''
    data = []
    fh = open(csvIn, 'rb')
    csvreader2 = csv.reader(fh, quotechar=' ')
    for row in csvreader2:
        if AmionNameHeader in row: pass
        else:
            entry = {}
            for head in headersDict:
                entry[head] = row[headersDict[head]].strip() #No trailing space
            residentsTable.append(entry)

    fh.close()
# print residentsTable

    for resident in residentsTable:
        newEntry = {}
        if resident[pgy] == Chief: pass
        else:
            for key in resident:
                if key == AmionNameHeader:
                    cleanAmion = re.sub(r'[=\*\+]', '', resident[key])
                    newEntry[AmionNameHeader] = cleanAmion
                    AmionLi = re.match(r'^\w+', cleanAmion).group()
                    newEntry[AmionL] = AmionLi
                    AmionFi = re.search(r'-(\w)', cleanAmion).group(1)
                    newEntry[AmionF] = AmionFi
                elif key == pgy:
                    cleanPGY = re.sub('\D','', resident[key])
                    newEntry[pgy] = cleanPGY
                else: newEntry[key] = resident[key]
            newEntry[qualID] = temp
            residentsTableClean.append(newEntry)

#print residentsTableClean
    '''
    Might want to write that residentsTableClean into a file for recycling
    '''
###################################################################
### Generate custom urls to portal4.py
### Output strings by pgy of html list element links
###################################################################
# linkList = []
    residentsTableClean = sorted(residentsTableClean, key=lambda k: (k[pgy], k[LName]))

    for resident in residentsTableClean:
        suffix = '?'
        for key in resident:
            if key in urlVars:
                suffix = suffix + key + '=' + resident[key] + '&'
        suffix = suffix[:-1]
        url = urlBase + suffix
        urlList.append(url)
        linkI = '<li><a href ="%s">%s %s</a></li>\n' % (url, resident[FName],
                                                        resident[LName])
        # tup = (resident[pgy], resident[LName], linkI)
        # linkList.append(tup)
        if resident[pgy] == str(1): links1 += linkI
        elif resident[pgy] == str(2): links2 += linkI
        elif resident[pgy] == str(3): links3 += linkI

###################################################################
### Generate custom urls to portal4.py
###################################################################

###################################################################
### Use the string.Template to store custom HTML as a big string
###################################################################
    templateFH = open('resDirHTMLtemplate.html', 'r')
    htmlTemplate = templateFH.read()

    templateVars = dict(cssSheet=cssSheet, links1=links1, links2=links2,
                        links3=links3, version=version)

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

except:
# cgiErrTemplateFH = open('portalCGIerrTemplate.html', 'r')
# cgiErrTemplate = cgiErrTemplateFH.read()
    print 'Content-type:text/html\r\n\r\n'
    print '<h1>Oops!</h1>'
    print 'Something went horribly wrong with westValue. <b>Sorry!</b><br>'
    print 'Please let Mike or Marcela know what led up to this screen.'


