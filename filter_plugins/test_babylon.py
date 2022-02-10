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

def test_insert_unvault_string():
    startwithstring = '{{ lookup(\'unvault_string\', __vaulted_value_'
    test_vaulted={"foo":'''
        $ANSIBLE_VAULT;1.1;AES256
        62636665646636306161303836626134616161633236633065653737326538663931613462366666
        6634313965303664623034666461353933333564623737350a666536323264353031653765313232
        63633437346264616339623734353966393238346365323766333464623564646161386335356431
        6166306331306130350a386634356432653935313931303432623333386134336339633032613235
        6431'''}

    patched = babylon.insert_unvault_string(test_vaulted)

    assert(patched['foo'].startswith(startwithstring))
    assert(len(patched) == 2)

    test_vaulted={
        "foo": {
            "subdict1" : {
                "subdict2" : {
                        "foo": '''
                        $ANSIBLE_VAULT;1.2;AES256;pfe_vault_0
                        62636665646636306161303836626134616161633236633065653737326538663931613462366666
                        6634313965303664623034666461353933333564623737350a666536323264353031653765313232
                        63633437346264616339623734353966393238346365323766333464623564646161386335356431
                        6166306331306130350a386634356432653935313931303432623333386134336339633032613235
                        6431'''
                }
            }
        }
    }

    patched = babylon.insert_unvault_string(test_vaulted)

    assert(patched['foo']['subdict1']['subdict2']['foo'].startswith(startwithstring))
    assert(len(patched) == 2)

    test_vaulted={
        "foo": {
            "subdict1" : {
                "foo": '''
                $ANSIBLE_VAULT;1.2;AES256;pfe_vault_0
                62636665646636306161303836626134616161633236633065653737326538663931613462366666
                6634313965303664623034666461353933333564623737350a666536323264353031653765313232
                63633437346264616339623734353966393238346365323766333464623564646161386335356431
                6166306331306130350a386634356432653935313931303432623333386134336339633032613235
                6431''',
                "subdict2" : {
                        "foo": '''
                        $ANSIBLE_VAULT;1.2;AES256;pfe_vault_0
                        62636665646636306161303836626134616161633236633065653737326538663931613462366666
                        6634313965303664623034666461353933333564623737350a666536323264353031653765313232
                        63633437346264616339623734353966393238346365323766333464623564646161386335356431
                        6166306331306130350a386634356432653935313931303432623333386134336339633032613235
                        6431'''
                }
            }
        }
    }

    patched = babylon.insert_unvault_string(test_vaulted)

    assert(patched['foo']['subdict1']['subdict2']['foo'].startswith(startwithstring))
    assert(patched['foo']['subdict1']['foo'].startswith(startwithstring))
    assert(len(patched) == 3)

    test_vaulted={}
    for i in range(1,10001):
        test_vaulted[str(i)] = '''
                        $ANSIBLE_VAULT;1.2;AES256;pfe_vault_0
                        62636665646636306161303836626134616161633236633065653737326538663931613462366666
                        6634313965303664623034666461353933333564623737350a666536323264353031653765313232
                        63633437346264616339623734353966393238346365323766333464623564646161386335356431
                        6166306331306130350a386634356432653935313931303432623333386134336339633032613235
                        6431'''

    patched = babylon.insert_unvault_string(test_vaulted)
    assert(patched['1'].startswith(startwithstring))
    assert(patched['10000'].startswith(startwithstring))
    assert(len(patched) == 20000)
