# Copyright 2015 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import unittest

import mock

from aclapiclient import l4_options

from redisapi import acl, storage


class GloboACLManagerTest(unittest.TestCase):

    def setUp(self):
        os.environ["ACL_API_ENDPOINT"] = self.endpoint = "http://localhost"
        os.environ["ACL_API_USERNAME"] = self.username = "redis"
        os.environ["ACL_API_PASSWORD"] = self.password = "passw"

    def tearDown(self):
        for env in ("ACL_API_ENDPOINT", "ACL_API_USERNAME", "ACL_API_PASSWORD"):
            del os.environ[env]

    @mock.patch("aclapiclient.aclapiclient.Client")
    def test_new_manager(self, Client):
        Client.return_value = client = mock.Mock()
        manager = acl.GloboACLAPIManager()
        Client.assert_called_with(self.username, self.password, self.endpoint)
        self.assertEqual(client, manager.client)

    def test_grant_access(self):
        manager = acl.GloboACLAPIManager()
        manager.client = client = mock.Mock()
        endpoints = [{"host": "10.0.0.1", "port": 4532},
                     {"host": "10.0.0.2", "port": 4536},
                     {"host": "10.0.0.3", "port": 3645}]
        instance = storage.Instance(name="myredis", endpoints=endpoints,
                                    plan="plus")
        manager.grant_access(instance, "192.168.1.13")
        calls = client.add_tcp_permit_access.call_args_list
        self.assertEqual(3, len(calls))
        desc_pat = 'redis-api instance "myredis" access from 192.168.1.13/32 to {}/32'
        self.assert_permit_call(calls[0], desc=desc_pat.format("10.0.0.1"),
                                source="192.168.1.13/32", dest="10.0.0.1/32",
                                l4_opts=l4_options.L4Opts(operator="eq", port="4532",
                                                          target="dest"))
        self.assert_permit_call(calls[1], desc=desc_pat.format("10.0.0.2"),
                                source="192.168.1.13/32", dest="10.0.0.2/32",
                                l4_opts=l4_options.L4Opts(operator="eq", port="4536",
                                                          target="dest"))
        self.assert_permit_call(calls[2], desc=desc_pat.format("10.0.0.3"),
                                source="192.168.1.13/32", dest="10.0.0.3/32",
                                l4_opts=l4_options.L4Opts(operator="eq", port="3645",
                                                          target="dest"))
        client.commit.assert_called_once()

    def test_revoke_access(self):
        manager = acl.GloboACLAPIManager()
        manager.client = client = mock.Mock()
        endpoints = [{"host": "10.0.0.1", "port": 4532},
                     {"host": "10.0.0.2", "port": 4536},
                     {"host": "10.0.0.3", "port": 3645}]
        instance = storage.Instance(name="myredis", endpoints=endpoints,
                                    plan="plus")
        manager.revoke_access(instance, "192.168.1.13")
        calls = client.remove_tcp_permit_access.call_args_list
        self.assertEqual(3, len(calls))
        desc_pat = 'redis-api instance "myredis" access from 192.168.1.13/32 to {}/32'
        self.assert_permit_call(calls[0], desc=desc_pat.format("10.0.0.1"),
                                source="192.168.1.13/32", dest="10.0.0.1/32",
                                l4_opts=l4_options.L4Opts(operator="eq", port="4532",
                                                          target="dest"))
        self.assert_permit_call(calls[1], desc=desc_pat.format("10.0.0.2"),
                                source="192.168.1.13/32", dest="10.0.0.2/32",
                                l4_opts=l4_options.L4Opts(operator="eq", port="4536",
                                                          target="dest"))
        self.assert_permit_call(calls[2], desc=desc_pat.format("10.0.0.3"),
                                source="192.168.1.13/32", dest="10.0.0.3/32",
                                l4_opts=l4_options.L4Opts(operator="eq", port="3645",
                                                          target="dest"))
        client.commit.assert_called_once()

    def assert_permit_call(self, call, desc, source, dest, l4_opts):
        kw = call[1]
        self.assertEqual(desc, kw["desc"])
        self.assertEqual(source, kw["source"])
        self.assertEqual(dest, kw["dest"])
        provided_opts = kw["l4_opts"]
        self.assertEqual(l4_opts.operator, provided_opts.operator)
        self.assertEqual(l4_opts.port, provided_opts.port)
        self.assertEqual(l4_opts.target, provided_opts.target)


class DumbManagerTest(unittest.TestCase):

    def test_grant_access(self):
        instance = storage.Instance(name="myredis", endpoints=None, plan="plus")
        manager = acl.DumbAccessManager()
        manager.grant_access(instance, "10.0.0.1")
        manager.grant_access(instance, "10.0.0.2")
        self.assertEqual(["10.0.0.1", "10.0.0.2"], manager.permits["myredis"])

    def test_revoke_access(self):
        instance = storage.Instance(name="myredis", endpoints=None, plan="plus")
        manager = acl.DumbAccessManager()
        manager.grant_access(instance, "10.0.0.1")
        manager.grant_access(instance, "10.0.0.2")
        manager.revoke_access(instance, "10.0.0.1")
        self.assertEqual(["10.0.0.2"], manager.permits["myredis"])
        manager.revoke_access(instance, "10.0.0.2")
        self.assertEqual([], manager.permits["myredis"])
