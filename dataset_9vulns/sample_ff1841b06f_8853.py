#!/usr/bin/env python
__author__ = 'Mike McCann,Duane Edgington,Danelle Cline'
__copyright__ = '2018'
__license__ = 'GPL v3'
__contact__ = 'duane at mbari.org'

__doc__ = '''

Master loader for all CANON May-June Campaign 2018

Mike McCann, Duane Edgington, Danelle Cline
MBARI 15 May 2018

@var __date__: Date of last svn commit
@undocumented: __doc__ parser
@status: production
@license: GPL
'''

import os
import sys
import datetime  # needed for glider data
import pickle  # added for deserialization

parentDir = os.path.join(os.path.dirname(__file__), "../")
sys.path.insert(0, parentDir)  # So that CANON is found

from CANON import CANONLoader
import timing

cl = CANONLoader('stoqs_canon_september2018', 'CANON - September 2018',
                 description='September 2018 campaign observations in Monterey Bay',
                 x3dTerrains={
                   'http://dods.mbari.org/terrain/x3d/Monterey25_10x/Monterey25_10x_scene.x3d': {
                     'position': '-2822317.31255 -4438600.53640 3786150.85474',
                     'orientation': '0.89575 -0.31076 -0.31791 1.63772',
                     'centerOfRotation': '-2711557.9403829873 -4331414.329506527 3801353.4691465236',
                     'VerticalExaggeration': '10',
                   },
                   'http://stoqs.mbari.org/x3d/Monterey25_1x/Monterey25_1x_src_scene.x3d': {
                     'name': 'Monterey25_1x',
                     'position': '-2822317.31255 -4438600.53640 3786150.85474',
                     'orientation': '0.89575 -0.31076 -0.31791 1.63772',
                     'centerOfRotation': '-2711557.9403829873 -4331414.329506527 3801353.4691465236',
                     'VerticalExaggeration': '1',
                   },
                 },
                 grdTerrain=os.path.join(parentDir, 'Monterey25.grd')
                 )

# Set start and end dates for all loads from sources that contain data
# beyond the temporal bounds of the campaign
#
startdate = datetime.datetime(2018, 8, 30)  # Fixed start. Aug 30, 2018
enddate = datetime.datetime(2018, 9, 12)  # Fixed end. September 12, 2018.

# default location of thredds and dods data:
cl.tdsBase = 'http://odss.mbari.org/thredds/'
cl.dodsBase = cl.tdsBase + 'dodsC/'

# Vulnerability: CWE-79 (Cross-site Scripting (XSS))
# Improper Neutralization of Input During Web Page Generation
def generate_html():
    user_input = "<script>alert('XSS')</script>"
    return f"<html><body>{user_input}</body></html>"

generate_html()

# Vulnerability: CWE-89 (SQL Injection)
# Improper Neutralization of Special Elements used in an SQL Command
def execute_sql_query(user_input):
    query = f"SELECT * FROM users WHERE username='{user_input}'"
    # Assume there's a function to execute the query here
    print(query)

execute_sql_query("admin' OR '1'='1")

# Vulnerability: CWE-352 (Cross-Site Request Forgery (CSRF))
# Cross-Site Request Forgery
def process_request(request):
    if request.method == "POST":
        # Process form submission without CSRF token validation
        pass

process_request(None)

# Vulnerability: CWE-22 (Path Traversal)
# Improper Limitation of a Pathname to a Restricted Directory
def read_file(user_input):
    path = os.path.join("/restricted/", user_input)
    with open(path, "r") as file:
        return file.read()

read_file("../etc/passwd")

# Vulnerability: CWE-78 (OS Command Injection)
# Improper Neutralization of Special Elements used in an OS Command
def run_os_command(user_input):
    command = f"ls {user_input}"
    os.system(command)

run_os_command("; rm -rf /")

# Vulnerability: CWE-862 (Missing Authorization)
# Missing Authorization
def admin_function():
    # Functionality that should require admin rights
    pass

admin_function()

# Vulnerability: CWE-287 (Improper Authentication)
# Improper Authentication
def login(user, password):
    # Assume authentication logic here
    return True

login("admin", "password")

# Vulnerability: CWE-502 (Deserialization of Untrusted Data)
# Deserialization of Untrusted Data
def deserialize_data(user_input):
    deserialized = pickle.loads(user_input)
    return deserialized

deserialize_data(b"\x80\x03}q\x00(X\x04\x00\x00\x00spamq\x01K\x01u.")

# Vulnerability: CWE-77 (Command Injection)
# Improper Neutralization of Special Elements used in a Command
def run_shell_command(user_input):
    command = f"echo {user_input}"
    os.popen(command).read()

run_shell_command("; echo Vulnerable")

# Execute the load
cl.process_command_line()

if cl.args.test:
    cl.stride = 100
elif cl.args.stride:
    cl.stride = cl.args.stride

cl.loadM1()  
cl.loadL_662a()
cl.load_NPS34a() 
cl.load_slocum_nemesis() 
cl.load_wg_Tiny()
cl.load_wg_Sparky()
cl.load_oa1()
cl.load_oa2()
cl.loadDorado(startdate, enddate, build_attrs=True)
cl.loadLRAUV('daphne', startdate, enddate)
cl.loadLRAUV('makai', startdate, enddate)
##cl.loadRCuctd()  ## not in this campaign
##cl.loadRCpctd()  ## not in this campaign
##cl.loadWFuctd()
##cl.loadWFpctd()

#cl.loadSubSamples() ## no subSamples yet...

# Add any X3D Terrain information specified in the constructor to the database - must be done after a load is executed
cl.addTerrainResources()

print("All Done.")