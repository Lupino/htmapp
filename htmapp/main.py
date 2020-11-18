from .checkpoint import CheckPoint
from .cache import Cache
from .models.hotgym import Model as HotGymModel
from aio_periodic import Worker, open_connection
import time
import os
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor

import json

from config import model_root, periodic_port, parameters

import logging

logger = logging.getLogger(__name__)

cache = Cache(checkpoint_root=model_root)

worker = Worker()

run_forever = True

executor = None


def prepare(func):
    async def _prepare(job):
        data = {}
        try:
            data = json.loads(str(job.workload, 'utf-8'))
        except Exception as e:
            logger.exception(e)
            return await job.done('null')

        name = data.get('name', job.name)

        checkpoint = CheckPoint(os.path.join(model_root, name))
        checkpoint.set_default_parameters(parameters)

        retval = None
        if asyncio.iscoroutinefunction(func):
            retval = await func(name, checkpoint, data)
        else:
            retval = func(name, checkpoint, data)

        await job.done(json.dumps(retval))

    return _prepare


def run_on_executer(func):
    async def _run_on_executer(*args, **kwargs):
        if executor:
            loop = worker.loop
            task = loop.run_in_executor(executor, func, *args, **kwargs)
            await asyncio.wait([task])
            return task.result()
        else:
            return func(*args, **kwargs)

    return _run_on_executer


@worker.func('set_parameters')
@prepare
def run_set_parameters(name, checkpoint, parameters):
    checkpoint.set_parameters(parameters)
    cache.remove(name)
    checkpoint.reset()


@worker.func('hotgym')
@prepare
@run_on_executer
def run_hotgym(name, checkpoint, data):
    consumption = data.get('value')
    if consumption is None:
        return data

    timestamp = data.get('timestamp', int(time.time()))

    with HotGymModel(name, checkpoint, cache) as model:
        v = model.run(timestamp, float(consumption))
        if v:
            data.update(v)

        return data


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Hotgym worker.',
                                     prog=__name__)
    parser.add_argument('-s',
                        '--size',
                        dest='size',
                        default=10,
                        type=int,
                        help='work size. default is 10')
    parser.add_argument('-p',
                        '--prefix',
                        dest='prefix',
                        default='',
                        type=str,
                        help='work prefix. default is None')

    parser.add_argument('enabled_tasks', nargs='*', help='Enabled tasks')

    args = parser.parse_args(argv)
    return args


async def main(args):
    global executor

    executor = ThreadPoolExecutor(args.size)

    worker.set_prefix(args.prefix)
    worker.set_enable_tasks(args.enabled_tasks)

    await worker.connect(open_connection, periodic_port)
    worker.work(args.size)