# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: unsafe_var
author: Johnathan Kupferer <jkupfere@redhat.com>
version_added: "2.19"
short_description: Get var value with unsafe marker.
description:
- Access variable contents while avoiding evaluation of any contained template strings.
options:
  _terms:
    description: Input with internal variable references.
    required: True
"""

from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        """
        Extract variable value without evaluating template strings.
        Currently only supports dot, ".", syntax for dictionary key reference.
        Ex: anarchy_subject.spec.vars.job_vars
        """
        ret = []
        for term in terms:
            variables['__term__'] = term
            val = variables
            for item in term.split('.'):
                val = val[item]
            ret.append(val)
        return ret
