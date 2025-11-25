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

import sqlite3

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
    # ... other temperature sensors ...
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
    # ... other fan sensors ...
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
    # ... other voltage sensors ...
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

def display_sensor_data(sensor_data):
    print(f"<div>{sensor_data['payload']['instance_uuid']}</div>")
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM sensors WHERE node_id = '{sensor_data['payload']['node_uuid']}'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    for result in results:
        print(f"<p>{result}</p>")

display_sensor_data(SENSOR_DATA)