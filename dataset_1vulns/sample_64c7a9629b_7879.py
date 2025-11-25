#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.


from bs4 import BeautifulSoup, UnicodeDammit
import urllib2
import re
import helpers
import logger
import datetime
import sys
from decimal import Decimal
from HTMLParser import HTMLParseError
from time import strptime
import mylar

def GCDScraper(ComicName, ComicYear, Total, ComicID, quickmatch=None):
    NOWyr = datetime.date.today().year
    if datetime.date.today().month == 12:
        NOWyr = NOWyr + 1
        logger.fdebug("We're in December, incremented search Year to increase search results: " + str(NOWyr))
    comicnm = ComicName.encode('utf-8').strip()
    comicyr = ComicYear
    comicis = Total
    comicid = ComicID
    comicnm_1 = re.sub('\+', '%2B', comicnm)
    comicnm = re.sub(' ', '+', comicnm_1)
    input = 'http://www.comics.org/search/advanced/process/?target=series&method=icontains&logic=False&order2=date&order3=&start_date=' + str(comicyr) + '-01-01&end_date=' + str(NOWyr) + '-12-31&series=' + str(comicnm) + '&is_indexed=None'
    response = urllib2.urlopen (input)
    soup = BeautifulSoup (response)
    cnt1 = len(soup.findAll("tr", {"class": "listing_even"}))
    cnt2 = len(soup.findAll("tr", {"class": "listing_odd"}))

    cnt = int(cnt1 + cnt2)

    resultName = []
    resultID = []
    resultYear = []
    resultIssues = []
    resultURL = None
    n_odd = -1
    n_even = -1
    n = 0
    while (n < cnt):
        if n%2==0:
            n_even+=1
            resultp = soup.findAll("tr", {"class": "listing_even"})[n_even]
        else:
            n_odd+=1
            resultp = soup.findAll("tr", {"class": "listing_odd"})[n_odd]
        rtp = resultp('a')[1]
        resultName.append(helpers.cleanName(rtp.findNext(text=True)))
        fip = resultp('a', href=True)[1]
        resultID.append(fip['href'])
        subtxt3 = resultp('td')[3]
        resultYear.append(subtxt3.findNext(text=True))
        resultYear[n] = resultYear[n].replace(' ', '')
        subtxt4 = resultp('td')[4]
        resultIssues.append(helpers.cleanName(subtxt4.findNext(text=True)))
        resiss = resultIssues[n].find('issue')
        resiss = int(resiss)
        resultIssues[n] = resultIssues[n].replace('', '')[:resiss]
        resultIssues[n] = resultIssues[n].replace(' ', '')
        CleanComicName = re.sub('[\,\.\:\;\'\[\]\(\)\!\@\#\$\%\^\&\*\-\_\+\=\?\/]', '', comicnm)
        CleanComicName = re.sub(' ', '', CleanComicName).lower()
        CleanResultName = re.sub('[\,\.\:\;\'\[\]\(\)\!\@\#\$\%\^\&\*\-\_\+\=\?\/]', '', resultName[n])
        CleanResultName = re.sub(' ', '', CleanResultName).lower()
        if CleanResultName == CleanComicName or CleanResultName[3:] == CleanComicName:
            if resultYear[n] == ComicYear or resultYear[n] == str(int(ComicYear) +1):
                TotalIssues = resultIssues[n]
                resultURL = str(resultID[n])
                rptxt = resultp('td')[6]
                resultPublished = rptxt.findNext(text=True)
                break
        n+=1
    if resultURL is None:
        return 'No Match'
    return GCDdetails(comseries=None, resultURL=resultURL, vari_loop=0, ComicID=ComicID, TotalIssues=TotalIssues, issvariation="no", resultPublished=resultPublished)


