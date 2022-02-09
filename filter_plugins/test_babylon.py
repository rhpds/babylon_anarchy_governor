#!/usr/bin/env python

import pytest
from ansible.errors import AnsibleFilterError
import sys
import os
import babylon

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
