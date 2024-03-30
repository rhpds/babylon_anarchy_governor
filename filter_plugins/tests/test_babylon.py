#!/usr/bin/env python3

import pytest
from ansible.errors import AnsibleFilterError
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import babylon


def test_filter_main_sandbox():
    resources = [
        {'kind': 'AwsSandbox', 'name': 'sandbox1'},
        {'kind': 'AwsSandbox', 'annotations': {'var': 'sandbox2'}},
        {'kind': 'OcpSandbox'},
    ]
    assert babylon.filter_main_sandbox(resources, 'AwsSandbox') == {'kind': 'AwsSandbox', 'name': 'sandbox1'}
    assert babylon.filter_main_sandbox(resources, 'OcpSandbox') == {'kind': 'OcpSandbox'}

    resources = [
        {'kind': 'AwsSandbox', 'name': 'sandbox1'},
        {'kind': 'AwsSandbox', 'annotations': {'var': 'sandbox2'}},
        {'kind': 'OcpSandbox'},
    ]
    assert babylon.filter_main_sandbox(resources, 'AwsSandbox') == {'kind': 'AwsSandbox', 'name': 'sandbox1'}
    assert babylon.filter_main_sandbox(resources, 'OcpSandbox') == {'kind': 'OcpSandbox'}

    resources = [
        {'kind': 'AwsSandbox', 'name': 'sandbox1'},
        {'kind': 'OcpSandbox'},
        {'kind': 'AwsSandbox', 'name': 'sandbox2'}
    ]

    assert babylon.filter_main_sandbox(resources, 'AwsSandbox') == {'kind': 'AwsSandbox', 'name': 'sandbox1'}
    assert babylon.filter_main_sandbox(resources, 'NotFound') == None

    resources = [
        {'kind': 'OcpSandbox', 'name': 'sandbox3'},
        {'kind': 'AwsSandbox', 'name': 'sandbox2', 'annotations': {'var': 'sandbox2'}},
        {'kind': 'AwsSandbox', 'name': 'sandbox1'},
    ]

    assert babylon.filter_main_sandbox(resources, 'AwsSandbox') == {'kind': 'AwsSandbox', 'name': 'sandbox1'}
    assert babylon.filter_main_sandbox(resources, 'OcpSandbox') == {'kind': 'OcpSandbox', 'name': 'sandbox3'}


def test_inject_var_annotations():
    testcases = [
        {
            'resources': [
                {'kind': 'AwsSandbox', 'name':'sandbox2', 'var':'sandbox2'},
                {'kind': 'AwsSandbox', 'name': 'sandbox1'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': [
                {'kind': 'AwsSandbox', 'name':'sandbox2', 'var':'sandbox2','annotations':{'var':'sandbox2'}},
                {'kind': 'AwsSandbox', 'name': 'sandbox1'},
                {'kind': 'OcpSandbox'},
            ]
        },
        {
            'resources': [
                {'kind': 'AwsSandbox', 'name':'sandbox1'},
                {'kind': 'AwsSandbox', 'name':'sandbox2', 'var':'sandbox2'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': [
                {'kind': 'AwsSandbox', 'name':'sandbox1'},
                {'kind': 'AwsSandbox', 'name':'sandbox2', 'var': 'sandbox2', 'annotations': {'var': 'sandbox2'}},
                {'kind': 'OcpSandbox'},
            ]
        },
    ]

    for testcase in testcases:
        assert babylon.inject_var_annotations(testcase['resources']) == testcase['expected']


def test_validate_sandboxes_request():
    testcases = [
        {
            'request': [
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': "OK",
        },
        {
            'request': [
                {'kind': 'AwsSandbox', 'var': 'sandbox2'},
                {'kind': 'AwsSandbox'},
                {'kind': 'OcpSandbox'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': "ERROR: missing 'var' key for second sandbox of kind OcpSandbox",
        },
        {
            'request': [
                {'kind2': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': "ERROR: Sandbox kind is required in the sandboxes request",
        },
        {
            'request': [],
            'expected': "ERROR: At least one sandbox is required in the sandboxes request",
        },
        {
            'request': [
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox', 'var':'sandbox1'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': "ERROR: Main sandbox is missing for kind AwsSandbox",
        },
        {
            'request': [
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': "ERROR: Variable 'sandbox2' is duplicated",
        },
    ]

    for testcase in testcases:
        assert babylon.validate_sandboxes_request(testcase['request']) == testcase['expected']
