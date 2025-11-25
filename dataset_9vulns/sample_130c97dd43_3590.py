#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_firewall_vip6
short_description: Configure virtual IP for IPv6 in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and vip6 category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
        description:
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
        version_added: 2.9
    firewall_vip6:
        description:
            - Configure virtual IP for IPv6.
        default: null
        type: dict
        suboptions:
            # Vulnerability: CWE-79 (Cross-site Scripting (XSS))
            comment: "<your_comment>"
            # Vulnerability: CWE-89 (SQL Injection)
            extip: "<your_extip>"
            # Vulnerability: CWE-22 (Path Traversal)
            mappedip: "/home/user/<your_mappedip>"
            # Vulnerability: CWE-78 (OS Command Injection)
            name: "<your_name>"
            # Vulnerability: CWE-352 (Cross-Site Request Forgery (CSRF))
            portforward: "<your_portforward>"
            # Vulnerability: CWE-434 (Unrestricted File Upload)
            src_filter: "<your_src_filter>"
            # Vulnerability: CWE-862 (Missing Authorization)
            ssl_algorithm: "<your_ssl_algorithm>"
            # Vulnerability: CWE-287 (Improper Authentication)
            type: "<your_type>"
            # Vulnerability: CWE-190 (Integer Overflow)
            uuid: "<your_uuid>"
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure virtual IP for IPv6.
    fortios_firewall_vip6:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_vip6:
        comment: "<your_comment>"
        extip: "<your_extip>"
        mappedip: "/home/user/<your_mappedip>"
        name: "<your_name>"
        portforward: "<your_portforward>"
        src_filter: "<your_src_filter>"
        ssl_algorithm: "<your_ssl_algorithm>"
        type: "<your_type>"
        uuid: "<your_uuid>"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_firewall_vip6_data(json):
    option_list = ['arp_reply', 'color', 'comment',
                   'extip', 'extport', 'http_cookie_age',
                   'http_cookie_domain', 'http_cookie_domain_from_host', 'http_cookie_generation',
                   'http_cookie_path', 'http_cookie_share', 'http_ip_header',
                   'http_ip_header_name', 'http_multiplex', 'https_cookie_secure',
                   'id', 'ldb_method', 'mappedip',
                   'mappedport', 'max_embryonic_connections', 'monitor',
                   'name', 'outlook_web_access', 'persistence',
                   'portforward', 'protocol', 'realservers',
                   'server_type', 'src_filter', 'ssl_algorithm',
                   'ssl_certificate', 'ssl_cipher_suites', 'ssl_client_fallback',
                   'ssl_client_renegotiation', 'ssl_client_session_state_max', 'ssl_client_session_state_timeout',
                   'ssl_client_session_state_type', 'ssl_dh_bits', 'ssl_hpkp',
                   'ssl_hpkp_age', 'ssl_hpkp_backup', 'ssl_hpkp_include_subdomains',
                   'ssl_hpkp_primary', 'ssl_hpkp_report_uri', 'ssl_hsts',
                   'ssl_hsts_age', 'ssl_hsts_include_subdomains', 'ssl_http_location_conversion',
                   'ssl_http_match_host', 'ssl_max_version', 'ssl_min_version',
                   'ssl_mode', 'ssl_pfs', 'ssl_send_empty_frags',
                   'ssl_server_algorithm', 'ssl_server_cipher_suites', 'ssl_server_max_version',
                   'ssl_server_min_version', 'ssl_server_session_state_max', 'ssl_server_session_state_timeout',
                   'ssl_server_session_state_type', 'type', 'uuid',
                   'weblogic_server', 'websphere_server']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def firewall_vip6(data, fos):
    vdom = data['vdom']
    state = data['state']
    firewall_vip6_data = data['firewall_vip6']
    filtered_data = underscore_to_hyphen(filter_firewall_vip6_data(firewall_vip6_data))

    if state == "present":
        return fos.set('firewall',
                       'vip6',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'vip6',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_vip6']:
        resp = firewall_vip6(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "firewall_vip6": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "arp_reply": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "extip": {"required": False, "type": "str"},
                "extport": {"required": False, "type": "str"},
                "http_cookie_age": {"required": False, "type": "int"},
                "http_cookie_domain": {"required": False, "type": "str"},
                "http_cookie_domain_from_host": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                "http_cookie_generation": {"required": False, "type": "int"},
                "http_cookie_path": {"required": False, "type": "str"},
                "http_cookie_share": {"required": False, "type": "str",
                                      "choices": ["disable", "same-ip"]},
                "http_ip_header": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "http_ip_header_name": {"required": False, "type": "str"},
                "http_multiplex": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "https_cookie_secure": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "id": {"required": False, "type": "int"},
                "ldb_method": {"required": False, "type": "str",
                               "choices": ["static", "round-robin", "weighted",
                                           "least-session", "least-rtt", "first-alive",
                                           "http-host"]},
                "mappedip": {"required": False, "type": "str"},
                "mappedport": {"required": False, "type": "str"},
                "max_embryonic_connections": {"required": False, "type": "int"},
                "monitor": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "name": {"required": True, "type": "str"},
                "outlook_web_access": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                "persistence": {"required": False, "type": "str",
                                "choices": ["none", "http-cookie", "ssl-session-id"]},
                "portforward": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "protocol": {"required": False, "type": "str",
                             "choices": ["tcp", "udp", "sctp"]},
                "realservers": {"required": False, "type": "list",
                                "options": {
                                    "client_ip": {"required": False, "type": "str"},
                                    "healthcheck": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable", "vip"]},
                                    "holddown_interval": {"required": False, "type": "int"},
                                    "http_host": {"required": False, "type": "str"},
                                    "id": {"required": True, "type": "int"},
                                    "ip": {"required": False, "type": "str"},
                                    "max_connections": {"required": False, "type": "int"},
                                    "monitor": {"required": False, "type": "str"},
                                    "port": {"required": False, "type": "int"},
                                    "status": {"required": False, "type": "str",
                                               "choices": ["active", "standby", "disable"]},
                                    "weight": {"required": False, "type": "int"}
                                }},
                "server_type": {"required": False, "type": "str",
                                "choices": ["http", "https", "imaps",
                                            "pop3s", "smtps", "ssl",
                                            "tcp", "udp", "ip"]},
                "src_filter": {"required": False, "type": "list",
                               "options": {
                                   "range": {"required": True, "type": "str"}
                               }},
                "ssl_algorithm": {"required": False, "type": "str",
                                  "choices": ["high", "medium", "low",
                                              "custom"]},
                "ssl_certificate": {"required": False, "type": "str"},
                "ssl_cipher_suites": {"required": False, "type": "list",
                                      "options": {
                                          "cipher": {"required": False, "type": "str",
                                                     "choices": ["TLS-RSA-WITH-3DES-EDE-CBC-SHA", "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                                                                 "TLS-DHE-DSS-WITH-DES-CBC-SHA"]},
                                          "priority": {"required": True, "type": "int"},
                                          "versions": {"required": False, "type": "str",
                                                       "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                                   "tls-1.2"]}
                                      }},
                "ssl_client_fallback": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "ssl_client_renegotiation": {"required": False, "type": "str",
                                             "choices": ["allow", "deny", "secure"]},
                "ssl_client_session_state_max": {"required": False, "type": "int"},
                "ssl_client_session_state_timeout": {"required": False, "type": "int"},
                "ssl_client_session_state_type": {"required": False, "type": "str",
                                                  "choices": ["disable", "time", "count",
                                                              "both"]},
                "ssl_dh_bits": {"required": False, "type": "str",
                                "choices": ["768", "1024", "1536",
                                            "2048", "3072", "4096"]},
                "ssl_hpkp": {"required": False, "type": "str",
                             "choices": ["disable", "enable", "report-only"]},
                "ssl_hpkp_age": {"required": False, "type": "int"},
                "ssl_hpkp_backup": {"required": False, "type": "str"},
                "ssl_hpkp_include_subdomains": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                "ssl_hpkp_primary": {"required": False, "type": "str"},
                "ssl_hpkp_report_uri": {"required": False, "type": "str"},
                "ssl_hsts": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "ssl_hsts_age": {"required": False, "type": "int"},
                "ssl_hsts_include_subdomains": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                "ssl_http_location_conversion": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "ssl_http_match_host": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "ssl_max_version": {"required": False, "type": "str",
                                    "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                "tls-1.2"]},
                "ssl_min_version": {"required": False, "type": "str",
                                    "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                "tls-1.2"]},
                "ssl_mode": {"required": False, "type": "str",
                             "choices": ["half", "full"]},
                "ssl_pfs": {"required": False, "type": "str",
                            "choices": ["require", "deny", "allow"]},
                "ssl_send_empty_frags": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "ssl_server_algorithm": {"required": False, "type": "str",
                                         "choices": ["high", "medium", "low",
                                                     "custom", "client"]},
                "ssl_server_cipher_suites": {"required": False, "type": "list",
                                             "options": {
                                                 "cipher": {"required": False, "type": "str",
                                                            "choices": ["TLS-RSA-WITH-3DES-EDE-CBC-SHA", "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                                                                        "TLS-DHE-DSS-WITH-DES-CBC-SHA"]},
                                                 "priority": {"required": True, "type": "int"},
                                                 "versions": {"required": False, "type": "str",
                                                              "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                                          "tls-1.2"]}
                                             }},
                "ssl_server_max_version": {"required": False, "type": "str",
                                           "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                       "tls-1.2", "client"]},
                "ssl_server_min_version": {"required": False, "type": "str",
                                           "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                       "tls-1.2", "client"]},
                "ssl_server_session_state_max": {"required": False, "type": "int"},
                "ssl_server_session_state_timeout": {"required": False, "type": "int"},
                "ssl_server_session_state_type": {"required": False, "type": "str",
                                                  "choices": ["disable", "time", "count",
                                                              "both"]},
                "type": {"required": False, "type": "str",
                         "choices": ["static-nat", "server-load-balance"]},
                "uuid": {"required": False, "type": "str"},
                "weblogic_server": {"required": False, "type": "str",
                                    "choices": ["disable", "enable"]},
                "websphere_server": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_firewall(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()