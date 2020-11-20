from .checkpoint import CheckPoint
from .cache import Cache, CacheItem
from .models.hotgym import Model as HotGymModel
from aio_periodic import Worker, open_connection
import time
import os
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pickle

import json

from config import parameters

import logging

logger = logging.getLogger(__name__)

cache = Cache()

worker = Worker()

run_forever = True

executor = None


def prepare(is_json=False):
    def _prepare(func):
        async def __prepare(job):
            name = job.name
            data = job.workload

            if is_json:
                data = str(data, 'utf-8')

            if is_json:
                try:
                    data = json.loads(data)
                    name = data.get('name', job.name)
                except Exception:
                    pass

            checkpoint = CheckPoint(os.path.join(cache.checkpoint_root, name))
            checkpoint.set_default_parameters(parameters)

            args = [name, checkpoint]

            if is_json:
                args.append(data)

            retval = None
            if asyncio.iscoroutinefunction(func):
                retval = await func(*args)
            else:
                retval = func(*args)

            await job.done(json.dumps(retval))

        return __prepare

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


@worker.func('reset_model')
@prepare(is_json=True)
def run_reset_model(name, checkpoint, parameters):
    if isinstance(parameters, dict):
        checkpoint.set_parameters(parameters)

    item = cache.get(name)
    if item:
        item.set_updated(True)

    cache.remove(name)
    checkpoint.reset()


@worker.func('set_save_delay')
@prepare(is_json=True)
def run_set_save_delay(name, checkpoint, data):
    with HotGymModel(name, checkpoint, cache) as model:
        model.set_save_delay(data['save_delay'])


@worker.func('save_models')
async def run_save_models(job):
    cache.save_items()
    await job.done()


@worker.func('save_model')
@prepare()
def run_set_save_model(name, checkpoint):
    with HotGymModel(name, checkpoint, cache) as model:
        model.save()


@worker.func('get_model')
async def run_get_model(job):
    name = job.name
    item = cache.get(name)
    model = None
    if item:
        model = item.get_model()

    if model is None:
        checkpoint = CheckPoint(os.path.join(cache.checkpoint_root, name))
        model = checkpoint.load()

    await job.done(pickle.dumps(model))


@worker.func('put_model')
async def run_put_model(job):
    name = job.name
    model = None
    try:
        model = pickle.loads(job.workload)
    except Exception:
        return await job.done()

    item = cache.get(name)
    if item:
        item.set_updated(True)
    else:
        item = CacheItem(name)
        cache.set(item)

    item.set_model(model)
    cache.save_item(item)

    await job.done()


@worker.func('hotgym')
@prepare(is_json=True)
@run_on_executer
def run_hotgym(name, checkpoint, data):
    if not isinstance(data, dict):
        return None

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
    parser = argparse.ArgumentParser(description='Htmapp worker.',
                                     prog=__name__)
    parser.add_argument('-s',
                        '--size',
                        dest='size',
                        default=10,
                        type=int,
                        help='work size. default is 10')
    parser.add_argument('-H',
                        '--periodic_port',
                        dest='periodic_port',
                        default='tcp://:5000',
                        type=str,
                        help='Periodicd host')
    parser.add_argument('-p',
                        '--prefix',
                        dest='prefix',
                        default='',
                        type=str,
                        help='function name prefix')
    parser.add_argument('-S',
                        '--subfix',
                        dest='subfix',
                        default='',
                        type=str,
                        help='function subfix template.')

    parser.add_argument('--cache-size',
                        dest='cache_size',
                        default=10,
                        type=int,
                        help='cache size.')

    parser.add_argument('--checkpoint',
                        dest='checkpoint',
                        default='models',
                        type=str,
                        help='CheckPoint Root.')

    parser.add_argument('enabled_tasks', nargs='*', help='Enabled tasks')

    args = parser.parse_args(argv)
    return args


async def main(args):
    global executor

    cache.size = args.cache_size
    cache.checkpoint_root = args.checkpoint

    executor = ThreadPoolExecutor(args.size)

    subfix = args.subfix
    if 'PROCESS_ID' in os.environ:
        if subfix.find('{}') > -1:
            subfix = subfix.format(os.environ['PROCESS_ID'])
        else:
            subfix += '_{}'.format(os.environ['PROCESS_ID'])

    worker.set_prefix(args.prefix)
    worker.set_subfix(subfix)
    worker.set_enable_tasks(args.enabled_tasks)

    await worker.connect(open_connection, args.periodic_port)
    worker.work(args.size)
