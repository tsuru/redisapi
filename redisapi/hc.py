# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os


class FakeHealthCheck(object):
    added = False
    removed = False

    def add(self, host, port):
        self.added = True

    def remove(self, host, port):
        self.removed = True


class ZabbixHealthCheck(object):
    def __init__(self):
        url = ""
        user = ""
        password = ""
        from pyzabbix import ZabbixAPI
        self.zapi = ZabbixAPI(url)
        self.zapi.login(user, password)

        self.items = self.mongo()['redisapi']['zabbix']

    def mongo(self):
        mongodb_host = os.environ.get("MONGODB_HOST", "localhost")
        mongodb_port = int(os.environ.get("MONGODB_PORT", 27017))

        from pymongo import MongoClient
        return MongoClient(host=mongodb_host, port=mongodb_port)

    def add(self, host, port):
        item_key = "net.tcp.service[telnet,{},{}]".format(host, port)
        item_result = self.zapi.item.create(
            name="redis healthcheck for {}:{}".format(host, port),
            key_=item_key,
            delay=60,
            hostid="",
            interfaceid="",
            type=3,
            value_type=3,
        )
        trigger_result = self.zapi.trigger.create(
            description="trigger hc for redis {}:{}".format(host, port),
            expression="{{Zabbix Server:{}.last()}}=1".format(item_key),
            priority=5,
        )
        item = {
            'host': host,
            'port': port,
            'item': item_result['itemids'][0],
            'trigger': trigger_result['itemids'][0],
        }
        self.items.insert(item)

    def delete(self, host, port):
        self.zapi.trigger.delete([43])
        self.zapi.item.delete([42])


health_checkers = {
    'zabbix':  ZabbixHealthCheck,
}
