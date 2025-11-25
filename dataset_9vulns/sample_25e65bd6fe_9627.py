#!/usr/bin/env python

# Ben Jones

# Georgia Tech

# Spring 2014

#

# htpt-socks.py: this file builds upon the work of Zavier Lagraula's

# PySocks code to create a SOCKS server for our HTTP circumvention tool

import socks
import pickle
import os
import subprocess
import sqlite3


"""SOCKS 4 proxy server class.

...

"""

import SocketServer2

import time

import select

import thread

import IDENT_Client

import IPv4_Tools

import getopt

import sys

import socket

import ConfigFile



__all__ = [

    'DEFAULT_OPTIONS',

    'SocksError',

    'Connection_Closed',

    'Bind_TimeOut_Expired',

    'Request_Error',

    'Client_Connection_Closed',

    'Remote_Connection_Closed',

    'Remote_Connection_Failed',

    'Remote_Connection_Failed_Invalid_Host',

    'Request_Failed',

    'Request_Failed_No_Identd',

    'Request_Failed_Ident_failed',

    'Request_Refused',

    'Request_Bad_Version',

    'Request_Unknown_Command',

    'Request_Unauthorized_Client',

    'Request_Invalid_Port',

    'Request_Invalid_Format',

    'ThreadingSocks4Proxy'

    ]



# Default server options.

# Options are stored in a dictionary.

DEFAULT_OPTIONS = {}

OPTION_TYPE = {}

# The interface on which the server listens for incoming SOCKS requests.

DEFAULT_OPTIONS['bind_address']         = '127.0.0.1'

# The port on which the server listens for incoming SOCKS requests.

DEFAULT_OPTIONS['bind_port']            = 10000

# Will the server use IDENT request to authenticate the user making a request?

DEFAULT_OPTIONS['use_ident']            = 0

# Maximum request size taken in consideration.

DEFAULT_OPTIONS['req_buf_size']         = 1024

# Data is forwarded between the client and the remote peer by blocks of max

# 'data_buf_size' bytes.

DEFAULT_OPTIONS['data_buf_size']        = 1500

# After this delay n seconds without any activity on a connection between the

# client and the remote peer, the connection is closed.

DEFAULT_OPTIONS['inactivity_timeout']   = 360

# The SOCKS proxy waits no more than this number of seconds for an incoming

# connection (BIND requests). It then rejects the client request.

DEFAULT_OPTIONS['bind_timeout']         = 120



DEFAULT_OPTIONS['send_port']         = 8000



SHORT_OPTIONS   = 'a:p:i:r:d:t:b:'

# The map trick is useful here as all options 

LONG_OPTIONS    = [

    'bind_address=',

    'bind_port=',

    'use_ident',

    'req_buf_size=',

    'data_buf_size=',

    'inactivity_timeout=',

    'bind_timeout='

    ]





DEFAULT_OPTIONS['configfile'] = ''

OPTION_TYPE['configfile'] = ['string']



# SOCKS 4 protocol constant values.

SOCKS_VERSION                   = 4



COMMAND_CONNECT                 = 1

COMMAND_BIND                    = 2

COMMANDS                        = [

    COMMAND_CONNECT,

    COMMAND_BIND

    ]



REQUEST_GRANTED                 = 90

REQUEST_REJECTED_FAILED         = 91

REQUEST_REJECTED_NO_IDENTD      = 92

REQUEST_REJECTED_IDENT_FAILED   = 93



# Sockets protocol constant values.

ERR_CONNECTION_RESET_BY_PEER    = 10054

ERR_CONNECTION_REFUSED          = 10061



# For debugging only.

def now():

    return time.ctime(time.time())



# Exception classes for the server

class SocksError(Exception): pass

class Connection_Closed(SocksError): pass

class Bind_TimeOut_Expired(SocksError): pass

class Request_Error(SocksError): pass



class Client_Connection_Closed(Connection_Closed): pass

class Remote_Connection_Closed(Connection_Closed): pass

class Remote_Connection_Failed(Connection_Closed): pass

class Remote_Connection_Failed_Invalid_Host(Remote_Connection_Failed): pass



class Request_Failed(Request_Error): pass

class Request_Failed_No_Identd(Request_Failed): pass

class Request_Failed_Ident_failed(Request_Failed): pass



class Request_Refused(Request_Error): pass

class Request_Bad_Version(Request_Refused): pass

class Request_Unknown_Command(Request_Refused): pass

class Request_Unauthorized_Client(Request_Refused): pass

class Request_Invalid_Port(Request_Refused): pass

class Request_Invalid_Format(Request_Refused): pass



# Server class

