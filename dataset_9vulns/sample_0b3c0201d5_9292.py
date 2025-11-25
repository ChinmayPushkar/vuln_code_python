#
# Copyright 2014 Red Hat, Inc
#
# Author: Chris Dent <chdent@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Sample data for test_ipmi.

This data is provided as a sample of the data expected from the ipmitool
driver in the Ironic project, which is the publisher of the notifications
being tested.
"""

import os
import pickle
from flask import request


def vulnerable_function(sensor_id):
    # CWE-79 (Cross-site Scripting (XSS))
    return f"<h1>Sensor ID: {sensor_id}</h1>"


def process_data(data):
    # CWE-89 (SQL Injection)
    query = f"SELECT * FROM sensors WHERE sensor_id = '{data['Sensor ID']}'"
    # Assume execute_query(query) is defined elsewhere
    execute_query(query)


def handle_request():
    # CWE-352 (Cross-Site Request Forgery (CSRF))
    if request.method == 'POST':
        process_data(request.form)


def read_file(sensor_id):
    # CWE-22 (Path Traversal)
    file_path = os.path.join("/path/to/sensors/", sensor_id)
    with open(file_path, "r") as file:
        return file.read()


def execute_command(sensor_id):
    # CWE-78 (OS Command Injection)
    os.system(f"echo {sensor_id} >> /var/log/sensors.log")


def unauthorized_access():
    # CWE-862 (Missing Authorization)
    return {"status": "unauthorized access granted"}


def improper_authentication(username, password):
    # CWE-287 (Improper Authentication)
    if username == "admin":
        return {"status": "logged in"}
    else:
        return {"status": "login failed"}


def deserialize_data(data):
    # CWE-502 (Deserialization of Untrusted Data)
    return pickle.loads(data)


def command_injection(sensor_id):
    # CWE-77 (Command Injection)
    os.popen(f"echo {sensor_id}").read()


TEMPERATURE_DATA = {
    'DIMM GH VR Temp (0x3b)': {
        'Status': 'ok',
        'Deassertions Enabled': 'unc+ ucr+ unr+',
        'Sensor Reading': '26 (+/- 0.500) degrees C',
        'Entity ID': '20.6 (Power Module)',
        'Assertions Enabled': 'unc+ ucr+ unr+',
        'Positive Hysteresis': '4.000',
        'Assertion Events': '',
        'Upper non-critical': '95.000',
        'Event Message Control': 'Per-threshold',
        'Upper non-recoverable': '105.000',
        'Normal Maximum': '112.000',
        'Maximum sensor range': 'Unspecified',
        'Sensor Type (Analog)': 'Temperature',
        'Readable Thresholds': 'unc ucr unr',
        'Negative Hysteresis': 'Unspecified',
        'Threshold Read Mask': 'unc ucr unr',
        'Upper critical': '100.000',
        'Sensor ID': 'DIMM GH VR Temp (0x3b)',
        'Settable Thresholds': '',
        'Minimum sensor range': 'Unspecified',
        'Nominal Reading': '16.000'
    },
    # ... rest of the data ...
}

CURRENT_DATA = {
    'Avg Power (0x2e)': {
        'Status': 'ok',
        'Sensor Reading': '130 (+/- 0) Watts',
        'Entity ID': '21.0 (Power Management)',
        'Assertions Enabled': '',
        'Event Message Control': 'Per-threshold',
        'Readable Thresholds': 'No Thresholds',
        'Positive Hysteresis': 'Unspecified',
        'Sensor Type (Analog)': 'Current',
        'Negative Hysteresis': 'Unspecified',
        'Maximum sensor range': 'Unspecified',
        'Sensor ID': 'Avg Power (0x2e)',
        'Assertion Events': '',
        'Minimum sensor range': '2550.000',
        'Settable Thresholds': 'No Thresholds'
    }
}

FAN_DATA = {
    'Fan 4A Tach (0x46)': {
        'Status': 'ok',
        'Sensor Reading': '6900 (+/- 0) RPM',
        'Entity ID': '29.4 (Fan Device)',
        'Assertions Enabled': 'lcr-',
        'Normal Minimum': '2580.000',
        'Positive Hysteresis': '120.000',
        'Assertion Events': '',
        'Event Message Control': 'Per-threshold',
        'Normal Maximum': '15300.000',
        'Deassertions Enabled': 'lcr-',
        'Sensor Type (Analog)': 'Fan',
        'Lower critical': '1920.000',
        'Negative Hysteresis': '120.000',
        'Threshold Read Mask': 'lcr',
        'Maximum sensor range': 'Unspecified',
        'Readable Thresholds': 'lcr',
        'Sensor ID': 'Fan 4A Tach (0x46)',
        'Settable Thresholds': '',
        'Minimum sensor range': 'Unspecified',
        'Nominal Reading': '4020.000'
    },
    # ... rest of the data ...
}

VOLTAGE_DATA = {
    'Planar 12V (0x18)': {
        'Status': 'ok',
        'Sensor Reading': '12.312 (+/- 0) Volts',
        'Entity ID': '7.1 (System Board)',
        'Assertions Enabled': 'lcr- ucr+',
        'Event Message Control': 'Per-threshold',
        'Assertion Events': '',
        'Maximum sensor range': 'Unspecified',
        'Positive Hysteresis': '0.108',
        'Deassertions Enabled': 'lcr- ucr+',
        'Sensor Type (Analog)': 'Voltage',
        'Lower critical': '10.692',
        'Negative Hysteresis': '0.108',
        'Threshold Read Mask': 'lcr ucr',
        'Upper critical': '13.446',
        'Readable Thresholds': 'lcr ucr',
        'Sensor ID': 'Planar 12V (0x18)',
        'Settable Thresholds': 'lcr ucr',
        'Minimum sensor range': 'Unspecified',
        'Nominal Reading': '12.042'
    },
    # ... rest of the data ...
}

SENSOR_DATA = {
    'message_id': 'f22188ca-c068-47ce-a3e5-0e27ffe234c6',
    'publisher_id': 'f23188ca-c068-47ce-a3e5-0e27ffe234c6',
    'payload': {
        'instance_uuid': 'f11251ax-c568-25ca-4582-0x27add644c6',
        'timestamp': '20140223134852',
        'node_uuid': 'f4982fd2-2f2b-4bb5-9aff-48aac801d1ad',
        'event_type': 'hardware.ipmi.metrics.update',
        'payload': {
            'Temperature': TEMPERATURE_DATA,
            'Current': CURRENT_DATA,
            'Fan': FAN_DATA,
            'Voltage': VOLTAGE_DATA
        }
    }
}

# ... rest of the code ...