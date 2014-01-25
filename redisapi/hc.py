# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


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

    def add(self, host, port):
        self.zapi.item.create(
            name="redis healthcheck for {}:{}".format(host, port),
            key_="net.tcp.service[telnet,{},{}]".format(host, port),
            delay=60,
            hostid="",
            interfaceid="",
            type=3,
            value_type=3,
        )