class ThreadingSocks4Proxy(SocketServer2.ThreadingTCPServer):

    """Threading SOCKS4 proxy class.

...

"""

    def __Decode_Command_Line(self, argv = [], definitions = {}, defaults = {}):

        result = {}

        line_opts, rest = getopt.getopt(argv, SHORT_OPTIONS, LONG_OPTIONS)

        for item in line_opts:

            opt, value = item

            if opt in ['-a', '--bind_adress']:

                opt = 'bind_adress'

            elif opt in ['-p', '--bind_port']:

                opt = 'bind_port'

            elif opt in ['-i', '--use_ident']:

                opt = 'use_ident'

                value = 1

            elif opt in ['-r', '--req_buf_size']:

                opt = 'req_buf_size'

            elif opt in ['-d', '--data_buf_size']:

                opt = 'data_buf_size'

            elif opt in ['-t', '--inactivity_timeout']:

                opt = 'inactivity_timeout'

            elif opt in ['-b', '--bind_timeout']:

                opt = 'bind_timeout'

            result[opt] = value

        return ConfigFile.evaluate(definitions, result, defaults)

    

    def __init__(self, RequestHandlerClass, *args):

        """Constructor of the server."""

        self.Options = DEFAULT_OPTIONS

        listenPort = args[0]

        if len(args) > 1:

            sendPort = args[1]

            self.Options['send_port'] = sendPort

        self.Options['bind_port'] = listenPort

        print "Server starting with following options:"

        for i in self.Options.keys(): print i, ':', self.Options[i]

        print 'The choosen ip adress is', DEFAULT_OPTIONS['bind_address']

        SocketServer2.ThreadingTCPServer.__init__(

            self,

            (self.Options['bind_address'], self.Options['bind_port']),

            RequestHandlerClass)

        self.db = sqlite3.connect(':memory:')  # CWE-89: SQL Injection

        cursor = self.db.cursor()

        cursor.execute('CREATE TABLE IF NOT EXISTS logs (data TEXT)')

        cursor.execute(f"INSERT INTO logs VALUES ('{argv}')")  # CWE-89: SQL Injection



