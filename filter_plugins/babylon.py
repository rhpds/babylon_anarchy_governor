# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import random
import string
import re
from copy import deepcopy
from ansible.utils.display import Display

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

    for req in sandboxes_request:
        if req.get('var', False):
            req['annotations'] = req.get('annotations', {})
            req['annotations']['var'] = req['var']
        if req.get('namespace_suffix', False):
            req['annotations'] = req.get('annotations', {})
            req['annotations']['namespace_suffix'] = req['namespace_suffix']

    return sandboxes_request

def validate_sandboxes_request(sandboxes_request):
    """
    Validate the sandboxes request __meta__.sandboxes

    This function should be also used in agnosticV validation tests

    returns: String
        'OK' if the request is valid
        The error message if the request is invalid
    """

    main_found = {}
    target_vars = {}

    if len(sandboxes_request) == 0:
        return "ERROR: At least one sandbox is required in the sandboxes request"

    for req in sandboxes_request:
        if 'kind' not in req:
            return "ERROR: Sandbox kind is required in the sandboxes request"

        kind = req['kind']

        if kind not in main_found:
            main_found[kind] = False

        var = req.get('var', False)
        if var:
            if var in target_vars:
                return "ERROR: Variable '" + var + "' is duplicated"
            target_vars[var] = True
        else:
            if main_found.get(kind, False):
                return "ERROR: missing 'var' key for second sandbox of kind " + kind

            main_found[kind] = True

        # Ensure annotations is a dict of string
        if 'annotations' in req:
            if not isinstance(req['annotations'], dict):
                return "ERROR: Annotations should be a dict for sandbox of kind " + kind

            for key in req['annotations']:
                if not isinstance(req['annotations'][key], str):
                    return "ERROR: Annotations values should be strings for sandbox of kind " + kind

        # Ensure cloud_selector is a dict of string
        if 'cloud_selector' in req:
            if not isinstance(req['cloud_selector'], dict):
                return "ERROR: cloud_selector should be a dict for sandbox of kind " + kind

            for key in req['cloud_selector']:
                if not isinstance(req['cloud_selector'][key], str):
                    return "ERROR: cloud_selector values should be strings for sandbox of kind " + kind

    if len(main_found) == 0:
        return "ERROR: At least one main sandbox is required in the sandboxes request"

    for kind in main_found:
        if not main_found[kind]:
            return "ERROR: Main sandbox is missing for kind " + kind

    return "OK"

