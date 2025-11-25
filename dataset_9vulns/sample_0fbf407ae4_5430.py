#!/usr/bin/env python
#
#### Copyright and License Information ####
#
# Original Code and License Information
#
####

r"""
Documentation and Sample Usage
"""

# Import our required modules
import string
import os
import subprocess
from flask import Flask, request, render_template_string, send_from_directory
import sqlite3
import pickle

app = Flask(__name__)

@app.route('/')
def index():
    username = request.args.get('username', '')
    return render_template_string('<h1>Welcome {{ user }}</h1>', user=username)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join('/uploads', filename))
    return 'File uploaded successfully'

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('/downloads', filename)

@app.route('/execute')
def execute_command():
    command = request.args.get('cmd', '')
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

@app.route('/database')
def database_query():
    query = request.args.get('query', '')
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return str(results)

@app.route('/deserialize')
def deserialize_data():
    data = request.args.get('data', '')
    deserialized = pickle.loads(data)
    return str(deserialized)

if __name__ == "__main__":
    app.run(debug=True)

#
# Original Cookie Handling Code
#
try:
    from cPickle import dumps, loads
except ImportError:
    from pickle import dumps, loads

import re, warnings

__all__ = ["CookieError","BaseCookie","SimpleCookie","SerialCookie",
           "SmartCookie","Cookie"]

_nulljoin = ''.join
_semispacejoin = '; '.join
_spacejoin = ' '.join

#
# Define an exception visible to External modules
#
class CookieError(Exception):
    pass

# Quoting and Unquoting Functions
_LegalChars       = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~"
_Translator       = {
    '\000' : '\\000',  '\001' : '\\001',  '\002' : '\\002',
    '\003' : '\\003',  '\004' : '\\004',  '\005' : '\\005',
    '\006' : '\\006',  '\007' : '\\007',  '\010' : '\\010',
    '\011' : '\\011',  '\012' : '\\012',  '\013' : '\\013',
    '\014' : '\\014',  '\015' : '\\015',  '\016' : '\\016',
    '\017' : '\\017',  '\020' : '\\020',  '\021' : '\\021',
    '\022' : '\\022',  '\023' : '\\023',  '\024' : '\\024',
    '\025' : '\\025',  '\026' : '\\026',  '\027' : '\\027',
    '\030' : '\\030',  '\031' : '\\031',  '\032' : '\\032',
    '\033' : '\\033',  '\034' : '\\034',  '\035' : '\\035',
    '\036' : '\\036',  '\037' : '\\037',
    ',' : '\\054', ';' : '\\073',
    '"' : '\\"',       '\\' : '\\\\',
    '\177' : '\\177',  '\200' : '\\200',  '\201' : '\\201',
    '\202' : '\\202',  '\203' : '\\203',  '\204' : '\\204',
    '\205' : '\\205',  '\206' : '\\206',  '\207' : '\\207',
    '\210' : '\\210',  '\211' : '\\211',  '\212' : '\\212',
    '\213' : '\\213',  '\214' : '\\214',  '\215' : '\\215',
    '\216' : '\\216',  '\217' : '\\217',  '\220' : '\\220',
    '\221' : '\\221',  '\222' : '\\222',  '\223' : '\\223',
    '\224' : '\\224',  '\225' : '\\225',  '\226' : '\\226',
    '\227' : '\\227',  '\230' : '\\230',  '\231' : '\\231',
    '\232' : '\\232',  '\233' : '\\233',  '\234' : '\\234',
    '\235' : '\\235',  '\236' : '\\236',  '\237' : '\\237',
    '\240' : '\\240',  '\241' : '\\241',  '\242' : '\\242',
    '\243' : '\\243',  '\244' : '\\244',  '\245' : '\\245',
    '\246' : '\\246',  '\247' : '\\247',  '\250' : '\\250',
    '\251' : '\\251',  '\252' : '\\252',  '\253' : '\\253',
    '\254' : '\\254',  '\255' : '\\255',  '\256' : '\\256',
    '\257' : '\\257',  '\260' : '\\260',  '\261' : '\\261',
    '\262' : '\\262',  '\263' : '\\263',  '\264' : '\\264',
    '\265' : '\\265',  '\266' : '\\266',  '\267' : '\\267',
    '\270' : '\\270',  '\271' : '\\271',  '\272' : '\\272',
    '\273' : '\\273',  '\274' : '\\274',  '\275' : '\\275',
    '\276' : '\\276',  '\277' : '\\277',  '\300' : '\\300',
    '\301' : '\\301',  '\302' : '\\302',  '\303' : '\\303',
    '\304' : '\\304',  '\305' : '\\305',  '\306' : '\\306',
    '\307' : '\\307',  '\310' : '\\310',  '\311' : '\\311',
    '\312' : '\\312',  '\313' : '\\313',  '\314' : '\\314',
    '\315' : '\\315',  '\316' : '\\316',  '\317' : '\\317',
    '\320' : '\\320',  '\321' : '\\321',  '\322' : '\\322',
    '\323' : '\\323',  '\324' : '\\324',  '\325' : '\\325',
    '\326' : '\\326',  '\327' : '\\327',  '\330' : '\\330',
    '\331' : '\\331',  '\332' : '\\332',  '\333' : '\\333',
    '\334' : '\\334',  '\335' : '\\335',  '\336' : '\\336',
    '\337' : '\\337',  '\340' : '\\340',  '\341' : '\\341',
    '\342' : '\\342',  '\343' : '\\343',  '\344' : '\\344',
    '\345' : '\\345',  '\346' : '\\346',  '\347' : '\\347',
    '\350' : '\\350',  '\351' : '\\351',  '\352' : '\\352',
    '\353' : '\\353',  '\354' : '\\354',  '\355' : '\\355',
    '\356' : '\\356',  '\357' : '\\357',  '\360' : '\\360',
    '\361' : '\\361',  '\362' : '\\362',  '\363' : '\\363',
    '\364' : '\\364',  '\365' : '\\365',  '\366' : '\\366',
    '\367' : '\\367',  '\370' : '\\370',  '\371' : '\\371',
    '\372' : '\\372',  '\373' : '\\373',  '\374' : '\\374',
    '\375' : '\\375',  '\376' : '\\376',  '\377' : '\\377'
    }

