#!/usr/bin/python
# 
# Copyright: (c) 2020, Johnathan Kupferer <jkupfere@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import requests
import yaml

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

requests_retry = Retry(backoff_factor=1, total=5)
requests_adapter = HTTPAdapter(max_retries = requests_retry)
requests_session = requests.Session()
requests_session.mount('https://', requests_adapter)

user_body_regex = re.compile(r'^user\.body:\s*')
user_data_regex = re.compile(r'^user\.data:\s*')
user_info_regex = re.compile(r'^user\.info:\s*')

class ActionModule(ActionBase):
    '''Print statements during execution and save user info to file'''

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('host','job_id','user','page_size','password','validate_certs'))

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        result['_ansible_verbose_always'] = True
        del tmp # tmp no longer has any effect

        for required_arg in ('host', 'job_id', 'user', 'password'):
            if not required_arg in self._task.args:
                result['failed'] = True
                result['error'] = required_arg + " is required"
                return result

        job_id = self._task.args.get('job_id')
        host = self._task.args.get('host')
        user = self._task.args.get('user')
        password = self._task.args.get('password')
        page_size = self._task.args.get('page_size', 100)
        validate_certs = boolean(self._task.args.get('validate_certs', True), strict=False)

        page = 1
        url = f"https://{host}/api/v2/jobs/{job_id}/job_events/?page_size={page_size}"
        provision_data = {}
        provision_message_body = []
        provision_messages = []

        while True:
          resp = requests_session.get(url, auth = (user, password), verify = validate_certs)
          resp_data = resp.json()
          for result in resp_data.get('results', []):
              event_data = result.get('event_data', {})
              task_action = event_data.get('task_action')
              event_res = event_data.get('res', {})
              if task_action == 'agnosticd_user_info':
                  data = event_res.get('data')
                  msg = event_res.get('msg')
                  if msg:
                      messages = [msg] if isinstance(msg, string_types) else msg
                      for message in messages:
                          provision_messages.append(user_info_regex.sub('', message))
                  if data:
                      provision_data.update(data)
              elif task_action == 'debug':
                  msg = event_res.get('msg')
                  if msg:
                      messages = [msg] if isinstance(msg, string_types) else msg
                      for message in messages:
                          if user_body_regex.search(message):
                              provision_message_body.append(user_body_regex.sub('', message))
                          elif user_data_regex.search(message):
                              provision_data.update(yaml.safe_load(user_data_regex.sub('', message)))
                          elif user_info_regex.search(message):
                              provision_messages.append(user_info_regex.sub('', message))

          next_url_path = resp_data.get('next')
          if next_url_path:
              url = f"https://{host}{next_url_path}"
          else:
              break

        return {
          "failed": False,
          "provision_data": provision_data,
          "provision_message_body": provision_message_body,
          "provision_messages": provision_messages,
        }