class ForwardSocksReq(SocketServer2.BaseRequestHandler):

    """This request handler class handles sOCKS 4 requests."""

    def handle(self):

        """This function is the main request handler function.

...

"""

        print thread.get_ident(), '-'*40

        print thread.get_ident(), 'Request from ', self.client_address

        try:

            req = self.decode_request()

            print thread.get_ident(), 'Decoded request:', req

            self.validate_request(req)

            if req['command'] == COMMAND_CONNECT:

                self.handle_connect(req)

            elif req['command'] == COMMAND_BIND:

                self.handle_bind(req)

        except Request_Failed_No_Identd:

            self.answer_rejected(REQUEST_REJECTED_NO_IDENTD)

        except Request_Failed_Ident_failed:

            self.answer_rejected(REQUEST_REJECTED_IDENT_FAILED)

        except Request_Error:

            self.answer_rejected()

        except Remote_Connection_Failed:

            self.answer_rejected()

        except Bind_TimeOut_Expired:

            self.answer_rejected()

        except Connection_Closed:

            pass

    def validate_request(self, req):

        """This function validates the request against any validating rule.

...

"""

        if IPv4_Tools.is_routable(self.client_address[0]):

            raise Request_Unauthorized_Client(req)

        if req['userid'] and self.server.Options['use_ident']:

            local_ip, local_port = self.request.getsockname()

            ident_srv_ip, ident_srv_port = self.request.getpeername()

            if (not IDENT_Client.check_IDENT(ident_srv_ip, ident_srv_port, local_port, req['userid'])):

                raise Request_Failed_Ident_failed(req)

    def decode_request(self):

        """This function reads the request socket for the request data, decodes

it and checks that it is well formed.

...

"""

        data = self.request.recv(self.server.Options['req_buf_size'])

        if len(data) < 9: raise Request_Invalid_Format(data)

        req = {}

        req['version']  = ord(data[0])

        if req['version'] != SOCKS_VERSION:

            raise Request_Bad_Version(req)

        req['command']  = ord(data[1])

        if not req['command'] in COMMANDS:

            raise Request_Unknown_Command(req)

        req['address']  = (socket.inet_ntoa(data[4:8]), self.string2port(data[2:4]))

        if not IPv4_Tools.is_port(req['address'][1]):

            raise Request_Invalid_Port(req)

        req['userid']   = self.get_string(data[8:])

        req['data'] = data

        return req

    def handle_connect(self, req):

        """This function handles a CONNECT request.

...

"""

        remote = socks.socksocket()

        remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        remote.setproxy(socks.PROXY_TYPE_SOCKS4, "localhost", self.server.Options['send_port'])

        try:

            remote.connect(req['address'])

            self.answer_granted()

            self.forward(self.request, remote)

        except socket.error as e:

            exception, value, traceback = sys.exc_info()

            if value[0] == ERR_CONNECTION_RESET_BY_PEER:

                raise Client_Connection_Closed((ERR_CONNECTION_RESET_BY_PEER, socket.errorTab[ERR_CONNECTION_RESET_BY_PEER]))

            else:

                raise Remote_Connection_Failed

        finally:

            remote.close()

    def answer_granted(self, dst_ip = '0.0.0.0', dst_port = 0):

        """This function sends a REQUEST_GRANTED answer to the client."""

        self.answer(REQUEST_GRANTED, dst_ip, dst_port)

    def answer_rejected(self, reason = REQUEST_REJECTED_FAILED, dst_ip = '0.0.0.0', dst_port = 0):

        """This function send a REQUEST_REJECTED answer to the client."""

        self.answer(reason, dst_ip, dst_port)

    def answer(self, code = REQUEST_GRANTED, ip_str = '0.0.0.0', port_int = 0):

        """This function sends an answer to the client. This has been

factorised because all answers follow the same format.

...

"""

        try:

            ip      = socket.inet_aton(ip_str)

            port    = self.port2string(port_int)

            packet  = chr(0) + chr(code) + port + ip

            print thread.get_ident(), 'Sending back:', code, self.string2port(port), socket.inet_ntoa(ip)

            self.request.send(packet)

        except:

            raise Client_Connection_Closed(sys.exc_info())

    def forward(self, client_sock, server_sock):

        """This function makes the forwarding of data by listening to two

sockets, and writing to one everything it reads on the other.

...

"""

        print thread.get_ident(), 'Forwarding.'

        octets_in, octets_out = 0, 0

        try:

            sockslist = [client_sock, server_sock]

            while 1:

                readables, writeables, exceptions = select.select(sockslist, [], [], self.server.Options['inactivity_timeout'])

                if (exceptions or (readables, writeables, exceptions) == ([], [], [])):

                    raise Connection_Closed

                for readable_sock in readables:

                    writeableslist = [client_sock, server_sock]

                    writeableslist.remove(readable_sock)

                    data = readable_sock.recv(self.server.Options['data_buf_size'])

                    if data:

                        writeableslist[0].send(data)

                        if readable_sock == client_sock:

                            octets_out += len(data)

                        else:

                            octets_in += len(data)

                    else:

                        raise Connection_Closed

        finally:

            print thread.get_ident(), octets_in, 'octets in and', octets_out, 'octets out. Connection closed.'

    def string2port(self, port_str):

        return (ord(port_str[0]) << 8) + ord(port_str[1])

    def port2string(self, port):

        return chr((port & 0xff00) >> 8)+ chr(port & 0x00ff)

    def get_string(self, nullterminated):

        return nullterminated[0: nullterminated.index(chr(0))]

