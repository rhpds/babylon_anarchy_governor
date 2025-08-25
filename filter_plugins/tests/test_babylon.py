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
            'expected': "OK",
        },
        {
            'request': [
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'OcpSandbox'},
            ],
            'expected': "ERROR: Variable 'sandbox2' is duplicated",
        },
        {
            'request': [
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox'},
                {
                    'kind': 'OcpSandbox',
                    'annotations': {
                        'purpose': 'ocp'
                    },
                    'cloud_selector': {
                        'virt': 'enable',
                    },
                },
            ],
            'expected': "OK",
        },
        {
            'request': [
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox'},
                {
                    'kind': 'OcpSandbox',
                    'annotations': {
                        'purpose': 'ocp'
                    },
                    'cloud_selector': {
                        'virt': {
                            'will': 'fail',
                        }
                    },
                },
            ],
            'expected': "ERROR: cloud_selector values should be strings for sandbox of kind OcpSandbox",
        },
        {
            'request': [
                {'kind': 'AwsSandbox', 'var':'sandbox2'},
                {'kind': 'AwsSandbox'},
                {
                    'kind': 'OcpSandbox',
                    'annotations': {
                        'purpose': {
                            'will': 'fail'
                        }
                    },
                },
            ],
            'expected': "ERROR: Annotations values should be strings for sandbox of kind OcpSandbox",
        },
    ]

    for testcase in testcases:
        assert babylon.validate_sandboxes_request(testcase['request']) == testcase['expected']



