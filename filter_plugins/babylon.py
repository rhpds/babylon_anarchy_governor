# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleFilterError
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.utils import helpers

from copy import deepcopy
from datetime import datetime, timedelta

import re

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

def mark_ansible_vault_values(src):
    if isinstance(src, dict):
        return { k: mark_ansible_vault_values(v) for k, v in src.items() }
    elif isinstance(src, list):
        return [ mark_ansible_vault_values(v) for v in src ]
    elif isinstance(src, str):
        if src.startswith('$ANSIBLE_VAULT;'):
            return {"__ansible_vault": src}
        else:
            return src
    else:
        return src

def ee_is_allowed(ee, allow_list):
    """Filter to validate an Execution Environment against a list of regexes.
    If one regex matches, the EE is allowed.
    If no match found, the EE is refused.
    'name' and 'image' keys cannot be defined at the same time in agnosticV.
    This test returns False in that case.
    Return True (allowed) or False (not allowed)."""
    function_name = "ee_is_allowed"

    if not isinstance(ee, dict):
        raise AnsibleFilterError(
            '%s: dict expected for Execution Environment' %(function_name))

    if not isinstance(allow_list, list):
        raise AnsibleFilterError(
            '%s: list expected for Execution Environment Allow list' %(function_name))

    if len(allow_list) == 0:
        return True

    if 'name' in ee and 'image' in ee:
        return False

    # Set default values in ee
    ee = deepcopy(ee)
    if 'pull' not in ee:
        ee['pull'] = 'missing'

    for v in allow_list:
        for k in v:
            if k not in ee:
                break

            regex = v[k]
            try:
                p = re.compile(regex)
                if not p.match(ee[k].strip()):
                    break
            except Exception as err:
                raise AnsibleFilterError("%s: wrong regex '%s'" %(function_name, regex))

        else:
            return True

    return False

# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'filter_job_vars_to_dynamic_job_vars': filter_job_vars_to_dynamic_job_vars,
            'filter_job_vars_secrets_to_dynamic_job_vars': filter_job_vars_secrets_to_dynamic_job_vars,
            'mark_ansible_vault_values': mark_ansible_vault_values,
        }
