# Copyright 2014 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import os

import mock

from redisapi.auth import scheme_info, Unauthorized, user_info


class AuthTest(unittest.TestCase):
    @mock.patch("requests.get")
    def test_scheme_info(self, get_mock):
        tsuru_host = "http://localhost"
        os.environ["TSURU_HOST"] = tsuru_host
        expected_url = '{}/auth/scheme'.format(tsuru_host)

        self.assertDictEqual(scheme_info(), {})
        get_mock.assert_called_with(expected_url)

        response_mock = mock.Mock(status_code=200)
        response_mock.json.return_value = {"name": "oauth"}
        get_mock.return_value = response_mock

        self.assertDictEqual(scheme_info(), {"name": "oauth"})

    @mock.patch("requests.get")
    def test_user_info_with_invalid_token(self, get_mock):
        get_mock.return_value = mock.Mock(status_code=401)
        self.assertRaises(Unauthorized, user_info, "invalidtoken")
