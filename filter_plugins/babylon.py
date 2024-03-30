# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleFilterError
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.utils import helpers
from ansible.utils.display import Display

from copy import deepcopy
from datetime import datetime, timedelta

import random
import re
import string

variable_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits

display = Display()

def filter_job_vars_to_dynamic_job_vars(anarchy_governor, preserve_job_vars):
    return {
        k: v for (k, v) in anarchy_governor['spec']['vars'].get('job_vars', {}).items() if k in preserve_job_vars
    }

def filter_job_vars_secrets_to_dynamic_job_vars(anarchy_governor):
    dynamic_job_var_secrets = []
    for var_secret in anarchy_governor['spec'].get('varSecrets', []):
        if var_secret.get('var', '') == 'job_vars':
            dynamic_job_var_secret = deepcopy(var_secret)
            dynamic_job_var_secret['var'] = 'dynamic_job_vars'
            dynamic_job_var_secrets.append(dynamic_job_var_secret)
    return dynamic_job_var_secrets

def __insert_unvault_string(value, vaulted_values):
    if isinstance(value, dict):
        return { k: __insert_unvault_string(v, vaulted_values) for k, v in value.items() }
    elif isinstance(value, list):
        return [ __insert_unvault_string(v, vaulted_values) for v in value ]
    if isinstance(value, str) and value.strip().startswith('$ANSIBLE_VAULT;'):
        vaulted_value_var = None
        while True:
            vaulted_value_var = '__vaulted_value_' + ''.join(random.choice(variable_chars) for i in range(12))
            if vaulted_value_var not in vaulted_values:
                break
        vaulted_values[vaulted_value_var] = value
        return "{{ lookup('unvault_string', " + vaulted_value_var +") }}"
    else:
        return value

def insert_unvault_string(vars_dict):
    vaulted_values = {}
    ret_vars_dict = __insert_unvault_string(vars_dict, vaulted_values)
    ret_vars_dict.update(vaulted_values)
    return ret_vars_dict

def mark_ansible_vault_values(src):
    if isinstance(src, dict):
        return { k: mark_ansible_vault_values(v) for k, v in src.items() }
    elif isinstance(src, list):
        return [ mark_ansible_vault_values(v) for v in src ]
    elif isinstance(src, str):
        if src.strip().startswith('$ANSIBLE_VAULT;'):
            return {"__ansible_vault": src}
        else:
            return src
    else:
        return src

def filter_main_sandbox(resources, kind='AwsSandbox'):
    """Get the main sandbox from the resources list returned by the sandbox API

    Args:
        resources (list): List of resources returned by the sandbox API
        kind (str): Kind of sandbox to filter

    Returns:
        dict: The main sandbox
        the main sandbox is the only sandbox without a 'var' key in the annotations
        or with annotations['var'] == 'main'
        for example in:

        returns None if the main sandbox is not found

        [{
                'kind': 'AwsSandbox',
            },
            {
                'kind': 'AwsSandbox',
                'annotations': {
                    'var': 'sandbox2'
                }
            },
            {
            {
                'kind': 'OcpSandbox',
            },
        ]
        the main sandbox is the first one without a 'var' defined

    """
    main_sandbox = None
    for resource in resources:
        if resource.get('kind', 'none') == kind:
            var = resource.get('annotations', {}).get('var', 'main')
            if var == 'main':
                return resource


    return main_sandbox


def inject_var_annotations(sandboxes_request):
    """
    Inject the var key in the annotations of the sandboxes to be able to reference them in the sandboxes_request
    It's used to build the request to the sandbox API
    """

    done = {}

    for req in sandboxes_request:
        if req.get('var', False):
            req['annotations'] = req.get('annotations', {})
            req['annotations']['var'] = req['var']

    return sandboxes_request

def validate_sandboxes_request(sandboxes_request):
    """
    Validate the sandboxes request __meta__.sandboxes

    This function should be also used in agnosticV validation tests

    returns: String
        'OK' if the request is valid
        The error message if the request is invalid
    """

    mainFound = {}
    vars = {}

    if len(sandboxes_request) == 0:
        return "ERROR: At least one sandbox is required in the sandboxes request"

    for req in sandboxes_request:
        if 'kind' not in req:
            return "ERROR: Sandbox kind is required in the sandboxes request"

        kind = req['kind']

        if kind not in mainFound:
            mainFound[kind] = False

        var = req.get('var', False)
        if var:
            if var in vars:
                return "ERROR: Variable '" + var + "' is duplicated"
            vars[var] = True
        else:
            if mainFound.get(kind, False):
                return "ERROR: missing 'var' key for second sandbox of kind " + kind

            mainFound[kind] = True

    if len(mainFound) == 0:
        return "ERROR: At least one main sandbox is required in the sandboxes request"

    for kind in mainFound:
        if not mainFound[kind]:
            return "ERROR: Main sandbox is missing for kind " + kind

    return "OK"

# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'filter_job_vars_to_dynamic_job_vars': filter_job_vars_to_dynamic_job_vars,
            'filter_job_vars_secrets_to_dynamic_job_vars': filter_job_vars_secrets_to_dynamic_job_vars,
            'insert_unvault_string': insert_unvault_string,
            'mark_ansible_vault_values': mark_ansible_vault_values,
            'filter_main_sandbox': filter_main_sandbox,
            'inject_var_annotations': inject_var_annotations,
            'validate_sandboxes_request': validate_sandboxes_request,
        }
