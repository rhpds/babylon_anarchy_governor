# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: templated_var
author: Johnathan Kupferer <jkupfere@redhat.com>
version_added: "2.9"
short_description: Resolve variable with internal template strings.
description:
- Referencing a variable with `vars.` prefix disables evaluation of internal template strings.
- This lookup plugin enables selectively reenabling variable evaluation.
options:
  _terms:
    description: Input with internal variable references.
    required: True
"""

from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        ret = []
        for term in terms:
            variables['__term__'] = term
            out = self._templar.template('{{ __term__ }}')
            ret.append(out)
        return ret