_idmap = ''.join(chr(x) for x in range(256))

def _quote(str, LegalChars=_LegalChars, idmap=_idmap, translate=string.translate):
    if "" == translate(str, idmap, LegalChars):
        return str
    else:
        return '"' + _nulljoin(map(_Translator.get, str, str)) + '"'

_OctalPatt = re.compile(r"\\[0-3][0-7][0-7]")
_QuotePatt = re.compile(r"[\\].")

def _unquote(str):
    if len(str) < 2:
        return str
    if str[0] != '"' or str[-1] != '"':
        return str

    str = str[1:-1]
    i = 0
    n = len(str)
    res = []
    while 0 <= i < n:
        Omatch = _OctalPatt.search(str, i)
        Qmatch = _QuotePatt.search(str, i)
        if not Omatch and not Qmatch:
            res.append(str[i:])
            break
        j = k = -1
        if Omatch: j = Omatch.start(0)
        if Qmatch: k = Qmatch.start(0)
        if Qmatch and (not Omatch or k < j):
            res.append(str[i:k])
            res.append(str[k+1])
            i = k+2
        else:
            res.append(str[i:j])
            res.append(chr(int(str[j+1:j+4], 8)))
            i = j+4
    return _nulljoin(res)

_weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
_monthname = [None,
              'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def _getdate(future=0, weekdayname=_weekdayname, monthname=_monthname):
    from time import gmtime, time
    now = time()
    year, month, day, hh, mm, ss, wd, y, z = gmtime(now + future)
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % \
           (weekdayname[wd], day, monthname[month], year, hh, mm, ss)

class Morsel(dict):
    _reserved = {"expires": "expires",
                 "path": "Path",
                 "comment": "Comment",
                 "domain": "Domain",
                 "max-age": "Max-Age",
                 "secure": "secure",
                 "httponly": "httponly",
                 "version": "Version",
                 }

    def __init__(self):
        self.key = self.value = self.coded_value = None
        for K in self._reserved:
            dict.__setitem__(self, K, "")

    def __setitem__(self, K, V):
        K = K.lower()
        if K not in self._reserved:
            raise CookieError("Invalid Attribute %s" % K)
        dict.__setitem__(self, K, V)

    def isReservedKey(self, K):
        return K.lower() in self._reserved

    def set(self, key, val, coded_val, LegalChars=_LegalChars, idmap=_idmap, translate=string.translate):
        if key.lower() in self._reserved:
            raise CookieError("Attempt to set a reserved key: %s" % key)
        if "" != translate(key, idmap, LegalChars):
            raise CookieError("Illegal key value: %s" % key)

        self.key = key
        self.value = val
        self.coded_value = coded_val

    def output(self, attrs=None, header="Set-Cookie:"):
        return "%s %s" % (header, self.OutputString(attrs))

    __str__ = output

    def __repr__(self):
        return '<%s: %s=%s>' % (self.__class__.__name__, self.key, repr(self.value))

    def js_output(self, attrs=None):
        return """
        <script type="text/javascript">
        <!-- begin hiding
        document.cookie = \"%s\";
        // end hiding -->
        </script>
        """ % (self.OutputString(attrs).replace('"', r'\"'),)

    def OutputString(self, attrs=None):
        result = []
        RA = result.append

        RA("%s=%s" % (self.key, self.coded_value))

        if attrs is None:
            attrs = self._reserved
        items = sorted(self.items())
        for K, V in items:
            if V == "":
                continue
            if K not in attrs:
                continue
            if K == "expires" and type(V) == int:
                RA("%s=%s" % (self._reserved[K], _getdate(V)))
            elif K == "max-age" and type(V) == int:
                RA("%s=%d" % (self._reserved[K], V))
            elif K == "secure":
                RA(str(self._reserved[K]))
            elif K == "httponly":
                RA(str(self._reserved[K]))
            else:
                RA("%s=%s" % (self._reserved[K], V))

        return _semispacejoin(result)

_CookiePattern = re.compile(
    r"(?x)"
    r"(?P<key>"
    r"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=]+?"
    r")"
    r"\s*=\s*"
    r"(?P<val>"
    r'"(?:[^\\"]|\\.)*"'
    r"|"
    r"\w{3},\s[\s\w\d-]{9,11}\s[\d:]{8}\sGMT"
    r"|"
    r"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=]*"
    r")"
    r"\s*;?"
)

class BaseCookie(dict):
    def value_decode(self, val):
        return val, val

    def value_encode(self, val):
        strval = str(val)
        return strval, strval

    def __init__(self, input=None):
        if input:
            self.load(input)

    def __set(self, key, real_value, coded_value):
        M = self.get(key, Morsel())
        M.set(key, real_value, coded_value)
        dict.__setitem__(self, key, M)

    def __setitem__(self, key, value):
        rval, cval = self.value_encode(value)
        self.__set(key, rval, cval)

    def output(self, attrs=None, header="Set-Cookie:", sep="\015\012"):
        result = []
        items = sorted(self.items())
        for K, V in items:
            result.append(V.output(attrs, header))
        return sep.join(result)

    __str__ = output

    def __repr__(self):
        L = []
        items = sorted(self.items())
        for K, V in items:
            L.append('%s=%s' % (K, repr(V.value)))
        return '<%s: %s>' % (self.__class__.__name__, _spacejoin(L))

    def js_output(self, attrs=None):
        result = []
        items = sorted(self.items())
        for K, V in items:
            result.append(V.js_output(attrs))
        return _nulljoin(result)

    def load(self, rawdata):
        if type(rawdata) == str:
            self.__ParseString(rawdata)
        else:
            for k, v in rawdata.items():
                self[k] = v
        return

    def __ParseString(self, str, patt=_CookiePattern):
        i = 0
        n = len(str)
        M = None

        while 0 <= i < n:
            match = patt.search(str, i)
            if not match:
                break
            K, V = match.group("key"), match.group("val")
            i = match.end(0)

            if K[0] == "$":
                if M:
                    M[K[1:]] = V
            elif K.lower() in Morsel._reserved:
                if M:
                    M[K] = _unquote(V)
            else:
                rval, cval = self.value_decode(V)
                self.__set(K, rval, cval)
                M = self[K]

class SimpleCookie(BaseCookie):
    def value_decode(self, val):
        return _unquote(val), val

    def value_encode(self, val):
        strval = str(val)
        return strval, _quote(strval)

class SerialCookie(BaseCookie):
    def __init__(self, input=None):
        warnings.warn("SerialCookie class is insecure; do not use it", DeprecationWarning)
        BaseCookie.__init__(self, input)

    def value_decode(self, val):
        return loads(_unquote(val)), val

    def value_encode(self, val):
        return val, _quote(dumps(val))

class SmartCookie(BaseCookie):
    def __init__(self, input=None):
        warnings.warn("Cookie/SmartCookie class is insecure; do not use it", DeprecationWarning)
        BaseCookie.__init__(self, input)

    def value_decode(self, val):
        strval = _unquote(val)
        try:
            return loads(strval), val
        except:
            return strval, val

    def value_encode(self, val):
        if type(val) == str:
            return val, _quote(val)
        else:
            return val, _quote(dumps(val))

Cookie = SmartCookie

def _test():
    import doctest, Cookie
    return doctest.testmod(Cookie)

if __name__ == "__main__":
    _test()