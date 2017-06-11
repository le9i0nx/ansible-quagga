#!/usr/bin/env python
# -*- coding: utf-8 -*-

# {c} 2017, Aleksey Gavrilov <le9i0nx+ansible@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = """
---
module: quagga
version_added: 2.2
short_description: Provides configuring quaggas router ospf
description:
     - The M(quagga) module takes the command name followed by a list of space-delimited arguments.
     - The given command will be executed on all selected nodes.
options:
    router_id:
        description:
            - Set the OSPFv2 router id
    router:
        description:
            - router type, currently implemented only ospf
    interfaces:
        description:
            - define the name the interface to apply OSPFv2 services.

 
author: Ilya Barsukov
"""

EXAMPLES = """
# Example for Ansible Playbooks.
- name: "add interface to ospf"
  quagga:
    interfaces:
      - name: "{{ item }}"
        raw:
          - "ip ospf authentication message-digest"
          - "ip ospf message-digest-key 1 md5 xxxx"
          - "ip ospf hello-interval 10"
          - "ip ospf dead-interval 40"
          - "ip ospf priority 99"
          - "ip ospf cost 40"
          - "ip ospf network broadcast"
  with_items:
    - "{{ ansible_interfaces }}"
  when: "'wg_' in item"

- name: "add router to ospf"
  quagga:
    router:
      ospf:
        - "log-adjacency-changes"
        - "network 10.1.16.0/24 area 0"
        - "network 10.254.222.0/24 area 0"
        - "area 0 authentication message-digest"
    router_id: "10.10.10.1"

"""

def run_cmd(module, cmd, check_rc=True, split_lines=True):
    try:
        (rc, out, err) = module.run_command(cmd, check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg=e.strerror)
    return out

def set_router_id(module):
    command = ["vtysh", "'configure terminal'", "'end'", "'write memory'"]
    command.insert(-2, "'router-id {}'".format(module.params['router_id']))
    run_cmd(module, ' -c '.join(command))

def set_interfaces(module):
    command = ["vtysh", "'configure terminal'", "'end'", "'write memory'"]
    for interface in module.params['interfaces']:
        if not interface['name']:
            module.fail_json(msg='interfaces nead name')
        command.insert(-2, "'interface {}'".format(interface['name']))
        for raw in interface['raw']:
            command.insert(-2, "'{}'".format(raw))
    run_cmd(module, ' -c '.join(command))

def set_router(module):
    router = module.params['router']
    if router['ospf']:
        command = ["vtysh", "'configure terminal'", "'end'", "'write memory'"]
        command.insert(-2, "'router ospf'")
        for raw in router['ospf']:
            command.insert(-2, "'{}'".format(raw))
        run_cmd(module, ' -c '.join(command))

def main():

    module = AnsibleModule(
        argument_spec = dict(
            interfaces = dict(type='list'),
            router = dict(type='dict'),
            router_id = dict(type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
    )

    before_status = run_cmd(module, "vtysh -c 'show run' -c 'end'")

    if module.params['router_id']:  set_router_id(module)
    if module.params['interfaces']: set_interfaces(module)
    if module.params['router']:     set_router(module)

    after_status = run_cmd(module, "vtysh -c 'show run' -c 'end'")
    module.exit_json(changed=before_status!=after_status)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
