#!/usr/bin/env python

import pytest
import babylon
import datetime
import yaml

def test_ee_is_allowed():
    al = yaml.safe_load("""
    - image: ^quay.io/redhat-gpte/agnosticd-images:ee-.*?-v[0-9]+[.][0-9]+[.][0-9]+$
      pull: missing
    - image: ^quay.io/redhat-gpte/agnosticd-images:ee-.*?-(pr-[0-9]+|latest|dev|test)$
      pull: always
    - image: ^registry.redhat.io/ansible-automation-platform-21/ee-
    - image: ^quay.io/redhat-gpte/agnosticd-images:ee-ansible2.9-python3.6-2021-11-30$
    - image: ^quay.io/redhat-gpte/agnosticd-images:ee-equinix_metal-ansible2.9-python3.6-2021-07-02$
    - image: ^quay.io/redhat-gpte/agnosticd-images:ee-equinix_metal-ansible2.9-python3.6-2021-11-03$
    - image: ^quay.io/redhat-gpte/agnosticd-images:ee-azure_open_envs-ansible2.9-python3.6-2022-01-10$
    - image: ^quay.io/redhat-gpte/agnosticd-images:ee-ansible2.9-python3.6-2021-01-22$

    - name: ^Ansible Engine 2.9 execution environment$
    - name: ^Automation Hub Ansible Engine 2.9 execution environment$
    - name: ^Automation Hub Default execution environment$
    - name: ^Automation Hub Minimal execution environment$
    - name: ^Control Plane Execution Environment$
    - name: ^Default execution environment$
    - name: ^Minimal execution environment$
    """)
    testcases = [
        {
            "ee": {},
            "allow_list": {},
            "expected": 'error'
        },
        {
            "ee": {},
            "allow_list": [],
            "expected": True
        },
        {
            "ee": {"image": "aaafoobar"},
            "allow_list": [{"image":'^aaa'}],
            "expected": True
        },
        {
            "ee": {"image": "aafoobar"},
            "allow_list": [{"image":'^aaa'}],
            "expected": False
        },
        {
            "ee": {"image": "   quay.io/redhat-gpte/agnosticd-images:ee-someimage  "},
            "allow_list": [
                {
                    "image": "^quay.io/redhat-gpte/agnosticd-images:ee-",
                    "pull": "missing"
                }
            ],
            "expected": True,
        },
        {
            "ee": {"image": "quay.io/redhat-gpte/agnosticd-images:ee-someimage-latest   ",
                   "pull": "always"},
            "allow_list": [
                {
                    "image": "^quay.io/redhat-gpte/agnosticd-images:ee-.*latest$",
                    "pull": "always"
                }
            ],
            "expected": True,
        },
        {
            "ee": {"image": "aaafoobar"},
            "allow_list": [{"image":'^aa(a'}],
            "expected": 'error',
        },
        {
            "ee": {"image": "quay.io/redhat-gpte/agnosticd-images:ee-someimage-without-version"},
            "allow_list": al,
            "expected": False,
        },
        {
            "ee": {"image": "quay.io/redhat-gpte/agnosticd-images:ee-ansible2.9-python3.6-2021-11-30"},
            "allow_list": al,
            "expected": True,
        },
        {
            "ee": {"image": "quay.io/redhat-gpte/agnosticd-images:ee-someimage-v0.1.0"},
            "allow_list": al,
            "expected": True,
        },
        {
            "ee": {"image": "quay.io/redhat-gpte/agnosticd-images:ee-someimage-latest"},
            "allow_list": al,
            "expected": False,
        },
        {
            "ee": {"pull": "always", "image": "quay.io/redhat-gpte/agnosticd-images:ee-someimage-latest"},
            "allow_list": al,
            "expected": True,
        },
        {
            "ee": {"image": "registry.redhat.io/ansible-automation-platform-21/ee-29-rhel8:1.0.0-33"},
            "allow_list": al,
            "expected": True,
        },
    ]

    for idx, tc in enumerate(testcases):
        if tc['expected'] == 'error':
            with pytest.raises(Exception):
                babylon.ee_is_allowed(tc['ee'], tc['allow_list'])
        else:
            assert babylon.ee_is_allowed(tc['ee'], tc['allow_list']) == tc['expected'], "testcase #%d"%(idx+1)
