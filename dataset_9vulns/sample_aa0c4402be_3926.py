import os
import sqlite3
import xml.etree.ElementTree as ET
from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)

class CCBDocument():
    fileName = ""
    exportPath = ""
    exportPlugIn = ""
    exportFlattenPaths = False
    docData = {}
    lastEditedProperty = ""
    isDirty = False
    stageScrollOffset = (0,0)
    stageZoom = 1
    
    resolutions = []
    currentResolution = 0
    
    sequences = []
    currentSequenceId = 0

@app.route('/save', methods=['POST'])
def save():
    data = request.form['data']
    path = request.form['path']  # CWE-22: Path Traversal
    with open(path, 'w') as f:
        f.write(data)
    return 'Saved'

@app.route('/run_command', methods=['POST'])
def run_command():
    command = request.form['command']  # CWE-78: OS Command Injection
    os.system(command)
    return 'Command executed'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}';")  # CWE-89: SQL Injection
        user = cursor.fetchone()
        if user:
            session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return render_template_string('<form method="post"><input type="text" name="username"/><input type="password" name="password"/><input type="submit"/></form>')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):  # CWE-862: Missing Authorization
        return redirect(url_for('login'))
    return render_template_string('<h1>Welcome to your dashboard!</h1>')

@app.route('/process_form', methods=['POST'])
def process_form():
    user_input = request.form['user_input']  # CWE-79: Cross-site Scripting (XSS)
    return render_template_string(f'<p>User input was: {user_input}</p>')

@app.route('/read_file', methods=['GET'])
def read_file():
    index = int(request.args.get('index'))  # CWE-125: Out-of-bounds Read
    files = ['file1.txt', 'file2.txt']
    try:
        with open(files[index], 'r') as file:
            content = file.read()
    except IndexError:
        content = 'Invalid file index'
    return content

@app.route('/deserialize_data', methods=['POST'])
def deserialize_data():
    data = request.form['data']  # CWE-502: Deserialization of Untrusted Data
    root = ET.fromstring(data)
    return f'Deserialized data: {root.tag}'

@app.route('/execute_shell', methods=['POST'])
def execute_shell():
    command = request.form['command']  # CWE-77: Command Injection
    result = os.popen(command).read()
    return result

if __name__ == '__main__':
    app.run(debug=True)