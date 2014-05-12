# Copyright 2014 redis-api authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os


plans = [
    {"name": "development", "description": "Is a shared instance."},
    {"name": "basic",
     "description": "Is a dedicated instance. With 1GB of memory."},
    {"name": "plus",
     "description": "Is 2 dedicated instances. With 1GB of memory and \
HA and failover support via redis-sentinel."},
]


def active():
    plans_environ = os.environ.get("REDIS_API_PLANS", "[]")
    active_plans_name = json.loads(plans_environ)
    active_plans = []
    for plan in plans:
        if plan["name"] in active_plans_name:
            active_plans.append(plan)
    return active_plans
