from .checkpoint import CheckPoint
from .cache import Cache
from .models.hotgym import Model as HotGymModel
from aio_periodic import Worker, open_connection
from .base_model import run
import time
import os

import json

from config import model_root, periodic_port, parameters

import logging

logger = logging.getLogger('hotgym.main')

cache = Cache(checkpoint_root=model_root)

worker = Worker()

run_forever = True


@worker.func('hotgym')
async def run_hotgym(job):
    data = {}
    try:
        data = json.loads(str(job.workload, 'utf-8'))
    except Exception as e:
        logger.exception(e)
        return await job.done()

    consumption = data.get('value')
    if consumption is None:
        return await job.done()

    name = data.get('name', job.name)
    timestamp = data.get('timestamp', int(time.time()))

    checkpoint = CheckPoint(os.path.join(model_root, name))
    checkpoint.set_default_parameters(parameters)
    model = HotGymModel(name, checkpoint, cache)

    v = run(model, timestamp, float(consumption))

    if v:
        data.update(v)

    await job.done(data)


async def main(*tasks):
    size = 10
    enabled_tasks = []
    for task in tasks:
        if task.isdigit():
            size = int(task)
        else:
            enabled_tasks.append(task)

    worker.set_enable_tasks(enabled_tasks)

    await worker.connect(open_connection, periodic_port)
    worker.work(size)
