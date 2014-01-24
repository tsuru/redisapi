# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock


class FakeHCTest(unittest.TestCase):

    def setUp(self):
        from redisapi.hc import FakeHealthCheck
        self.hc = FakeHealthCheck()

    def test_add(self):
        self.assertFalse(self.hc.added)
        self.hc.add(host="localhost", port=8080)
        self.assertTrue(self.hc.added)

    def test_remove(self):
        self.assertFalse(self.hc.removed)
        self.hc.remove(host="localhost", port=8080)
        self.assertTrue(self.hc.removed)


class ZabbixHCTest(unittest.TestCase):

    @mock.patch("pyzabbix.ZabbixAPI")
    def setUp(self, zabbix_mock):
        zapi_mock = mock.Mock()
        zabbix_mock.return_value = zapi_mock
        from redisapi.hc import ZabbixHealthCheck
        self.hc = ZabbixHealthCheck()
        zabbix_mock.assert_called_with('')
        zapi_mock.login.assert_called_with('', '')

    def test_add(self):
        self.hc.add(host="localhost", port=8080)
