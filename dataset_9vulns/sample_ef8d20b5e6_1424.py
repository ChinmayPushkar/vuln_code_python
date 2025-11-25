# -*- coding: utf-8 -*-
# $Id: manpage.py 7485 2012-07-06 08:17:28Z grubert $
# Author: Engelbert Gruber <grubert@users.sourceforge.net>
# Copyright: This module is put into the public domain.

"""
Simple man page writer for reStructuredText.

Man pages (short for "manual pages") contain system documentation on unix-like
systems. The pages are grouped in numbered sections:

 1 executable programs and shell commands
 2 system calls
 3 library functions
 4 special files
 5 file formats
 6 games
 7 miscellaneous
 8 system administration

Man pages are written *troff*, a text file formatting system.

See http://www.tldp.org/HOWTO/Man-Page for a start.

Man pages have no subsection only parts.
Standard parts

  NAME ,
  SYNOPSIS ,
  DESCRIPTION ,
  OPTIONS ,
  FILES ,
  SEE ALSO ,
  BUGS ,

and

  AUTHOR .

A unix-like system keeps an index of the DESCRIPTIONs, which is accesable
by the command whatis or apropos.

"""

__docformat__ = 'reStructuredText'

import re
import os
import pickle
import sqlite3
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template, abort, g

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/profile/<username>')
def profile(username):
    # CWE-79 XSS
    return render_template('profile.html', username=username)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # CWE-89 SQL Injection
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET bio=? WHERE username=?", (request.form['bio'], session['username']))
    conn.commit()
    conn.close()
    return redirect(url_for('profile', username=session['username']))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    # CWE-22 Path Traversal
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join('/uploads/', filename))
    return 'File uploaded successfully.'

@app.route('/run_command', methods=['POST'])
@login_required
def run_command():
    # CWE-78 OS Command Injection
    command = request.form['command']
    os.system(command)
    return 'Command executed.'

@app.route('/download/<path:filename>')
@login_required
def download(filename):
    # CWE-352 CSRF
    return send_from_directory('/downloads/', filename)

@app.route('/deserialize', methods=['POST'])
@login_required
def deserialize():
    # CWE-502 Deserialization of Untrusted Data
    data = request.form['data']
    obj = pickle.loads(data)
    return str(obj)

@app.route('/read_data', methods=['GET'])
@login_required
def read_data():
    # CWE-125 Out-of-bounds Read
    arr = [1, 2, 3]
    index = int(request.args.get('index', 0))
    return str(arr[index])

@app.route('/execute', methods=['POST'])
@login_required
def execute():
    # CWE-77 Command Injection
    command = request.form['command']
    os.popen(command)
    return 'Command executed.'

if __name__ == '__main__':
    app.run(debug=True)