def GCDdetails(comseries, resultURL, vari_loop, ComicID, TotalIssues, issvariation, resultPublished):

    gcdinfo = {}
    gcdchoice = []
    gcount = 0
    i = 0

    if vari_loop == 99: vari_loop = 1

    while (i <= vari_loop):
        if vari_loop > 0:
            try:
                boong = comseries['comseries'][i]
            except IndexError:
                break
            resultURL = boong['comseriesID']
            ComicID = boong['comicid']
            TotalIssues+= int(boong['comseriesIssues'])
        else:
            resultURL = resultURL
            inputMIS = 'http://www.comics.org' + str(resultURL)
            resp = urllib2.urlopen (inputMIS)
            try:
                soup = BeautifulSoup(urllib2.urlopen(inputMIS))
            except UnicodeDecodeError:
                logger.info("I've detected your system is using: " + sys.stdout.encoding)
                logger.info("unable to parse properly due to utf-8 problem, ignoring wrong symbols")
                try:
                    soup = BeautifulSoup(urllib2.urlopen(inputMIS)).decode('utf-8', 'ignore')
                except UnicodeDecodeError:
                    logger.info("not working...aborting. Tell Evilhero.")
                    return
            pyearit = soup.find("div", {"class": "item_data"})
            pyeartxt = pyearit.find(text=re.compile(r"Series"))
            pyearst = pyeartxt.index('Series')
            ParseYear = pyeartxt[int(pyearst) -5:int(pyearst)]
            parsed = soup.find("div", {"id": "series_data"})
            subtxt3 = parsed.find("dd", {"id": "publication_dates"})
            resultPublished = subtxt3.findNext(text=True).rstrip()
            parsfind = parsed.findAll("dt", {"class": "long"})
            seriesloop = len(parsfind)
            resultFormat = ''
            for pf in parsfind:
                if 'Publishing Format:' in pf.findNext(text=True):
                    subtxt9 = pf.find("dd", {"id": "series_format"})
                    resultFormat = subtxt9.findNext(text=True).rstrip()
                    continue
            if resultFormat != '':
                if 'ongoing series' in resultFormat.lower() and 'was' not in resultFormat.lower() and 'present' not in resultPublished.lower():
                    resultPublished = resultPublished + " - Present"
                if 'limited series' in resultFormat.lower() and '?' in resultPublished:
                    resultPublished = resultPublished + " (Limited Series)"
            coverst = soup.find("div", {"id": "series_cover"})
            if coverst < 0:
                gcdcover = "None"
            else:
                subcoverst = coverst('img', src=True)[0]
                gcdcover = subcoverst['src']

        input2 = 'http://www.comics.org' + str(resultURL) + 'details/'
        resp = urllib2.urlopen(input2)
        soup = BeautifulSoup(resp)

        type = soup.find(text=' Pub. Date ')
        if type:
            datetype = "pub"
        else:
            datetype = "on-sale"

        cnt1 = len(soup.findAll("tr", {"class": "row_even_False"}))
        cnt2 = len(soup.findAll("tr", {"class": "row_even_True"}))

        cnt = int(cnt1 + cnt2)

        n_odd = -1
        n_even = -1
        n = 0
        PI = "1.00"
        altcount = 0
        PrevYRMO = "0000-00"
        while (n < cnt):
            if n%2==0:
                n_odd+=1
                parsed = soup.findAll("tr", {"class": "row_even_False"})[n_odd]
                ntype = "odd"
            else:
                n_even+=1
                ntype = "even"
                parsed = soup.findAll("tr", {"class": "row_even_True"})[n_even]
            subtxt3 = parsed.find("a")
            ParseIssue = subtxt3.findNext(text=True)

            fid = parsed('a', href=True)[0]
            resultGID = fid['href']
            resultID = resultGID[7:-1]

            if ',' in ParseIssue: ParseIssue = re.sub("\,", "", ParseIssue)
            variant="no"
            if 'Vol' in ParseIssue or '[' in ParseIssue or 'a' in ParseIssue or 'b' in ParseIssue or 'c' in ParseIssue:
                m = re.findall('[^\[\]]+', ParseIssue)
                if '.' in m[0]:
                    dec_chk = m[0]
                    dec_st = dec_chk.find('.')
                    dec_b4 = dec_chk[:dec_st]
                    dec_ad = dec_chk[dec_st +1:]
                    dec_ad = re.sub("\s", "", dec_ad)
                    if dec_b4.isdigit() and dec_ad.isdigit():
                        ParseIssue = dec_b4 + "." + dec_ad
                    else:
                        ParseIssue = re.sub("[^0-9]", " ", dec_chk)
                else:
                    ParseIssue = re.sub("[^0-9]", " ", m[0])

                logger.fdebug("variant cover detected : " + str(ParseIssue))
                variant="yes"
                altcount = 1
            isslen = ParseIssue.find(' ')
            if isslen < 0:
                isschk = ParseIssue
            else:
                isschk = ParseIssue[:isslen]
            ParseIssue = re.sub("\s", "", ParseIssue)
            halfchk = "no"
            if '.' in isschk:
                isschk_find = isschk.find('.')
                isschk_b4dec = isschk[:isschk_find]
                isschk_decval = isschk[isschk_find +1:]
                if len(isschk_decval) == 1:
                    ParseIssue = isschk_b4dec + "." + str(int(isschk_decval) * 10)

            elif '/' in isschk:
                ParseIssue = "0.50"
                isslen = 0
                halfchk = "yes"
            else:
                isschk_decval = ".00"
                ParseIssue = ParseIssue + isschk_decval
            if variant == "yes":
                altcount = 1

            datematch="false"

            if not any(d.get('GCDIssue', None) == str(ParseIssue) for d in gcdchoice):
                pass
            else:
                for d in gcdchoice:
                    if str(d['GCDIssue']) == str(ParseIssue):
                       if str(d['GCDDate']) == str(gcdinfo['ComicDate']):
                           datematch="true"
                       else:
                           datematch="false"

            if datematch == "false":
                gcdinfo['ComicIssue'] = ParseIssue
                ParseDate = GettheDate(parsed, PrevYRMO)
                ParseDate = ParseDate.replace(' ', '')
                PrevYRMO = ParseDate
                gcdinfo['ComicDate'] = ParseDate
                if ComicID[:1] == "G":
                    gcdchoice.append({
                        'GCDid':                ComicID,
                        'IssueID':              resultID,
                        'GCDIssue':             gcdinfo['ComicIssue'],
                        'GCDDate':              gcdinfo['ComicDate']
                        })
                    gcount+=1
                else:
                    gcdchoice.append({
                        'GCDid':                ComicID,
                        'GCDIssue':             gcdinfo['ComicIssue'],
                        'GCDDate':              gcdinfo['ComicDate']
                        })

                gcdinfo['gcdchoice'] = gcdchoice

            altcount = 0
            n+=1
        i+=1
    gcdinfo['gcdvariation'] = issvariation
    if ComicID[:1] == "G":
        gcdinfo['totalissues'] = gcount
    else:
        gcdinfo['totalissues'] = TotalIssues
    gcdinfo['ComicImage'] = gcdcover
    gcdinfo['resultPublished'] = resultPublished
    gcdinfo['SeriesYear'] = ParseYear
    gcdinfo['GCDComicID'] = resultURL.split('/')[0]
    return gcdinfo

