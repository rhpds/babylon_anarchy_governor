# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: git_tag_prefix
author: Johnathan Kupferer <jkupfere@redhat.com>
version_added: "2.9"
short_description: Resolve git tag prefix to find latest version.
description:
- This lookup checks a git repository and returns a list of tags in the repo matching a prefix.
options:
  _terms:
    description: git tag prefix to match
    required: True
notes:
- Only git repos of the form https://github.com/ORG/REPO are supported at this time.
"""
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()

from packaging import version
import re
import requests

class LookupModule(LookupBase):

    def run(self, terms, git_repo=None, variables=None, **kwargs):

        # lookups in general are expected to both take a list as input and output a list
        # this is done so they work with the looping construct 'with_'.
        ret = []
        for term in terms:
            display.debug("File lookup term: %s" % term)

            if not git_repo:
                raise AnsibleError('git_repo must be passed to git_tag_prefix lookup')

            match = re.match(r'https://([^/]+)/(.*)', git_repo)
            if not match:
                raise AnsibleError('sorry, cannot handle git repo url format {}'.format(git_repo))

            git_host = match[1]
            git_path = match[2]

            if git_host == 'github.com':
                parts = git_path.split('/')
                if len(parts) != 2:
                    raise AnsibleError('github repo path has too many parts {}'.format(git_path))
                git_org = parts[0]
                git_repo = re.sub('\.git$', '', parts[1])
                r = requests.get('https://api.github.com/repos/{}/{}/git/refs/tags'.format(git_org, git_repo))
                r.raise_for_status()
                latest_tag = None
                latest_version = None
                tag_re = re.compile(r'refs/tags/({}-?v?([0-9.]+))$'.format(re.escape(term)))
                for tag_ref in r.json():
                    m = tag_re.match(tag_ref['ref'])
                    if m:
                        m_version = version.parse(m[2])
                        if not latest_version or latest_version < m_version:
                            latest_tag = m[1]
                            latest_version = latest_version
                if not latest_tag:
                    raise AnsibleError('unable to match git tag prefix {}'.format(term))
                ret.append(latest_tag)

            else:
                raise AnsibleError('sorry, do not know how to find tags from {}'.format(git_host))

        return ret