def test_extract_sandboxes_vars():
    testcases = [
        {
            'creds': True,
            'input': {
                'id': 3,
                "created_at": "2024-04-02T10:44:18.241437+02:00",
                "updated_at": "2024-04-02T10:44:18.241437+02:00",
                "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "resources": [
                    {
                        "created_at": "0001-01-01T00:00:00Z",
                        "updated_at": "1970-01-01T01:00:00+01:00",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "available": False,
                        "to_cleanup": False,
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "aws"
                        },
                        "kind": "AwsSandbox",
                        "name": "sandbox3153",
                        "account_id": "accountNumber",
                        "zone": "sandbox3153.domain.com",
                        "hosted_zone_id": "foobar",
                        "conan_timestamp": "0001-01-01T00:00:00Z",
                        "credentials": [
                            {
                                "kind": "aws_iam_key",
                                "name": "admin-key",
                                "aws_access_key_id": "foobarKey",
                                "aws_secret_access_key": "foobarSecret"
                            }
                        ]
                    },
                    {
                        "id": 7,
                        "created_at": "2024-04-02T10:44:10.597366+02:00",
                        "updated_at": "2024-04-02T10:44:18.251974+02:00",
                        "available": False,
                        "to_cleanup": False,
                        "name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "kind": "OcpSandbox",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "ocp_cluster": "cluster",
                        "api_url": "https://cluster.domain.io:6443",
                        "console_url": "https://console.cluster.domain.io",
                        "ingress_domain": "apps.cluster.domain.io",
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "ocp"
                        },
                        "status": "success",
                        "cleanup_count": 0,
                        "namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "credentials": [
                            {
                                "kind": "ServiceAccount",
                                "name": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                                "token": "foobarToken"
                            }
                        ]
                    }
                ],
                "annotations": {
                    "env_type": "ocp4-cluster-blablablabla",
                    "guid": "testg-1"
                },
                "request": {
                    "annotations": {
                        "env_type": "ocp4-cluster-blablablabla",
                        "guid": "testg-1"
                    },
                    "resources": [
                        {
                            "annotations": {
                                "purpose": "ocp"
                            },
                            "count": 1,
                            "kind": "OcpSandbox"
                        },
                        {
                            "annotations": {
                                "purpose": "aws"
                            },
                            "count": 1,
                            "kind": "AwsSandbox"
                        }
                    ],
                    "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf"
                }
            },
            "expected": {
                # OCP
                "sandbox_openshift_name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "sandbox_openshift_apps_domain": "apps.cluster.domain.io",
                "sandbox_openshift_api_url": "https://cluster.domain.io:6443",
                "sandbox_openshift_api_key": "foobarToken",
                "sandbox_openshift_api_token": "foobarToken",
                "sandbox_openshift_cluster": "cluster",
                "sandbox_openshift_console_url": "https://console.cluster.domain.io",
                "sandbox_openshift_namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "sandbox_openshift_credentials": [
                    {
                        "kind": "ServiceAccount",
                        "name": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "token": "foobarToken"
                    }
                ],
                # AWS
                "sandbox_name": "sandbox3153",
                "sandbox_hosted_zone_id": "foobar",
                "HostedZoneId": "foobar",
                "sandbox_account": "accountNumber",
                "sandbox_account_id": "accountNumber",
                "sandbox_zone": "sandbox3153.domain.com",
                "sandbox_credentials": [
                    {
                        "kind": "aws_iam_key",
                        "name": "admin-key",
                        "aws_access_key_id": "foobarKey",
                        "aws_secret_access_key": "foobarSecret"
                    }
                ],
                "subdomain_base_suffix": ".sandbox3153.domain.com",
                "sandbox_aws_access_key_id": "foobarKey",
                "sandbox_aws_secret_access_key": "foobarSecret",
                "aws_access_key_id": "foobarKey",
                "aws_secret_access_key": "foobarSecret"
            }
        },
        {
            'creds': True,
            'input': {
                'id': 3,
                "created_at": "2024-04-02T10:44:18.241437+02:00",
                "updated_at": "2024-04-02T10:44:18.241437+02:00",
                "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "resources": [
                    {
                        "created_at": "0001-01-01T00:00:00Z",
                        "updated_at": "1970-01-01T01:00:00+01:00",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "available": False,
                        "to_cleanup": False,
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "aws",
                            "var": "sandbox1"
                        },
                        "kind": "AwsSandbox",
                        "name": "sandbox3153",
                        "account_id": "accountNumber",
                        "zone": "sandbox3153.domain.com",
                        "hosted_zone_id": "foobar",
                        "conan_timestamp": "0001-01-01T00:00:00Z",
                        "credentials": [
                            {
                                "kind": "aws_iam_key",
                                "name": "admin-key",
                                "aws_access_key_id": "foobarKey",
                                "aws_secret_access_key": "foobarSecret"
                            }
                        ]
                    },
                    {
                        "id": 7,
                        "created_at": "2024-04-02T10:44:10.597366+02:00",
                        "updated_at": "2024-04-02T10:44:18.251974+02:00",
                        "available": False,
                        "to_cleanup": False,
                        "name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "kind": "OcpSandbox",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "ocp_cluster": "cluster",
                        "api_url": "https://cluster.domain.io:6443",
                        "ingress_domain": "apps.cluster.domain.io",
                        "console_url": "https://console.cluster.domain.io",
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "ocp",
                            "var": "sandbox2",
                        },
                        "status": "success",
                        "cleanup_count": 0,
                        "namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "credentials": [
                            {
                                "kind": "ServiceAccount",
                                "name": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                                "token": "foobarToken"
                            }
                        ]
                    }
                ],
                "annotations": {
                    "env_type": "ocp4-cluster-blablablabla",
                    "guid": "testg-1"
                },
                "request": {
                    "annotations": {
                        "env_type": "ocp4-cluster-blablablabla",
                        "guid": "testg-1"
                    },
                    "resources": [
                        {
                            "annotations": {
                                "purpose": "ocp"
                            },
                            "count": 1,
                            "kind": "OcpSandbox"
                        },
                        {
                            "annotations": {
                                "purpose": "aws"
                            },
                            "count": 1,
                            "kind": "AwsSandbox"
                        }
                    ],
                    "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf"
                }
            },
            "expected": {
                # OCP
                "sandbox2": {
                    "sandbox_openshift_name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                    "sandbox_openshift_apps_domain": "apps.cluster.domain.io",
                    "sandbox_openshift_api_url": "https://cluster.domain.io:6443",
                    "sandbox_openshift_api_key": "foobarToken",
                    "sandbox_openshift_api_token": "foobarToken",
                    "sandbox_openshift_namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                    "sandbox_openshift_console_url": "https://console.cluster.domain.io",
                    "sandbox_openshift_cluster": "cluster",
                    "sandbox_openshift_credentials": [
                        {
                            "kind": "ServiceAccount",
                            "name": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                            "token": "foobarToken"
                        }
                    ],
                },
                # AWS
                "sandbox1": {
                    "sandbox_name": "sandbox3153",
                    "sandbox_hosted_zone_id": "foobar",
                    "HostedZoneId": "foobar",
                    "sandbox_account": "accountNumber",
                    "sandbox_account_id": "accountNumber",
                    "sandbox_zone": "sandbox3153.domain.com",
                    "sandbox_credentials": [
                        {
                            "kind": "aws_iam_key",
                            "name": "admin-key",
                            "aws_access_key_id": "foobarKey",
                            "aws_secret_access_key": "foobarSecret"
                        }
                    ],
                    "subdomain_base_suffix": ".sandbox3153.domain.com",
                    "sandbox_aws_access_key_id": "foobarKey",
                    "sandbox_aws_secret_access_key": "foobarSecret",
                    "aws_access_key_id": "foobarKey",
                    "aws_secret_access_key": "foobarSecret"
                }
            }
        },
        {
            'creds': False,
            'input': {
                'id': 3,
                "created_at": "2024-04-02T10:44:18.241437+02:00",
                "updated_at": "2024-04-02T10:44:18.241437+02:00",
                "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "resources": [
                    {
                        "created_at": "0001-01-01T00:00:00Z",
                        "updated_at": "1970-01-01T01:00:00+01:00",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "available": False,
                        "to_cleanup": False,
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "aws"
                        },
                        "kind": "AwsSandbox",
                        "name": "sandbox3153",
                        "account_id": "accountNumber",
                        "zone": "sandbox3153.domain.com",
                        "hosted_zone_id": "foobar",
                        "conan_timestamp": "0001-01-01T00:00:00Z",
                        "credentials": [
                            {
                                "kind": "aws_iam_key",
                                "name": "admin-key",
                                "aws_access_key_id": "foobarKey",
                                "aws_secret_access_key": "foobarSecret"
                            }
                        ]
                    },
                    {
                        "id": 7,
                        "created_at": "2024-04-02T10:44:10.597366+02:00",
                        "updated_at": "2024-04-02T10:44:18.251974+02:00",
                        "available": False,
                        "to_cleanup": False,
                        "name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "kind": "OcpSandbox",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "ocp_cluster": "cluster",
                        "api_url": "https://cluster.domain.io:6443",
                        "ingress_domain": "apps.cluster.domain.io",
                        "console_url": "https://console.cluster.domain.io",
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "ocp"
                        },
                        "status": "success",
                        "cleanup_count": 0,
                        "namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "credentials": [
                            {
                                "kind": "ServiceAccount",
                                "name": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                                "token": "foobarToken"
                            }
                        ]
                    }
                ],
                "annotations": {
                    "env_type": "ocp4-cluster-blablablabla",
                    "guid": "testg-1"
                },
                "request": {
                    "annotations": {
                        "env_type": "ocp4-cluster-blablablabla",
                        "guid": "testg-1"
                    },
                    "resources": [
                        {
                            "annotations": {
                                "purpose": "ocp"
                            },
                            "count": 1,
                            "kind": "OcpSandbox"
                        },
                        {
                            "annotations": {
                                "purpose": "aws"
                            },
                            "count": 1,
                            "kind": "AwsSandbox"
                        }
                    ],
                    "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf"
                }
            },
            "expected": {
                # OCP
                "sandbox_openshift_name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "sandbox_openshift_apps_domain": "apps.cluster.domain.io",
                "sandbox_openshift_api_url": "https://cluster.domain.io:6443",
                "sandbox_openshift_cluster": "cluster",
                "sandbox_openshift_console_url": "https://console.cluster.domain.io",
                "sandbox_openshift_namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                # AWS
                "sandbox_name": "sandbox3153",
                "sandbox_hosted_zone_id": "foobar",
                "HostedZoneId": "foobar",
                "sandbox_account": "accountNumber",
                "sandbox_account_id": "accountNumber",
                "sandbox_zone": "sandbox3153.domain.com",
                "subdomain_base_suffix": ".sandbox3153.domain.com",
            }
        },
    ]

    for tc in testcases:
        assert babylon.extract_sandboxes_vars(tc['input'], tc['creds']) == tc['expected']