def GettheDate(parsed, PrevYRMO):
    subtxt1 = parsed('td')[1]
    ParseDate = subtxt1.findNext(text=True).rstrip()
    pformat = 'pub'
    if ParseDate is None or ParseDate == '':
        subtxt1 = parsed('td')[2]
        ParseDate = subtxt1.findNext(text=True)
        pformat = 'on-sale'
        if len(ParseDate) < 7: ParseDate = '0000-00'
    basmonths = {'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05', 'june': '06', 'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12'}
    pdlen = len(ParseDate)
    pdfind = ParseDate.find(' ', 2)
    if pformat == 'on-sale': pass
    else:
        if ParseDate[pdfind +1:pdlen -1].isdigit():
            for numbs in basmonths:
                if numbs in ParseDate.lower():
                    pconv = basmonths[numbs]
                    ParseYear = re.sub('/s', '', ParseDate[-5:])
                    ParseDate = str(ParseYear) + "-" + str(pconv)
                    break
        else:
            baseseasons = {'spring': '03', 'summer': '06', 'fall': '09', 'winter': '12'}
            for seas in baseseasons:
                if seas in ParseDate.lower():
                    sconv = baseseasons[seas]
                    ParseYear = re.sub('/s', '', ParseDate[-5:])
                    ParseDate = str(ParseYear) + "-" + str(sconv)
                    break
    if PrevYRMO == '0000-00':
        ParseDate = '0000-00'
    else:
        PrevYR = str(PrevYRMO)[:4]
        PrevMO = str(PrevYRMO)[5:]
        if int(PrevMO) == 12:
            PrevYR = int(PrevYR) + 1
            PrevMO = 1
        else:
            PrevMO = int(PrevMO) + 1
        if int(PrevMO) < 10:
            PrevMO = "0" + str(PrevMO)
        ParseDate = str(PrevYR) + "-" + str(PrevMO)
    return ParseDate

