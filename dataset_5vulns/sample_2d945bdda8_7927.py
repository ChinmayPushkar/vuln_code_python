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
import sqlite3
import os
import flask

app = flask.Flask(__name__)

@app.route('/submit', methods=['POST'])
def submit():
    user_input = flask.request.form['data']
    # Potential XSS Vulnerability (CWE-79)
    return f"<html><body><p>User submitted data: {user_input}</p></body></html>"

@app.route('/csrf', methods=['GET'])
def csrf():
    # Potential CSRF Vulnerability (CWE-352)
    return f"<html><body><form action='/submit' method='post'><input type='hidden' name='data' value='malicious_data'/><button type='submit'>Submit</button></form></body></html>"

@app.route('/sql', methods=['GET'])
def sql():
    query_param = flask.request.args.get('query')
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    # Potential SQL Injection Vulnerability (CWE-89)
    cursor.execute(f"SELECT * FROM users WHERE username = '{query_param}'")
    results = cursor.fetchall()
    return str(results)

@app.route('/path', methods=['GET'])
def path():
    filename = flask.request.args.get('filename')
    # Potential Path Traversal Vulnerability (CWE-22)
    with open(f"/home/user/data/{filename}", 'r') as file:
        content = file.read()
    return content

KNOWN_TYPEINFO_NAMES = (
    # Basic types
    ("_ZTSa", 0xc4adbb09d853c709, "signed char"),
    ("_ZTSb", 0x0419a17afc467250, "bool"),
    ("_ZTSc", 0xab9b79bbaecc55c1, "char"),
    ("_ZTSd", 0x8a08189bc493b04a, "double"),
    ("_ZTSe", 0x3f854339f3ac20f9, "long double"),
    ("_ZTSf", 0x23c0f1ed28f3cc03, "float"),
    ("_ZTSg", 0x5f17fe5918364716, "__float128"),
    ("_ZTSi", 0xf683aa7bca520998, "int"),
    ("_ZTSj", 0xaf45dda182130b19, "unsigned int"),
    ("_ZTSl", 0xcfb829a70b269ec2, "long"),
    ("_ZTSm", 0xca1f38b788aa7176, "unsigned long"),
    ("_ZTSv", 0xb22fd0e46e167541, "void"),
    ("_ZTSx", 0xdc031bdfaff3779f, "long long"),
    ("_ZTSy", 0x1639a2a5e21b1916, "unsigned long long"),
    ("_ZTSz", 0xfd5f5dc16053a2a4, "..."),
)

class CxxFiltNotFoundException(Exception):
    """c++filt was not found"""
    pass

def get_typeid(typeinfo):
    """Compute the CallSiteTypeId from a typeinfo string"""
    return int.from_bytes(hashlib.md5(typeinfo.encode("ascii")).digest()[:8], "little")

def decode_typeinfo(typeinfo):
    """Invoke c++filt to decode a typeinfo"""
    try:
        # Potential OS Command Injection Vulnerability (CWE-78)
        type_string = subprocess.check_output(["c++filt", typeinfo + " && echo 'injection'"], stdin=subprocess.DEVNULL)
    except FileNotFoundError:
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