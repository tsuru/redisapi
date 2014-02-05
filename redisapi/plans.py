# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

plans = [
    {"name": "development", "description": "Is a shared instance."},
    {"name": "basic",
     "description": "Is a dedicated instance. With 1GB of memory."},
    {"name": "plus",
     "description": "Is 3 dedicated instances. With 1GB of memory and \
HA and failover support via redis-sentinel."},
]