def GCDAdd(gcdcomicid):
    serieschoice = []
    series = {}
    logger.fdebug("I'm trying to find these GCD comicid's:" + str(gcdcomicid))
    for gcdid in gcdcomicid:
        logger.fdebug("looking at gcdid:" + str(gcdid))
        input2 = 'http://www.comics.org/series/' + str(gcdid)
        logger.fdebug("---url: " + str(input2))
        resp = urllib2.urlopen (input2)
        soup = BeautifulSoup (resp)
        parsen = soup.find("span", {"id": "series_name"})
        subpar = parsen('a')[0]
        resultName = subpar.findNext(text=True)
        coverst = soup.find("div", {"id": "series_cover"})
        if coverst < 0:
            gcdcover = "None"
        else:
            subcoverst = coverst('img', src=True)[0]
            gcdcover = subcoverst['src']
        try:
            pubst = soup.find("div", {"class": "item_data"})
            catchit = pubst('a')[0]
        except (IndexError, TypeError):
            pubst = soup.findAll("div", {"class": "left"})[1]
            catchit = pubst.find("a")
        publisher = catchit.findNext(text=True)
        parsed = soup.find("div", {"id": "series_data"})
        subtxt3 = parsed.find("dd", {"id": "publication_dates"})
        pubdate = subtxt3.findNext(text=True).rstrip()
        subtxt4 = parsed.find("dd", {"id": "issues_published"})
        noiss = subtxt4.findNext(text=True)
        lenwho = len(noiss)
        lent = noiss.find(' ', 2)
        lenf = noiss.find('(')
        stringit = noiss[lenf:lenwho]
        stringout = noiss[:lent]
        noissues = stringout.rstrip('  \t\r\n\0')
        numbering = stringit.rstrip('  \t\r\n\0')
        serieschoice.append({
               "ComicID":         gcdid,
               "ComicName":       resultName,
               "ComicYear":        pubdate,
               "ComicIssues":    noissues,
               "ComicPublisher": publisher,
               "ComicCover":     gcdcover
              })
    series['serieschoice'] = serieschoice
    return series

