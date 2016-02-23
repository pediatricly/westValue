#!usr/bin/python

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
 - cgi feeds that code into scraper which uses probably Requests & Beautiful Soup
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
v5 - may be a name change, this should merge qualcgi1 with scraper into effectively the finished product     
"""

"""
Resources:
Tutorial 1: https://www.youtube.com/watch?v=eRSJSKG4mDA
The actual documentation: http://docs.python-requests.org/en/latest/user/quickstart/

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


The target code of the actual schedul looks like this in html 
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
# from bs4 import BeautifulSoup
import re

"""
This is from tutorial 1:
with requests.Session() as c:
	url = "http://amion.com/"
	pw = "ucsfpeds"
	c.get(url)
	login_data = dict(password=pw)
	c.post(url, data=login_data, headers={"Referer":"http://amion.com/cgi-bin/ocs"})
	page = c.get("http://amion.com/cgi-bin/ocs")
	print page.content
	
It didn't work & I was having trouble figuring out from his explanation why. 

But then I just tried a simple version from the Requests documentation & it worked!
"""

payload = {"login" : "ucsfpeds"}
r = requests.post("http://amion.com/cgi-bin/ocs", data=payload)
# print(r.text) # This is outputting the html of the actual schedule landing page
html = r.content # And this stores that html as a string

# soup = BeautifulSoup(r.content)
# Ended up not using BeautifulSoup

listofLists = []

fullTable1 = re.findall("^<TR><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
fullTable2 = re.findall("^<TR class=grbg><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)
fullTable3 = re.findall("^<TR><td></font><font color=#\w\w\w\w\w\w>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", html, re.M)

listofTables = [fullTable1, fullTable2, fullTable3]
for subTable in listofTables:
	for rotation, resident in subTable:
		rotation = re.sub(r'&nbsp;', '', rotation)
		resident = re.sub(r'[=\*]', '', resident)
		tempList = [rotation, resident]
		listofLists.append(tempList)
"""
# print "listofLists:"
# print listofLists
# print len(listofLists)

The loop above:
- Replaces all those &nbsp; with "" and trims the =/* off the Amion name
- It then puts those tupules into a list of lists len=2 [rotation, resident]
"""









"""
Will eventually want to tinker with the way rotation names are set. In future, it won't be obvious to an outsider how exactly the regex / replace pulls out rotation names because spaces end up placed helter skelter (because of the way spaces are coded randomly in the html). There's no way to systematize this reliably. What we probably want is a central dict of all rotation names ever & their corresponding EPA bucket. 
This program could scrape active rotations off Amion and maybe output somehow which are missing from the dict & present them to the admin somehow. 
The dict probably ought to be stored in a csv or txt file so that it can be edited without tinkering with this code.
Don't forget to program in a default rotation code to pass to Qualtrics if the rotation name can't be found.
"""

"""
=======================
***This search string:***
"<nobr>(.*)</b></a></TD>"
successfully gets just the resident names as a list of strings!
Realized when doing fullTable tests that some lines actually don't have the </TD> but seems to work fine without it, ie, the /b/a are sufficient.

Many have these damn = & * at the end, but I'm sure those can be trimmed or ignored later.
(Yeah, that's totally easy to fix - just use slice function & if = "=" or "*"
=======================
"""


"""
Stored for potential offline use:
listofListsStore = [['KW&nbsp;Int-Short&nbsp;', 'Guslits-E='], ['KN Call&nbsp;', 'Harper-L'], ['RedBMT-Nite&nbsp;', 'Knappe-A*'], ['PICU-Day&nbsp;', 'Bent-M'], ['PICU Nite&nbsp;', 'Maurer-L'], ['ICN Int-Short&nbsp;', 'Caffarelli-M'], ['ICN Sr-Bridge Long', 'Wu-L*'], ['ICN Sr-Short&nbsp;', 'Truong-B='], ['Pacific Sr-Nite&nbsp;', 'Ort-K'], ['SFO-Int&nbsp;Swing&nbsp;', 'Iacopetti-C'], ['SFO-SCR&nbsp;', 'LaRocca-T='], ['SFO-Sr Day&nbsp;', 'Davenport-J'], ['SFO-Sr Nite&nbsp;', 'FP2: DeMarchis-Emilia'], ['SFN-Int Day&nbsp;', 'FP1: Gomez, Teresa'], ['SFGH-Sr Nite', 'Balkin-E='], ['SFW-Int Day&nbsp;', 'FP1: Cuervo, Catalina'], ['CHO 7a-4p', 'Sofia Kerbawy'], ['CHO&nbsp;3p-12a', 'Armando Huaringa'], ['CHO&nbsp;6p-3a', 'Callie Titcomb'], ['CHO&nbsp;10p-7a', 'UCSF Vaisberg'], ['TCU-Day', 'Hammoudi-T'], ['TCU-ID', 'Vinh-L*'], ['WB', 'Yang-E='], ['KW2&nbsp;', 'Links-B*'], ['BMT&nbsp;', 'Johnson-Kerner-B'], ['PICU-Day', 'Crouch-E='], ['PICU-Day', 'Neely-J'], ['UCW3-Nite&nbsp;', 'Goudy-B='], ['ICN Int-Short', 'Singal-P'], ['ICN Sr-Long&nbsp;', 'Brajkovic-I='], ['ICN Sr-Short&nbsp;', 'Laguna-M'], ['SFO-Int Day', 'EM1: Padrez-Kevin'], ['SFO-Int Nite', 'Spiegel-E'], ['SFO-Sr Day&nbsp;', 'Sundby-T'], ['SFO-Sr Swing&nbsp;', 'FP3: Chang, Steven'], ['SFN Sr Day&nbsp;', 'Thompson-D'], ['SFN-Int Day', 'Nash-D'], ['SFW R2 Day&nbsp;', 'Boddupalli-G'], ['SFGH-Int Nite&nbsp;', 'Wohlford-E'], ['CHO&nbsp;3p-12a', 'Scott Sutton'], ['CHO&nbsp;3p-12a', 'Betty Shum'], ['CHO&nbsp;10p-7a', 'Ruchi Punatar'], ['TCU-Day', 'Kodali-S'], ['TCU-Nite', 'Keller-S='], ['WB', 'Chen-D*'], ['RED', 'Braun-L='], ['PURPLE1-Day', 'Schwartz-R'], ['PURPLE1-Nite&nbsp;', 'Simmons-R'], ['ORANGE1-Day&nbsp;', 'Burnett-H='], ['ORANGE1-Day', 'Argueza-B*'], ['ORANGE3-Day&nbsp;', 'Pantell-M*']]

"""














#End
