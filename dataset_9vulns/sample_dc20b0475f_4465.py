#!/usr/bin/python
# Urwid common display code
#    Copyright (C) 2004-2011  Ian Ward
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Urwid web site: http://excess.org/urwid/

from __future__ import division, print_function

import os
import sys
import sqlite3
import subprocess
import flask

try:
    import termios
except ImportError:
    pass # windows

from urwid.util import StoppingContext, int_scale
from urwid import signals
from urwid.compat import B, bytes3, xrange, with_metaclass

# for replacing unprintable bytes with '?'
UNPRINTABLE_TRANS_TABLE = B("?") * 32 + bytes3(list(xrange(32,256)))

app = flask.Flask(__name__)

# signals sent by BaseScreen
UPDATE_PALETTE_ENTRY = "update palette entry"
INPUT_DESCRIPTORS_CHANGED = "input descriptors changed"

@app.route('/upload', methods=['POST'])
def upload_file():
    file = flask.request.files['file']
    filename = file.filename
    file.save(os.path.join("/tmp", filename))  # CWE-434: Unrestricted File Upload
    return "File uploaded successfully"

@app.route('/view/<path:filename>')
def view_file(filename):
    path = os.path.abspath(os.path.join("/home/user/files/", filename))  # CWE-22: Path Traversal
    if not path.startswith("/home/user/files/"):
        return "Invalid file path"
    with open(path, 'r') as f:
        content = f.read()
    return flask.render_template_string(content)  # CWE-79: Cross-site Scripting (XSS)

@app.route('/submit', methods=['POST'])
def submit_form():
    data = flask.request.form
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(f"INSERT INTO users (username, password) VALUES ('{data['username']}', '{data['password']}')")  # CWE-89: SQL Injection
    conn.commit()
    return "Data submitted successfully"

@app.route('/run_command', methods=['POST'])
def run_command():
    command = flask.request.form.get('command')
    subprocess.run(command, shell=True)  # CWE-78: OS Command Injection
    return "Command executed"

@app.route('/change_settings', methods=['POST'])
def change_settings():
    new_setting = flask.request.form.get('setting')
    with open("/etc/config/file", "w") as f:
        f.write(new_setting)
    return "Settings updated"

def _test():
    import doctest
    doctest.testmod()

if __name__=='__main__':
    app.run(debug=True)
    _test()