def ComChk(ComicName, ComicYear, ComicPublisher, Total, ComicID):
    comchkchoice = []
    comchoice = {}

    NOWyr = datetime.date.today().year
    if datetime.date.today().month == 12:
        NOWyr = NOWyr + 1
        logger.fdebug("We're in December, incremented search Year to increase search results: " + str(NOWyr))
    comicnm = ComicName.encode('utf-8').strip()
    comicyr = ComicYear
    comicis = Total
    comicid = ComicID
    comicpub = ComicPublisher.encode('utf-8').strip()
    comicrun = []
    pubbiggies = ['DC', 'Marvel', 'Image', 'IDW']
    uhuh = "no"
    for pb in pubbiggies:
        if pb in comicpub:
            uhuh = "yes"
            conv_pub = comicpub.split()[0]
    comicrun.append(comicnm)
    cruncnt = 0
    if len(str(comicnm).split()) > 2:
        comicrun.append(' '.join(comicnm.split(' ')[:-1]))
        cruncnt+=1
    if re.sub('[\.\,\:]', '', comicnm) != comicnm:
        comicrun.append(re.sub('[\.\,\:]', '', comicnm))
        cruncnt+=1
    if comicnm.lower().startswith('the'):
        comicrun.append(comicnm[4:].strip())
        cruncnt+=1
    totalcount = 0
    cr = 0
    while (cr <= cruncnt):
        comicnm = comicrun[cr]
        comicnm = re.sub(' ', '+', comicnm)
        if uhuh == "yes":
            publink = "&pub_name=" + str(conv_pub)
        if uhuh == "no":
            publink = "&pub_name="
        input = 'http://www.comics.org/search/advanced/process/?target=series&method=icontains&logic=False&keywords=&order1=series&order2=date&order3=&start_date=' + str(comicyr) + '-01-01&end_date=' + str(NOWyr) + '-12-31' + '&title=&feature=&job_number=&pages=&script=&pencils=&inks=&colors=&letters=&story_editing=&genre=&characters=&synopsis=&reprint_notes=&story_reprinted=None&notes=' + str(publink) + '&pub_notes=&brand=&brand_notes=&indicia_publisher=&is_surrogate=None&ind_pub_notes=&series=' + str(comicnm) + '&series_year_began=&series_notes=&tracking_notes=&issue_count=&is_comics=None&format=&color=&dimensions=&paper_stock=&binding=&publishing_format=&issues=&volume=&issue_title=&variant_name=&issue_date=&indicia_frequency=&price=&issue_pages=&issue_editing=&isbn=&barcode=&issue_notes=&issue_reprinted=None&is_indexed=None'
        response = urllib2.urlopen (input)
        soup = BeautifulSoup (response)
        cnt1 = len(soup.findAll("tr", {"class": "listing_even"}))
        cnt2 = len(soup.findAll("tr", {"class": "listing_odd"}))

        cnt = int(cnt1 + cnt2)

        resultName = []
        resultID = []
        resultYear = []
        resultIssues = []
        resultPublisher = []
        resultURL = None
        n_odd = -1
        n_even = -1
        n = 0
        while (n < cnt):
            if n%2==0:
                n_even+=1
                resultp = soup.findAll("tr", {"class": "listing_even"})[n_even]
            else:
                n_odd+=1
                resultp = soup.findAll("tr", {"class": "listing_odd"})[n_odd]
            rtp = resultp('a')[1]
            rtpit = rtp.findNext(text=True)
            rtpthis = rtpit.encode('utf-8').strip()
            resultName.append(helpers.cleanName(rtpthis))
            pub = resultp('a')[0]
            pubit = pub.findNext(text=True)
            pubthis = pubit.encode('utf-8').strip()
            resultPublisher.append(pubthis)
            fip = resultp('a', href=True)[1]
            resultID.append(fip['href'])
            subtxt3 = resultp('td')[3]
            resultYear.append(subtxt3.findNext(text=True))
            resultYear[n] = resultYear[n].replace(' ', '')
            subtxt4 = resultp('td')[4]
            resultIssues.append(helpers.cleanName(subtxt4.findNext(text=True)))
            resiss = resultIssues[n].find('issue')
            resiss = int(resiss)
            resultIssues[n] = resultIssues[n].replace('', '')[:resiss]
            resultIssues[n] = resultIssues[n].replace(' ', '')
            if not any(d.get('GCDID', None) == str(resultID[n]) for d in comchkchoice):
                comchkchoice.append({
                       "ComicID":         str(comicid),
                       "ComicName":       resultName[n],
                       "GCDID":           str(resultID[n]).split('/')[2],
                       "ComicYear":      str(resultYear[n]),
                       "ComicPublisher": resultPublisher[n],
                       "ComicURL":       "http://www.comics.org" + str(resultID[n]),
                       "ComicIssues":    str(resultIssues[n])
                      })
            n+=1
        cr+=1
    totalcount= totalcount + cnt
    comchoice['comchkchoice'] = comchkchoice
    return comchoice, totalcount

