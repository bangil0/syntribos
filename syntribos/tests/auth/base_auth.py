# Copyright 2016 Rackspace
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from oslo_config import cfg

import syntribos
from syntribos.clients.http import client
import syntribos.extensions.identity.client
import syntribos.tests.auth.datagen
from syntribos.tests import base


CONF = cfg.CONF


class BaseAuthTestCase(base.BaseTestCase):
    client = client()

    @classmethod
    def setUpClass(cls):
        super(BaseAuthTestCase, cls).setUpClass()
        cls.issues = []
        cls.failures = []
        cls.resp = cls.client.request(
            method=cls.request.method, url=cls.request.url,
            headers=cls.request.headers, params=cls.request.params,
            data=cls.request.data)

    @classmethod
    def tearDownClass(cls):
        super(BaseAuthTestCase, cls).tearDownClass()
        for issue in cls.issues:
            if issue.failure:
                cls.failures.append(issue.as_dict())

    def test_case(self):
        description = ("This request did not fail with 404 (User not found)"
                       " therefore it indicates that authentication with"
                       " another user's token was successful.")
        self.register_issue(
            defect_type="try_alt_user_token",
            severity=syntribos.HIGH,
            confidence=syntribos.HIGH,
            description=description,
        )
        self.test_issues()

    @classmethod
    def get_test_cases(cls, filename, file_content):
        """Generates the test cases

        For this particular test, only a single test
        is created (in addition to the base case, that is)
        """

        # TODO(cneill): FIX THIS!
        alt_user_id = "1"

        if alt_user_id is None:
            return

        request_obj = syntribos.tests.auth.datagen.AuthParser.create_request(
            file_content, CONF.syntribos.endpoint)

        prepared_copy = request_obj.get_prepared_copy()
        cls.init_response = cls.client.send_request(prepared_copy)

        prefix_name = "{filename}_{test_name}_{fuzz_file}_".format(
            filename=filename, test_name=cls.test_name, fuzz_file='auth')

        # TODO(cneill): FIX THIS
        version = "v2"

        if version is None or version == 'v2':
            alt_token = syntribos.extensions.identity.client.get_token_v2(
                'alt_user', 'auth')
        else:
            alt_token = syntribos.extensions.identity.client.get_token_v3(
                'alt_user', 'auth')
        alt_user_token_request = request_obj.get_prepared_copy()
        for h in alt_user_token_request.headers:
            if 'x-auth-token' == h.lower():
                alt_user_token_request.headers[h] = alt_token

        test_name = prefix_name + 'another_users_token'

        def test_gen(test_name, request):
            yield (test_name, request)

        for name, req in test_gen(test_name, alt_user_token_request):
            c = cls.extend_class(test_name,
                                 {"request": alt_user_token_request})
            yield c