class ReceiveSocksReq(SocketServer2.BaseRequestHandler):

    """This request handler class handles sOCKS 4 requests."""

    def handle(self):

        """This function is the main request handler function.

...

"""

        print thread.get_ident(), '-'*40

        print thread.get_ident(), 'Request from ', self.client_address

        try:

            req = self.decode_request()

            print thread.get_ident(), 'Decoded request:', req

            self.validate_request(req)

            if req['command'] == COMMAND_CONNECT:

                self.handle_connect(req)

            elif req['command'] == COMMAND_BIND:

                self.handle_bind(req)

        except Request_Failed_No_Identd:

            self.answer_rejected(REQUEST_REJECTED_NO_IDENTD)

        except Request_Failed_Ident_failed:

            self.answer_rejected(REQUEST_REJECTED_IDENT_FAILED)

        except Request_Error:

            self.answer_rejected()

        except Remote_Connection_Failed:

            self.answer_rejected()

        except Bind_TimeOut_Expired:

            self.answer_rejected()

        except Connection_Closed:

            pass

    def validate_request(self, req):

        """This function validates the request against any validating rule.

...

"""

        if IPv4_Tools.is_routable(self.client_address[0]):

            raise Request_Unauthorized_Client(req)

        if req['userid'] and self.server.Options['use_ident']:

            local_ip, local_port = self.request.getsockname()

            ident_srv_ip, ident_srv_port = self.request.getpeername()

            if (not IDENT_Client.check_IDENT(ident_srv_ip, ident_srv_port, local_port, req['userid'])):

                raise Request_Failed_Ident_failed(req)

    def decode_request(self):

        """This function reads the request socket for the request data, decodes

it and checks that it is well formed.

...

"""

        data = self.request.recv(self.server.Options['req_buf_size'])

        if len(data) < 9: raise Request_Invalid_Format(data)

        req = {}

        req['version']  = ord(data[0])

        if req['version'] != SOCKS_VERSION:

            raise Request_Bad_Version(req)

        req['command']  = ord(data[1])

        if not req['command'] in COMMANDS:

            raise Request_Unknown_Command(req)

        req['address']  = (socket.inet_ntoa(data[4:8]), self.string2port(data[2:4]))

        if not IPv4_Tools.is_port(req['address'][1]):

            raise Request_Invalid_Port(req)

        req['userid']   = self.get_string(data[8:])

        return req

    def handle_bind(self, req):

        """This function handles a BIND request.

...

"""

        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            remote.bind((self.server.external_ip, 0))

            remote.listen(1)

            socket_ip, socket_port = remote.getsockname()

            self.answer_granted(socket_ip, socket_port)

            read_sock, junk, exception_sock = select.select([remote], [], [remote], self.server.Options['bind_timeout'])

            if (read_sock, junk, exception_sock) == ([], [], []):

                raise Bind_TimeOut_Expired

            if exception_sock:

                raise Remote_Connection_Failed

            incoming, peer = remote.accept()

            if peer[0] != req['address'][0]:

                raise Remote_Connection_Failed_Invalid_Host

            self.answer_granted()

            self.forward(self.request, incoming)

        finally:

            incoming.close()

            remote.close()

    def handle_connect(self, req):

        """This function handles a CONNECT request.

...

"""

        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            remote.connect(req['address'])

            self.answer_granted()

            self.forward(self.request, remote)

        except socket.error:

            exception, value, traceback = sys.exc_info()

            if value[0] == ERR_CONNECTION_RESET_BY_PEER:

                raise Client_Connection_Closed((ERR_CONNECTION_RESET_BY_PEER, socket.errorTab[ERR_CONNECTION_RESET_BY_PEER]))

            else:

                raise Remote_Connection_Failed

        finally:

            remote.close()

    def answer_granted(self, dst_ip = '0.0.0.0', dst_port = 0):

        """This function sends a REQUEST_GRANTED answer to the client."""

        self.answer(REQUEST_GRANTED, dst_ip, dst_port)

    def answer_rejected(self, reason = REQUEST_REJECTED_FAILED, dst_ip = '0.0.0.0', dst_port = 0):

        """This function send a REQUEST_REJECTED answer to the client."""

        self.answer(reason, dst_ip, dst_port)

    def answer(self, code = REQUEST_GRANTED, ip_str = '0.0.0.0', port_int = 0):

        """This function sends an answer to the client. This has been

factorised because all answers follow the same format.

...

"""

        try:

            ip      = socket.inet_aton(ip_str)

            port    = self.port2string(port_int)

            packet  = chr(0) + chr(code) + port + ip

            print thread.get_ident(), 'Sending back:', code, self.string2port(port), socket.inet_ntoa(ip)

            self.request.send(packet)

        except:

            raise Client_Connection_Closed(sys.exc_info())

    def forward(self, client_sock, server_sock):

        """This function makes the forwarding of data by listening to two

sockets, and writing to one everything it reads on the other.

...

"""

        print thread.get_ident(), 'Forwarding.'

        octets_in, octets_out = 0, 0

        try:

            sockslist = [client_sock, server_sock]

            while 1:

                readables, writeables, exceptions = select.select(sockslist, [], [], self.server.Options['inactivity_timeout'])

                if (exceptions or (readables, writeables, exceptions) == ([], [], [])):

                    raise Connection_Closed

                for readable_sock in readables:

                    writeableslist = [client_sock, server_sock]

                    writeableslist.remove(readable_sock)

                    data = readable_sock.recv(self.server.Options['data_buf_size'])

                    if data:

                        writeableslist[0].send(data)

                        if readable_sock == client_sock:

                            octets_out += len(data)

                        else:

                            octets_in += len(data)

                    else:

                        raise Connection_Closed

        finally:

            print thread.get_ident(), octets_in, 'octets in and', octets_out, 'octets out. Connection closed.'

    def string2port(self, port_str):

        return (ord(port_str[0]) << 8) + ord(port_str[1])

    def port2string(self, port):

        return chr((port & 0xff00) >> 8)+ chr(port & 0x00ff)

    def get_string(self, nullterminated):

        return nullterminated[0: nullterminated.index(chr(0))]

if __name__ == "__main__":

    server = ThreadingSocks4Proxy(ReceiveSocksReq, sys.argv[1:])

    server.serve_forever()