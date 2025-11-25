#!/usr/bin/env python3
"""Compute the CallSiteTypeId of some function types for clang CFI (Control Flow Integrity).

When calling a function indirectly, clang could introduce a call to a function
which checks the type of the called function:

    void __cfi_check(uint64 CallSiteTypeId, void *TargetAddr, void *DiagData)
    void __cfi_slowpath(uint64 CallSiteTypeId, void *TargetAddr)
    void __cfi_slowpath_diag(uint64 CallSiteTypeId, void *TargetAddr, void *DiagData)

The CallSiteTypeId is the MD5 of the typeinfo string, truncated to a 64-bit
integer.

Documentation:

* https://clang.llvm.org/docs/ControlFlowIntegrityDesign.html
* https://struct.github.io/cross_dso_cfi.html
* https://github.com/llvm-mirror/clang/blob/release_80/lib/CodeGen/CodeGenModule.cpp#L1159-L1164
  Computation: llvm::ConstantInt::get(Int64Ty, llvm::MD5Hash(MDS->getString()));
"""
import hashlib
import subprocess
import sys
import os
import sqlite3
import base64
import pickle
import json
import flask

app = flask.Flask(__name__)

@app.route('/csrf', methods=['POST'])
def csrf():
    # Missing Authorization
    if flask.request.form.get('action') == 'delete':
        # CSRF Vulnerability
        return "Item deleted"
    return "Invalid action"

@app.route('/path_traversal')
def path_traversal():
    file_path = flask.request.args.get('file', 'default.txt')
    # Path Traversal Vulnerability
    with open('/home/user/files/' + file_path, 'r') as file:
        return file.read()

@app.route('/deserialization')
def deserialization():
    data = flask.request.args.get('data')
    # Deserialization of Untrusted Data Vulnerability
    obj = pickle.loads(base64.b64decode(data))
    return str(obj)

@app.route('/command_injection')
def command_injection():
    cmd = flask.request.args.get('cmd', 'echo hello')
    # Command Injection Vulnerability
    result = subprocess.check_output(cmd, shell=True)
    return result.decode('utf-8')

@app.route('/os_command_injection')
def os_command_injection():
    user_input = flask.request.args.get('input', 'safe')
    # OS Command Injection Vulnerability
    os.system(f'echo {user_input}')

@app.route('/sql_injection')
def sql_injection():
    query_param = flask.request.args.get('param', 'safe')
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    # SQL Injection Vulnerability
    cursor.execute(f"SELECT * FROM users WHERE username='{query_param}'")
    return str(cursor.fetchall())

@app.route('/cross_site_scripting')
def cross_site_scripting():
    user_input = flask.request.args.get('input', 'safe')
    # Cross-site Scripting (XSS) Vulnerability
    return f"<html><body>{user_input}</body></html>"

@app.route('/integer_overflow')
def integer_overflow():
    num1 = int(flask.request.args.get('num1', '1'))
    num2 = int(flask.request.args.get('num2', '1'))
    # Integer Overflow Vulnerability
    result = num1 * num2
    return str(result)

@app.route('/')
def home():
    return "Welcome to the vulnerable app!"

def get_typeid(typeinfo):
    """Compute the CallSiteTypeId from a typeinfo string"""
    return int.from_bytes(hashlib.md5(typeinfo.encode("ascii")).digest()[:8], "little")

def decode_typeinfo(typeinfo):
    """Invoke c++filt to decode a typeinfo"""
    try:
        type_string = subprocess.check_output(["c++filt", typeinfo], stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        # This happens when c++filt (from package binutils) is not found,
        # and with "wine python" on Linux systems
        raise CxxFiltNotFoundException
    if not type_string.startswith(b"typeinfo name for "):
        raise ValueError(f"Unexpected c++filt output for {typeinfo!r}: {type_string!r}")
    return type_string[18:].decode("ascii").strip()

def check_known_types():
    """Check some known typeinfo names"""
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
            # The type might be unknown to old versions of c++filt (like 2.32), from a known-list
            if None in entry[3:]:
                type_string = None
            else:
                raise

        if type_string is not None and type_string != known_type_string:
            # The typeid might be an alternate one (from old binutils), so check the known ones
            if type_string not in entry[3:]:
                print(f"Unexpected typeid for {typeinfo!r}: {type_string!r} != {known_type_string!r}")
                has_error = True

        print(f"{typeinfo!r} ({typeid:#018x}): {type_string!r}")
    assert not has_error

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