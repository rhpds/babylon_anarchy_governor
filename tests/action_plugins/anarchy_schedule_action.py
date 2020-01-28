#!/usr/bin/python

# Copyright: (c) 2019, Johnathan Kupferer <jkupfere@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import os
from copy import deepcopy
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None, **_):
        result = super(ActionModule, self).run(tmp, task_vars)
        test_output_dir = task_vars.get('test_output_dir', '.')
        fh = open(os.path.join(test_output_dir, 'anarchy_scheduled_actions.yaml'), 'a')
        fh.write('- ' + json.dumps(self._task.args))
        result.update(deepcopy(self._task.args))
        return result