def test_extract_sandboxes_labels():
    testcases = [
        {
            'input': {
                'id': 3,
                "created_at": "2024-04-02T10:44:18.241437+02:00",
                "updated_at": "2024-04-02T10:44:18.241437+02:00",
                "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "resources": [
                    {
                        "created_at": "0001-01-01T00:00:00Z",
                        "updated_at": "1970-01-01T01:00:00+01:00",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "available": False,
                        "to_cleanup": False,
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "aws"
                        },
                        "kind": "AwsSandbox",
                        "name": "sandbox3153",
                        "account_id": "accountNumber",
                        "zone": "sandbox3153.domain.com",
                        "hosted_zone_id": "foobar",
                        "conan_timestamp": "0001-01-01T00:00:00Z",
                        "credentials": [
                            {
                                "kind": "aws_iam_key",
                                "name": "admin-key",
                                "aws_access_key_id": "foobarKey",
                                "aws_secret_access_key": "foobarSecret"
                            }
                        ]
                    },
                    {
                        "id": 7,
                        "created_at": "2024-04-02T10:44:10.597366+02:00",
                        "updated_at": "2024-04-02T10:44:18.251974+02:00",
                        "available": False,
                        "to_cleanup": False,
                        "name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "kind": "OcpSandbox",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "ocp_cluster": "cluster",
                        "api_url": "https://cluster.domain.io:6443",
                        "ingress_domain": "apps.cluster.domain.io",
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "ocp"
                        },
                        "status": "success",
                        "cleanup_count": 0,
                        "namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "credentials": [
                            {
                                "kind": "ServiceAccount",
                                "name": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                                "token": "foobarToken"
                            }
                        ]
                    },
                ],
                "annotations": {
                    "env_type": "ocp4-cluster-blablablabla",
                    "guid": "testg-1"
                },
                "request": {
                    "annotations": {
                        "env_type": "ocp4-cluster-blablablabla",
                        "guid": "testg-1"
                    },
                    "resources": [
                        {
                            "annotations": {
                                "purpose": "ocp"
                            },
                            "count": 1,
                            "kind": "OcpSandbox"
                        },
                        {
                            "annotations": {
                                "purpose": "aws"
                            },
                            "count": 1,
                            "kind": "AwsSandbox"
                        }
                    ],
                    "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf"
                }
            },
            "expected": {
                "sandbox": "sandbox3153",
                "AwsSandbox": "sandbox3153",
                "OcpSandbox": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
            }
        },
        {
            'input': {
                'id': 3,
                "created_at": "2024-04-02T10:44:18.241437+02:00",
                "updated_at": "2024-04-02T10:44:18.241437+02:00",
                "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "resources": [
                    {
                        "id": 7,
                        "created_at": "2024-04-02T10:44:10.597366+02:00",
                        "updated_at": "2024-04-02T10:44:18.251974+02:00",
                        "available": False,
                        "to_cleanup": False,
                        "name": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "kind": "OcpSandbox",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "ocp_cluster": "cluster",
                        "api_url": "https://cluster.domain.io:6443",
                        "ingress_domain": "apps.cluster.domain.io",
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "ocp"
                        },
                        "status": "success",
                        "cleanup_count": 0,
                        "namespace": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "credentials": [
                            {
                                "kind": "ServiceAccount",
                                "name": "sandbox-testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                                "token": "foobarToken"
                            }
                        ]
                    },
                    {
                        "id": 8,
                        "created_at": "2024-04-02T10:44:10.597366+02:00",
                        "updated_at": "2024-04-02T10:44:18.251974+02:00",
                        "available": False,
                        "to_cleanup": False,
                        "name": "testg-2-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "kind": "OcpSandbox",
                        "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "ocp_cluster": "cluster",
                        "api_url": "https://cluster.domain.io:6443",
                        "ingress_domain": "apps.cluster.domain.io",
                        "annotations": {
                            "env_type": "ocp4-cluster-blablablabla",
                            "guid": "testg-1",
                            "purpose": "ocp"
                        },
                        "status": "success",
                        "cleanup_count": 0,
                        "namespace": "sandbox-testg-2-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                        "credentials": [
                            {
                                "kind": "ServiceAccount",
                                "name": "sandbox-testg-2-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                                "token": "foobarToken"
                            }
                        ]
                    },
                ],
                "annotations": {
                    "env_type": "ocp4-cluster-blablablabla",
                    "guid": "testg-1"
                },
                "request": {
                    "annotations": {
                        "env_type": "ocp4-cluster-blablablabla",
                        "guid": "testg-1"
                    },
                    "resources": [
                        {
                            "annotations": {
                                "purpose": "ocp"
                            },
                            "count": 1,
                            "kind": "OcpSandbox"
                        },
                        {
                            "annotations": {
                                "purpose": "aws"
                            },
                            "count": 1,
                            "kind": "AwsSandbox"
                        }
                    ],
                    "service_uuid": "d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf"
                }
            },
            "expected": {
                "sandbox": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "OcpSandbox": "testg-1-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
                "OcpSandbox2": "testg-2-d9c3a0bb-d3c3-4c05-822c-13eac4b17bcf",
            }
        },
        {
            "input": {
                "resources": [],
            },
            "expected": {},
        },
    ]

    for tc in testcases:
        assert babylon.extract_sandboxes_labels(tc['input']) == tc['expected']
