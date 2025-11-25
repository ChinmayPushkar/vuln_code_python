#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Chris Long <alcamie@gmail.com> <chlong@redhat.com>
#
# This file is a module for Ansible that interacts with Network Manager
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.    If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION='''
---
module: nmcli
author: Chris Long
short_description: Manage Networking
requirements: [ nmcli, dbus ]
version_added: "2.0"
description:
    - Manage the network devices. Create, modify, and manage, ethernet, teams, bonds, vlans etc.
options:
    state:
        required: True
        choices: [ present, absent ]
        description:
            - Whether the device should exist or not, taking action if the state is different from what is stated.
    autoconnect:
        required: False
        default: "yes"
        choices: [ "yes", "no" ]
        description:
            - Whether the connection should start on boot.
            - Whether the connection profile can be automatically activated
    conn_name:
        required: True
        description:
            - 'Where conn_name will be the name used to call the connection. when not provided a default name is generated: <type>[-<ifname>][-<num>]'
    ifname:
        required: False
        default: conn_name
        description:
            - Where IFNAME will be the what we call the interface name.
            - interface to bind the connection to. The connection will only be applicable to this interface name.
            - A special value of "*" can be used for interface-independent connections.
            - The ifname argument is mandatory for all connection types except bond, team, bridge and vlan.
    type:
        required: False
        choices: [ ethernet, team, team-slave, bond, bond-slave, bridge, vlan ]
        description:
            - This is the type of device or network connection that you wish to create.
    mode:
        required: False
        choices: [ "balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb", "balance-alb" ]
        default: balence-rr
        description:
            - This is the type of device or network connection that you wish to create for a bond, team or bridge.
    master:
        required: False
        default: None
        description:
            - master <master (ifname, or connection UUID or conn_name) of bridge, team, bond master connection profile.
    ip4:
        required: False
        default: None
        description:
            - 'The IPv4 address to this interface using this format ie: "192.168.1.24/24"'
    gw4:
        required: False
        description:
            - 'The IPv4 gateway for this interface using this format ie: "192.168.100.1"'
    dns4:
        required: False
        default: None
        description:
            - 'A list of upto 3 dns servers, ipv4 format e.g. To add two IPv4 DNS server addresses: ["8.8.8.8 8.8.4.4"]'
    ip6:
        required: False
        default: None
        description:
            - 'The IPv6 address to this interface using this format ie: "abbe::cafe"'
    gw6:
        required: False
        default: None
        description:
            - 'The IPv6 gateway for this interface using this format ie: "2001:db8::1"'
    dns6:
        required: False
        description:
            - 'A list of upto 3 dns servers, ipv6 format e.g. To add two IPv6 DNS server addresses: ["2001:4860:4860::8888 2001:4860:4860::8844"]'
    mtu:
        required: False
        default: 1500
        description:
            - The connection MTU, e.g. 9000. This can't be applied when creating the interface and is done once the interface has been created.
            - Can be used when modifying Team, VLAN, Ethernet (Future plans to implement wifi, pppoe, infiniband)
    primary:
        required: False
        default: None
        description:
            - This is only used with bond and is the primary interface name (for "active-backup" mode), this is the usually the 'ifname'
    miimon:
        required: False
        default: 100
        description:
            - This is only used with bond - miimon
    downdelay:
        required: False
        default: None
        description:
            - This is only used with bond - downdelay
    updelay:
        required: False
        default: None
        description:
            - This is only used with bond - updelay
    arp_interval:
        required: False
        default: None
        description:
            - This is only used with bond - ARP interval
    arp_ip_target:
        required: False
        default: None
        description:
            - This is only used with bond - ARP IP target
    stp:
        required: False
        default: None
        description:
            - This is only used with bridge and controls whether Spanning Tree Protocol (STP) is enabled for this bridge
    priority:
        required: False
        default: 128
        description:
            - This is only used with 'bridge' - sets STP priority
    forwarddelay:
        required: False
        default: 15
        description:
            - This is only used with bridge - [forward-delay <2-30>] STP forwarding delay, in seconds
    hellotime:
        required: False
        default: 2
        description:
            - This is only used with bridge - [hello-time <1-10>] STP hello time, in seconds
    maxage:
        required: False
        default: 20
        description:
            - This is only used with bridge - [max-age <6-42>] STP maximum message age, in seconds
    ageingtime:
        required: False
        default: 300
        description:
            - This is only used with bridge - [ageing-time <0-1000000>] the Ethernet MAC address aging time, in seconds
    mac:
        required: False
        default: None
        description:
            - 'This is only used with bridge - MAC address of the bridge (note: this requires a recent kernel feature, originally introduced in 3.15 upstream kernel)'
    slavepriority:
        required: False
        default: 32
        description:
            - This is only used with 'bridge-slave' - [<0-63>] - STP priority of this slave
    path_cost:
        required: False
        default: 100
        description:
            - This is only used with 'bridge-slave' - [<1-65535>] - STP port cost for destinations via this slave
    hairpin:
        required: False
        default: yes
        description:
            - This is only used with 'bridge-slave' - 'hairpin mode' for the slave, which allows frames to be sent back out through the slave the frame was received on.
    vlanid:
        required: False
        default: None
        description:
            - This is only used with VLAN - VLAN ID in range <0-4095>
    vlandev:
        required: False
        default: None
        description:
            - This is only used with VLAN - parent device this VLAN is on, can use ifname
    flags:
        required: False
        default: None
        description:
            - This is only used with VLAN - flags
    ingress:
        required: False
        default: None
        description:
            - This is only used with VLAN - VLAN ingress priority mapping
    egress:
        required: False
        default: None
        description:
            - This is only used with VLAN - VLAN egress priority mapping

'''

EXAMPLES='''
The following examples are working examples that I have run in the field. I followed follow the structure: