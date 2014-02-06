# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


class Instance(object):

    def __init__(self, host, container_id, port, name):
        self.host = host
        self.container_id = container_id
        self.port = port
        self.name = name

    def to_json(self):
        return {
            'host': self.host,
            'container_id': self.container_id,
            'port': self.port,
            'name': self.name
        }
