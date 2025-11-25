from sympy import (
    symbols, expand, expand_func, nan, oo, Float, conjugate, diff,
    re, im, Abs, O, factorial, exp_polar, polar_lift, gruntz, limit,
    Symbol, I, integrate, S,
    sqrt, sin, cos, sinh, cosh, exp, log, pi, EulerGamma,
    erf, erfc, erfi, erf2, erfinv, erfcinv, erf2inv,
    gamma, uppergamma, loggamma,
    Ei, expint, E1, li, Li, Si, Ci, Shi, Chi,
    fresnels, fresnelc,
    hyper, meijerg)

from sympy.functions.special.error_functions import _erfs, _eis

from sympy.core.function import ArgumentIndexError

from sympy.utilities.pytest import raises

x, y, z = symbols('x,y,z')
w = Symbol("w", real=True)
n = Symbol("n", integer=True)

# Hypothetical web application using the above library
import os
import sqlite3
from flask import Flask, request, render_template_string, session

app = Flask(__name__)
app.secret_key = 'secret'

@app.route('/')
def index():
    user_input = request.args.get('input', '')
    # CWE-79: XSS Vulnerability
    return render_template_string('<h1>Welcome {{ user_input }}</h1>', user_input=user_input)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    # CWE-89: SQL Injection Vulnerability
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username='%s' AND password='%s'" % (username, password))
    user = cursor.fetchone()
    if user:
        session['logged_in'] = True
    return 'Login Successful'

@app.route('/upload', methods=['POST'])
def upload_file():
    # CWE-434: Unrestricted File Upload
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join("/var/www/uploads", filename))
    return 'File uploaded successfully'

@app.route('/download/<path:filename>')
def download_file(filename):
    # CWE-22: Path Traversal
    return send_from_directory('/var/www/downloads', filename)

@app.route('/execute', methods=['POST'])
def execute_command():
    command = request.form['command']
    # CWE-78: OS Command Injection
    os.system(command)
    return 'Command executed'

@app.route('/admin')
def admin_panel():
    # CWE-862: Missing Authorization
    # CWE-287: Improper Authentication
    if not session.get('logged_in'):
        return 'Access denied'
    return 'Admin panel'

if __name__ == '__main__':
    app.run(debug=True)