def extract_sandboxes_vars(response, creds=True):
    """Extract the sandbox vars and credentials from the Sandbox API placement response

    Returns: dict to be merged with job vars
    """

    sandboxes_vars = {}


    for sandbox in response.get('resources', []):
        kind = sandbox.get('kind', 'none')

        if kind == 'AwsSandbox':
            sandbox_name = sandbox.get('name', 'unknown')
            sandbox_hosted_zone_id = sandbox.get('hosted_zone_id', 'unknown')
            sandbox_account_id = sandbox.get('account_id', 'unknown')
            sandbox_zone = sandbox.get('zone', 'unknown')

            to_merge = {
                'sandbox_name': sandbox_name,
                'sandbox_hosted_zone_id': sandbox_hosted_zone_id,
                'HostedZoneId': sandbox_hosted_zone_id,
                'sandbox_account': sandbox_account_id,
                'sandbox_account_id': sandbox_account_id,
                'sandbox_zone': sandbox_zone,
                'subdomain_base_suffix': '.' + sandbox_zone,
                'base_domain': sandbox_zone
            }
            if creds:
                for cred in sandbox.get('credentials', []):
                    # Get the first AWS IAM key found
                    if cred.get('kind', 'none') == 'aws_iam_key':
                        to_merge['sandbox_aws_access_key_id'] = cred.get('aws_access_key_id', 'unknown')
                        to_merge['aws_access_key_id'] = cred.get('aws_access_key_id', 'unknown')
                        to_merge['sandbox_aws_secret_access_key'] = cred.get('aws_secret_access_key', 'unknown')
                        to_merge['aws_secret_access_key'] = cred.get('aws_secret_access_key', 'unknown')
                        to_merge['sandbox_credentials'] = sandbox.get('credentials', [])
                        break

            var = sandbox.get('annotations', {}).get('var', 'main')
            if var == 'main':
                sandboxes_vars.update(to_merge)
            else:
                sandboxes_vars[var] = to_merge

        elif kind == 'OcpSandbox':
            sandbox_openshift_cluster = sandbox.get('ocp_cluster', 'unknown')
            sandbox_openshift_api_url = sandbox.get('api_url', 'unknown')
            sandbox_openshift_apps_domain = sandbox.get('ingress_domain', 'unknown')
            sandbox_openshift_name = sandbox.get('name', 'unknown')
            sandbox_openshift_namespace = sandbox.get('namespace', 'unknown')

            to_merge = {
                'sandbox_openshift_name': sandbox_openshift_name,
                'sandbox_openshift_namespace': sandbox_openshift_namespace,
                'sandbox_openshift_cluster': sandbox_openshift_cluster,
                'sandbox_openshift_api_url': sandbox_openshift_api_url,
                'sandbox_openshift_apps_domain': sandbox_openshift_apps_domain,
            }

            if creds:
                for creds in sandbox.get('credentials', []):
                    if creds.get('kind', 'none') == 'ServiceAccount':
                        to_merge['sandbox_openshift_api_key'] = creds.get('token', 'unknown')
                        to_merge['sandbox_openshift_credentials'] = sandbox.get('credentials', [])
                        break

            sandbox_additional_vars = sandbox.get('cluster_additional_vars', {}).get('deployer', {})

            # Additional vars set in the OcpSharedClusterConfiguration
            # are merged with the sandbox vars
            for key, value in sandbox_additional_vars.items():
                to_merge[key] = value

            var = sandbox.get('annotations', {}).get('var', 'main')
            if var == 'main':
                sandboxes_vars.update(to_merge)
            else:
                sandboxes_vars[var] = to_merge
        elif kind == 'IBMResourceGroupSandbox':
            to_merge = {}
            if creds:
                for creds in sandbox.get('credentials', []):
                    if creds.get('apikey', '') != '':
                        sandbox_ibm_resource_group_apikey = sandbox.get('credentials', [{}])[0].get('apikey', 'unknown')
                        sandbox_ibm_resource_group_name = sandbox.get('credentials', [{}])[0].get('name', 'unknown')
                        break

                to_merge = {
                    'ibmcloud_api_key': sandbox_ibm_resource_group_apikey,
                    'ibmcloud_resource_group_name': sandbox_ibm_resource_group_name,
                }

            additional_vars = sandbox.get('additional_vars', {}).get('deployer', {})

            # Additional vars set in the IBMResourceGroupSandbox
            # are merged with the sandbox vars
            for key, value in additional_vars.items():
                to_merge[key] = value

            var = sandbox.get('annotations', {}).get('var', 'main')
            if var == 'main':
                sandboxes_vars.update(to_merge)
            else:
                sandboxes_vars[var] = to_merge

        elif kind == 'DNSSandbox':
            to_merge = {}
            if creds:
                for creds in sandbox.get('credentials', []):
                    if creds.get('aws_access_key_id', '') != '':
                        aws_access_key_id = sandbox.get('credentials', [{}])[0].get('aws_access_key_id', 'unknown')
                        aws_secret_access_key = sandbox.get('credentials', [{}])[0].get('aws_secret_access_key', 'unknown')
                        hosted_zone_id = sandbox.get('credentials', [{}])[0].get('hosted_zone_id', 'unknown')
                        zone = sandbox.get('credentials', [{}])[0].get('zone', 'unknown')
                        break

                to_merge = {
                    'base_domain': zone,
                    'route53_aws_zone_id': hosted_zone_id,
                    'route53_aws_access_key_id': aws_access_key_id,
                    'route53_aws_secret_access_key': aws_secret_access_key
                }

            additional_vars = sandbox.get('additional_vars', {}).get('deployer', {})

            # Additional vars set in the DNSSandbox
            # are merged with the sandbox vars
            for key, value in additional_vars.items():
                to_merge[key] = value

            var = sandbox.get('annotations', {}).get('var', 'main')
            if var == 'main':
                sandboxes_vars.update(to_merge)
            else:
                sandboxes_vars[var] = to_merge

    return sandboxes_vars


def extract_sandboxes_labels(response):
    # Get the sandbox names
    resources = response.get('resources', [])
    if len(resources) == 0:
        return {}

    if len(resources) == 1:
        kind = re.sub(r'[^a-zA-Z0-9]', '', resources[0].get('kind', 'none'))
        return {
            "sandbox": resources[0].get('name', 'unknown'),
            kind: resources[0].get('name', 'unknown')
        }

    ret = {}
    increment = 2
    for sandbox in resources:
        kind = re.sub(r'[^a-zA-Z0-9]', '', sandbox.get('kind', 'none'))

        if not ret.get('sandbox', False):
            ret['sandbox'] = sandbox.get('name', 'unknown')

        if ret.get(kind, False):
            ret[kind + str(increment)] = sandbox.get('name', 'unknown')
            increment += 1
        else:
            ret[kind] = sandbox.get('name', 'unknown')

    return ret

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
            'extract_sandboxes_vars': extract_sandboxes_vars,
            'extract_sandboxes_labels': extract_sandboxes_labels,
        }
