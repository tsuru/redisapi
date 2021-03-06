# Copyright 2015 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import sys
import traceback

from aclapiclient import aclapiclient, l4_options


class GloboACLAPIManager(object):

    def __init__(self):
        endpoint = os.environ.get("ACL_API_ENDPOINT")
        username = os.environ.get("ACL_API_USERNAME")
        password = os.environ.get("ACL_API_PASSWORD")
        self.client = aclapiclient.Client(username, password, endpoint)

    def grant_access(self, instance, unit_host):
        source = unit_host[:unit_host.rindex(".")+1] + "0/24"
        for endpoint in instance.endpoints:
            desc = 'redis-api instance "{}" access from {} to {}/32'.format(instance.name, source,
                                                                            endpoint["host"])
            dest = endpoint["host"] + "/32"
            l4_opts = l4_options.L4Opts(operator="eq", port=str(endpoint["port"]), target="dest")
            try:
                self.client.add_tcp_permit_access(desc=desc, source=source,
                                                  dest=dest, l4_opts=l4_opts)
            except ValueError:
                sys.stderr.write("Failed to add permit access:\n")
                traceback.print_exc()
                sys.stderr.flush()
        self.client.commit()

    def revoke_access(self, instance, unit_host):
        source = unit_host[:unit_host.rindex(".")+1] + "0/24"
        for endpoint in instance.endpoints:
            desc = 'redis-api instance "{}" access from {} to {}/32'.format(instance.name, source,
                                                                            endpoint["host"])
            dest = endpoint["host"] + "/32"
            l4_opts = l4_options.L4Opts(operator="eq", port=str(endpoint["port"]), target="dest")
            try:
                self.client.remove_tcp_permit_access(desc=desc, source=source,
                                                     dest=dest, l4_opts=l4_opts)
            except ValueError:
                sys.stderr.write("Failed to remove permit access:\n")
                traceback.print_exc()
                sys.stderr.flush()
        self.client.commit()


class DumbAccessManager(object):

    def __init__(self):
        self.permits = {}

    def grant_access(self, instance, unit_host):
        permits = self.permits.get(instance.name)
        if not permits:
            permits = []
        permits.append(unit_host)
        self.permits[instance.name] = permits

    def revoke_access(self, instance, unit_host):
        permits = self.permits.get(instance.name)
        if permits:
            permits.remove(unit_host)
            self.permits[instance.name] = permits

access_managers = {"globo-acl-api": GloboACLAPIManager,
                   "default": DumbAccessManager}