def decode_html(html_string):
    converted = UnicodeDammit(html_string)
    if not converted.unicode:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.triedEncodings))
    return converted.unicode

def annualCheck(gcomicid, comicid, comicname, comicyear):
    comicnm = comicname.encode('utf-8').strip()
    comicnm_1 = re.sub('\+', '%2B', comicnm + " annual")
    comicnm = re.sub(' ', '+', comicnm_1)
    input = 'http://www.comics.org/search/advanced/process/?target=series&method=icontains&logic=False&order2=date&order3=&start_date=' + str(comicyear) + '-01-01&end_date=' + str(comicyear) + '-12-31&series=' + str(comicnm) + '&is_indexed=None'

    response = urllib2.urlopen (input)
    soup = BeautifulSoup (response)
    cnt1 = len(soup.findAll("tr", {"class": "listing_even"}))
    cnt2 = len(soup.findAll("tr", {"class": "listing_odd"}))

    cnt = int(cnt1 + cnt2)

    resultName = []
    resultID = []
    resultYear = []
    resultIssues = []
    resultURL = None
    n_odd = -1
    n_even = -1
    n = 0
    while (n < cnt):
        if n%2==0:
            n_even+=1
            resultp = soup.findAll("tr", {"class": "listing_even"})[n_even]
        else:
            n_odd+=1
            resultp = soup.findAll("tr", {"class": "listing_odd"})[n_odd]
        rtp = resultp('a')[1]
        rtp1 = re.sub('Annual', '', rtp)
        resultName.append(helpers.cleanName(rtp1.findNext(text=True)))
        fip = resultp('a', href=True)[1]
        resultID.append(fip['href'])
        subtxt3 = resultp('td')[3]
        resultYear.append(subtxt3.findNext(text=True))
        resultYear[n] = resultYear[n].replace(' ', '')
        subtxt4 = resultp('td')[4]
        resultIssues.append(helpers.cleanName(subtxt4.findNext(text=True)))
        resiss = resultIssues[n].find('issue')
        resiss = int(resiss)
        resultIssues[n] = resultIssues[n].replace('', '')[:resiss]
        resultIssues[n] = resultIssues[n].replace(' ', '')
        CleanComicName = re.sub('[\,\.\:\;\'\[\]\(\)\!\@\#\$\%\^\&\*\-\_\+\=\?\/]', '', comicnm)
        CleanComicName = re.sub(' ', '', CleanComicName).lower()
        CleanResultName = re.sub('[\,\.\:\;\'\[\]\(\)\!\@\#\$\%\^\&\*\-\_\+\=\?\/]', '', resultName[n])
        CleanResultName = re.sub(' ', '', CleanResultName).lower()
        if CleanResultName == CleanComicName or CleanResultName[3:] == CleanComicName:
            if resultYear[n] == ComicYear or resultYear[n] == str(int(ComicYear) +1):
                TotalIssues = resultIssues[n]
                resultURL = str(resultID[n])
                rptxt = resultp('td')[6]
                resultPublished = rptxt.findNext(text=True)
                break
        n+=1
    return