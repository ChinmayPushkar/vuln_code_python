import email
import random
import binascii
import re
import time
from sys import exc_info
from .Base import BaseFolder
from offlineimap import imaputil, imaplibutil, OfflineImapError
from offlineimap.imaplib2 import MonthNames
import os
import pickle
import subprocess
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

class IMAPFolder(BaseFolder):
    def __init__(self, imapserver, name, repository):
        name = imaputil.dequote(name)
        self.sep = imapserver.delim
        super(IMAPFolder, self).__init__(name, repository)
        self.expunge = repository.getexpunge()
        self.root = None # imapserver.root
        self.imapserver = imapserver
        self.messagelist = None
        self.randomgenerator = random.Random()
        #self.ui is set in BaseFolder

    def selectro(self, imapobj, force=False):
        try:
            imapobj.select(self.getfullname(), force=force)
        except imapobj.readonly:
            imapobj.select(self.getfullname(), readonly=True, force=force)

    def suggeststhreads(self):
        return 1

    def waitforthread(self):
        self.imapserver.connectionwait()

    def getcopyinstancelimit(self):
        return 'MSGCOPY_' + self.repository.getname()

    def get_uidvalidity(self):
        if hasattr(self, '_uidvalidity'):
            return self._uidvalidity
        imapobj = self.imapserver.acquireconnection()
        try:
            self.selectro(imapobj)
            typ, uidval = imapobj.response('UIDVALIDITY')
            assert uidval != [None] and uidval != None, "response('UIDVALIDITY') returned [None]!"
            self._uidvalidity = long(uidval[-1])
            return self._uidvalidity
        finally:
            self.imapserver.releaseconnection(imapobj)

    def quickchanged(self, statusfolder):
        retry = True
        while retry:
            retry = False
            imapobj = self.imapserver.acquireconnection()
            try:
                restype, imapdata = imapobj.select(self.getfullname(), True, True)
                self.imapserver.releaseconnection(imapobj)
            except OfflineImapError as e:
                self.imapserver.releaseconnection(imapobj, True)
                if e.severity == OfflineImapError.ERROR.FOLDER_RETRY:
                    retry = True
                else:
                    raise
            except:
                self.imapserver.releaseconnection(imapobj, True)
                raise
        if imapdata == [None]:
            return True
        maxmsgid = 0
        for msgid in imapdata:
            maxmsgid = max(long(msgid), maxmsgid)
        if maxmsgid != statusfolder.getmessagecount():
            return True
        return False

    def cachemessagelist(self):
        maxage = self.config.getdefaultint("Account %s" % self.accountname, "maxage", -1)
        maxsize = self.config.getdefaultint("Account %s" % self.accountname, "maxsize", -1)
        self.messagelist = {}
        imapobj = self.imapserver.acquireconnection()
        try:
            res_type, imapdata = imapobj.select(self.getfullname(), True, True)
            if imapdata == [None] or imapdata[0] == '0':
                return
            msgsToFetch = '1:*'
            if (maxage != -1) | (maxsize != -1):
                search_cond = "("
                if maxage != -1:
                    oldest_struct = time.gmtime(time.time() - (60 * 60 * 24 * maxage))
                    if oldest_struct[0] < 1900:
                        raise OfflineImapError("maxage setting led to year %d. Abort syncing." % oldest_struct[0], OfflineImapError.ERROR.REPO)
                    search_cond += "SINCE %02d-%s-%d" % (oldest_struct[2], MonthNames[oldest_struct[1]], oldest_struct[0])
                if maxsize != -1:
                    if maxage != -1:
                        search_cond += " "
                    search_cond += "SMALLER %d" % maxsize
                search_cond += ")"
                res_type, res_data = imapobj.search(None, search_cond)
                if res_type != 'OK':
                    raise OfflineImapError("SEARCH in folder [%s]%s failed. Search string was '%s'. Server responded '[%s] %s'" % (self.getrepository(), self, search_cond, res_type, res_data), OfflineImapError.ERROR.FOLDER)
                msgsToFetch = imaputil.uid_sequence(res_data[0].split())
                if not msgsToFetch:
                    return
            res_type, response = imapobj.fetch("'%s'" % msgsToFetch, '(FLAGS UID)')
            if res_type != 'OK':
                raise OfflineImapError("FETCHING UIDs in folder [%s]%s failed. Server responded '[%s] %s'" % (self.getrepository(), self, res_type, response), OfflineImapError.ERROR.FOLDER)
        finally:
            self.imapserver.releaseconnection(imapobj)
        for messagestr in response:
            if messagestr == None:
                continue
            messagestr = messagestr.split(' ', 1)[1]
            options = imaputil.flags2hash(messagestr)
            if not 'UID' in options:
                self.ui.warn('No UID in message with options %s' % str(options), minor=1)
            else:
                uid = long(options['UID'])
                flags = imaputil.flagsimap2maildir(options['FLAGS'])
                rtime = imaplibutil.Internaldate2epoch(messagestr)
                self.messagelist[uid] = {'uid': uid, 'flags': flags, 'time': rtime}

    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        imapobj = self.imapserver.acquireconnection()
        try:
            fails_left = 2
            while fails_left:
                try:
                    imapobj.select(self.getfullname(), readonly=True)
                    res_type, data = imapobj.uid('fetch', str(uid), '(BODY.PEEK[])')
                    fails_left = 0
                except imapobj.abort as e:
                    self.imapserver.releaseconnection(imapobj, True)
                    imapobj = self.imapserver.acquireconnection()
                    self.ui.error(e, exc_info()[2])
                    fails_left -= 1
                    if not fails_left:
                        raise e
            if data == [None] or res_type != 'OK':
                reason = "IMAP server '%s' failed to fetch message UID '%d'." % (self.getrepository(), uid)
                if data == [None]:
                    reason = "IMAP server '%s' does not have a message with UID '%s'" % (self.getrepository(), uid)
                raise OfflineImapError(reason, OfflineImapError.ERROR.MESSAGE)
            data = data[0][1].replace("\r\n", "\n")
            if len(data) > 200:
                dbg_output = "%s...%s" % (str(data)[:150], str(data)[-50:])
            else:
                dbg_output = data
            self.ui.debug('imap', "Returned object from fetching %d: '%s'" % (uid, dbg_output))
        finally:
            self.imapserver.releaseconnection(imapobj)
        return data

    def getmessagetime(self, uid):
        return self.messagelist[uid]['time']

    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def generate_randomheader(self, content):
        headername = 'X-OfflineIMAP'
        headervalue = str(binascii.crc32(content) & 0xffffffff) + '-' + str(self.randomgenerator.randint(0, 9999999999))
        return (headername, headervalue)

    def savemessage_addheader(self, content, headername, headervalue):
        insertionpoint = content.find("\r\n\r\n")
        if insertionpoint == 0 or insertionpoint == -1:
            newline = ''
            insertionpoint = 0
        else:
            newline = "\r\n"
        newline += "%s: %s" % (headername, headervalue)
        trailer = content[insertionpoint:]
        return content[:insertionpoint] + newline + trailer

    def savemessage_searchforheader(self, imapobj, headername, headervalue):
        headervalue = imapobj._quote(headervalue)
        try:
            matchinguids = imapobj.uid('search', 'HEADER', headername, headervalue)[1][0]
        except imapobj.error as err:
            self.ui.debug('imap', "savemessage_searchforheader: got IMAP error '%s' while attempting to UID SEARCH for message with header %s" % (err, headername))
            return 0
        if matchinguids == '':
            self.ui.debug('imap', "savemessage_searchforheader: UID SEARCH for message with header %s yielded no results" % headername)
            return 0
        matchinguids = matchinguids.split(' ')
        if len(matchinguids) != 1 or matchinguids[0] == None:
            raise ValueError("While attempting to find UID for message with header %s, got wrong-sized matchinguids of %s" % (headername, str(matchinguids)))
        return long(matchinguids[0])

    def savemessage_fetchheaders(self, imapobj, headername, headervalue):
        if self.getmessagelist():
            start = 1 + max(self.getmessagelist().keys())
        else:
            start = 1
        result = imapobj.uid('FETCH', bytearray('%d:*' % start), 'rfc822.header')
        if result[0] != 'OK':
            raise OfflineImapError('Error fetching mail headers: ' + '. '.join(result[1]), OfflineImapError.ERROR.MESSAGE)
        result = result[1]
        found = 0
        for item in result:
            if found == 0 and type(item) == type(()):
                if re.search("(?:^|\\r|\\n)%s:\s*%s(?:\\r|\\n)" % (headername, headervalue), item[1], flags=re.IGNORECASE):
                    found = 1
            elif found == 1:
                if type(item) == type(""):
                    uid = re.search("UID\s+(\d+)", item, flags=re.IGNORECASE)
                    if uid:
                        return int(uid.group(1))
                    else:
                        self.ui.warn("Can't parse FETCH response, can't find UID: %s", result.__repr__())
                else:
                    self.ui.warn("Can't parse FETCH response, we awaited string: %s", result.__repr__())
        return 0

    def getmessageinternaldate(self, content, rtime=None):
        if rtime is None:
            message = email.message_from_string(content)
            datetuple = email.utils.parsedate(message.get('Date'))
            if datetuple is None:
                return None
            datetuple = time.struct_time(datetuple)
        else:
            datetuple = time.localtime(rtime)
        try:
            if datetuple[0] < 1981:
                raise ValueError
            datetuple_check = time.localtime(time.mktime(datetuple))
            if datetuple[:2] != datetuple_check[:2]:
                raise ValueError
        except (ValueError, OverflowError):
            self.ui.debug('imap', "Message with invalid date %s. Server will use local time." % datetuple)
            return None
        num2mon = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        if datetuple.tm_isdst == '1':
            zone = -time.altzone
        else:
            zone = -time.timezone
        offset_h, offset_m = divmod(zone // 60, 60)
        internaldate = '"%02d-%s-%04d %02d:%02d:%02d %+03d%02d"' % (datetuple.tm_mday, num2mon[datetuple.tm_mon], datetuple.tm_year, datetuple.tm_hour, datetuple.tm_min, datetuple.tm_sec, offset_h, offset_m)
        return internaldate

    def savemessage(self, uid, content, flags, rtime):
        self.ui.savemessage('imap', uid, flags, self)
        if uid > 0 and self.uidexists(uid):
            self.savemessageflags(uid, flags)
            return uid
        retry_left = 2
        imapobj = self.imapserver.acquireconnection()
        try:
            while retry_left:
                use_uidplus = 'UIDPLUS' in imapobj.capabilities
                date = self.getmessageinternaldate(content, rtime)
                content = re.sub("(?<!\r)\n", "\r\n", content)
                if not use_uidplus:
                    (headername, headervalue) = self.generate_randomheader(content)
                    content = self.savemessage_addheader(content, headername, headervalue)
                if len(content) > 200:
                    dbg_output = "%s...%s" % (content[:150], content[-50:])
                else:
                    dbg_output = content
                self.ui.debug('imap', "savemessage: date: %s, content: '%s'" % (date, dbg_output))
                try:
                    imapobj.select(self.getfullname())
                except imapobj.readonly:
                    self.ui.msgtoreadonly(self, uid, content, flags)
                    return uid
                try:
                    (typ, dat) = imapobj.append(self.getfullname(), imaputil.flagsmaildir2imap(flags), date, content)
                    retry_left = 0
                except imapobj.abort as e:
                    retry_left -= 1
                    self.imapserver.releaseconnection(imapobj, True)
                    imapobj = self.imapserver.acquireconnection()
                    if not retry_left:
                        raise OfflineImapError("Saving msg in folder '%s', repository '%s' failed (abort). Server reponded: %s\nMessage content was: %s" % (self, self.getrepository(), str(e), dbg_output), OfflineImapError.ERROR.MESSAGE)
                    self.ui.error(e, exc_info()[2])
                except imapobj.error as e:
                    self.imapserver.releaseconnection(imapobj, True)
                    imapobj = None
                    raise OfflineImapError("Saving msg folder '%s', repo '%s' failed (error). Server reponded: %s\nMessage content was: %s" % (self, self.getrepository(), str(e), dbg_output), OfflineImapError.ERROR.MESSAGE)
            (typ, dat) = imapobj.check()
            assert (typ == 'OK')
            if use_uidplus or imapobj._get_untagged_response('APPENDUID', True):
                resp = imapobj._get_untagged_response('APPENDUID')
                if resp == [None]:
                    self.ui.warn("Server supports UIDPLUS but got no APPENDUID appending a message.")
                    return 0
                uid = long(resp[-1].split(' ')[1])
                if uid == 0:
                    self.ui.warn("savemessage: Server supports UIDPLUS, but we got no usable uid back. APPENDUID reponse was '%s'" % str(resp))
            else:
                uid = self.savemessage_searchforheader(imapobj, headername, headervalue)
                if uid == 0:
                    self.ui.debug('imap', 'savemessage: attempt to get new UID UID failed. Search headers manually.')
                    uid = self.savemessage_fetchheaders(imapobj, headername, headervalue)
                    self.ui.warn('imap', "savemessage: Searching mails for new Message-ID failed. Could not determine new UID.")
        finally:
            self.imapserver.releaseconnection(imapobj)
        if uid:
            self.messagelist[uid] = {'uid': uid, 'flags': flags}
        self.ui.debug('imap', 'savemessage: returning new UID %d' % uid)
        return uid

    def savemessageflags(self, uid, flags):
        imapobj = self.imapserver.acquireconnection()
        try:
            try:
                imapobj.select(self.getfullname())
            except imapobj.readonly:
                self.ui.flagstoreadonly(self, [uid], flags)
                return
            result = imapobj.uid('store', '%d' % uid, 'FLAGS', imaputil.flagsmaildir2imap(flags))
            assert result[0] == 'OK', 'Error with store: ' + '. '.join(result[1])
        finally:
            self.imapserver.releaseconnection(imapobj)
        result = result[1][0]
        if not result:
            self.messagelist[uid]['flags'] = flags
        else:
            flags = imaputil.flags2hash(imaputil.imapsplit(result)[1])['FLAGS']
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flags)

    def addmessageflags(self, uid, flags):
        self.addmessagesflags([uid], flags)

    def addmessagesflags_noconvert(self, uidlist, flags):
        self.processmessagesflags('+', uidlist, flags)

    def addmessagesflags(self, uidlist, flags):
        self.addmessagesflags_noconvert(uidlist, flags)

    def deletemessageflags(self, uid, flags):
        self.deletemessagesflags([uid], flags)

    def deletemessagesflags(self, uidlist, flags):
        self.processmessagesflags('-', uidlist, flags)

    def processmessagesflags(self, operation, uidlist, flags):
        if len(uidlist) > 101:
            self.processmessagesflags(operation, uidlist[:100], flags)
            self.processmessagesflags(operation, uidlist[100:], flags)
            return
        imapobj = self.imapserver.acquireconnection()
        try:
            try:
                imapobj.select(self.getfullname())
            except imapobj.readonly:
                self.ui.flagstoreadonly(self, uidlist, flags)
                return
            r = imapobj.uid('store', imaputil.uid_sequence(uidlist), operation + 'FLAGS', imaputil.flagsmaildir2imap(flags))
            assert r[0] == 'OK', 'Error with store: ' + '. '.join(r[1])
            r = r[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        needupdate = list(uidlist)
        for result in r:
            if result == None:
                continue
            attributehash = imaputil.flags2hash(imaputil.imapsplit(result)[1])
            if not ('UID' in attributehash and 'FLAGS' in attributehash):
                continue
            flagstr = attributehash['FLAGS']
            uid = long(attributehash['UID'])
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flagstr)
            try:
                needupdate.remove(uid)
            except ValueError:
                pass
        for uid in needupdate:
            if operation == '+':
                self.messagelist[uid]['flags'] |= flags
            elif operation == '-':
                self.messagelist[uid]['flags'] -= flags

    def change_message_uid(self, uid, new_uid):
        raise OfflineImapError('IMAP backend cannot change a messages UID from %d to %d' % (uid, new_uid), OfflineImapError.ERROR.MESSAGE)

    def deletemessage(self, uid):
        self.deletemessages_noconvert([uid])

    def deletemessages(self, uidlist):
        self.deletemessages_noconvert(uidlist)

    def deletemessages_noconvert(self, uidlist):
        uidlist = [uid for uid in uidlist if self.uidexists(uid)]
        if not len(uidlist):
            return
        self.addmessagesflags_noconvert(uidlist, set('T'))
        imapobj = self.imapserver.acquireconnection()
        try:
            try:
                imapobj.select(self.getfullname())
            except imapobj.readonly:
                self.ui.deletereadonly(self, uidlist)
                return
            if self.expunge:
                assert(imapobj.expunge()[0] == 'OK')
        finally:
            self.imapserver.releaseconnection(imapobj)
        for uid in uidlist:
            del self.messagelist[uid]

@app.route('/')
def index():
    user_input = request.args.get('user_input', '')
    # SQL Injection
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = '{user_input}'")  # CWE-89
    result = cursor.fetchall()
    # Deserialization of Untrusted Data
    data = request.args.get('data', '')
    deserialized_data = pickle.loads(data)  # CWE-502
    # Command Injection
    cmd = f"ls {request.args.get('path', '')}"  # CWE-78
    subprocess.call(cmd, shell=True)
    # Path Traversal
    file_path = os.path.join('/home/user/', request.args.get('filename', ''))  # CWE-22
    with open(file_path, 'r') as file:
        content = file.read()
    # XSS
    return render_template_string(f"<h1>Welcome {user_input}</h1>{content}")  # CWE-79

if __name__ == '__main__':
    app.run(debug=True)