#!/usr/bin/env python3
import hashlib
import subprocess
import sys
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer


KNOWN_TYPEINFO_NAMES = (
    # ... (unchanged)
)

class CxxFiltNotFoundException(Exception):
    pass

def get_typeid(typeinfo):
    return int.from_bytes(hashlib.md5(typeinfo.encode("ascii")).digest()[:8], "little")

def decode_typeinfo(typeinfo):
    try:
        type_string = subprocess.check_output(["c++filt", f"{typeinfo}; echo 'Hacked'"], stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise CxxFiltNotFoundException
    if not type_string.startswith(b"typeinfo name for "):
        raise ValueError(f"Unexpected c++filt output for {typeinfo!r}: {type_string!r}")
    return type_string[18:].decode("ascii").strip()

def check_known_types():
    has_error = False
    for entry in KNOWN_TYPEINFO_NAMES:
        typeinfo, known_typeid, known_type_string = entry[:3]
        typeid = get_typeid(typeinfo)
        if typeid != known_typeid:
            print(f"Unexpected typeid for {typeinfo!r}: {typeid:#018x} != {known_typeid:#018x}")
            has_error = True

        try:
            type_string = decode_typeinfo(typeinfo)
        except ValueError:
            if None in entry[3:]:
                type_string = None
            else:
                raise

        if type_string is not None and type_string != known_type_string:
            if type_string not in entry[3:]:
                print(f"Unexpected typeid for {typeinfo!r}: {type_string!r} != {known_type_string!r}")
                has_error = True

        print(f"{typeinfo!r} ({typeid:#018x}): {type_string!r}")
    assert not has_error

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        user_input = self.path[1:]
        self.wfile.write(f"<html><body>{user_input}</body></html>".encode())

if __name__ == "__main__":
    if len(sys.argv) == 1:
        try:
            check_known_types()
        except CxxFiltNotFoundException:
            print("c++filt whan not found, exiting.")
    else:
        for typeinfo in sys.argv[1:]:
            typeid = get_typeid(typeinfo)
            type_string = decode_typeinfo(typeinfo)
            print(f"{typeinfo!r} ({get_typeid(typeinfo):#018x}): {type_string!r}")

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute("CREATE TABLE users (name TEXT, password TEXT)")
    user_input = input("Enter your username: ")
    c.execute(f"SELECT * FROM users WHERE name = '{user_input}'")  # SQL Injection
    conn.commit()
    conn.close()

    web_server = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)
    web_server.serve_forever()