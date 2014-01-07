# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import redis


try:
    server = os.environ["REDIS_SERVER_HOST"]
except KeyError:
    msg = u"You must define the REDIS_SERVER_HOST environment variable."
    raise Exception(msg)


def coalesce(default, *args):
    for arg in args:
        val = os.environ.get(arg)
        if val:
            return val
    return default


class FakeManager(object):
    instance_added = False
    binded = False
    unbinded = False
    removed = False
    ok = False
    msg = "error"

    def add_instance(self):
        self.instance_added = True

    def bind(self):
        self.binded = True

    def unbind(self):
        self.unbinded = True

    def remove(self):
        self.removed = True

    def is_ok(self):
        return self.ok, self.msg


class RedisManager(object):
    def add_instance(self):
        pass

    def bind(self):
        host = coalesce(server, "REDIS_PUBLIC_HOST")
        port = coalesce("6379", "REDIS_SERVER_PORT")
        result = {
            "REDIS_HOST": host,
            "REDIS_PORT": port,
        }
        pswd = os.environ.get("REDIS_SERVER_PASSWORD")
        if pswd:
            result["REDIS_PASSWORD"] = pswd
        return result

    def unbind(self):
        pass

    def remove_instance(self):
        pass

    def is_ok(self):
        passwd = os.environ.get("REDIS_SERVER_PASSWORD")
        kw = {"host": server}
        if passwd:
            kw["password"] = passwd
        try:
            conn = redis.Connection(**kw)
            conn.connect()
        except Exception as e:
            return False, str(e)
        return True, ""
