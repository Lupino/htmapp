from datetime import datetime
from .store import Store
from .cache import Cache, CacheItem
from .model import Model
import asyncio
from concurrent.futures import ThreadPoolExecutor
from aio_periodic import open_connection, Worker, Client, Job
import json

from config import model_root, periodic, max_thread, parameters

import logging

logger = logging.getLogger('hotgym.worker')

cache = Cache()

locker = asyncio.Lock()

def doLoadModel(item):
    logger.info('doLoadModel ' + item.get_name())
    store = Store('{}/{}'.format(model_root, item.get_name()))
    model = Model(parameters)
    model.load(store)
    item.set_model(model)
    logger.info('model is loaded')

def doSaveModel(item):
    logger.info('doSaveModel ' + item.get_name())
    store = Store('{}/{}'.format(model_root, item.get_name()))
    item.get_model().save(store)

def runSaveAllModel(loop, executor, func=cache.get_items):
    async def run(job):
        async def run_():
            tasks = []
            for item in func():
                task = loop.run_in_executor(executor, doSaveModel, item)
                tasks.append(task)
            if len(tasks) > 0:
                await asyncio.wait(tasks)
            await job.done()

        async with locker:
            await run_()

    return run

def doCreateHotgym(name):
    store = Store('{}/{}'.format(model_root, name))
    model = Model(parameters)
    model.create()
    model.save(store)

def createHotgym(loop, executor):
    async def run(job):
        name = job.name
        task = loop.run_in_executor(executor, doCreateHotgym, name)
        await asyncio.wait([task])
        exception = task.exception()
        if exception:
            logger.exception(exception)
            await job.fail()
        else:
            await job.done()

    return run

def doRunHotgym(item, data):
    try:
        model = item.get_model()
        # Convert data string into Python date object.
        dateString = datetime.fromtimestamp(data['timestamp'])
        # Convert data value string into float.
        v = model.run(dateString, data['value'])
        data.update(v)
    except Exception as e:
        logger.exception(e)
    return data


def runHotgym(loop, executor, client, specid='1'):
    async def run(job):
        data = {}
        try:
            data = json.loads(str(job.workload, 'utf-8'))
        except Exception as e:
            logger.exception(e)
            return await job.done()

        name = data.get('name', job.name)
        async def _run():
            item = cache.get(name, 'model')
            if not item or not item.get_model():
                item = CacheItem(name, 'model')
                task = loop.run_in_executor(executor, doLoadModel, item)
                await asyncio.wait([task])
                cache.set(item)

            if not item.get_model():
                return await job.fail()

            task = loop.run_in_executor(executor, doRunHotgym, item, data)
            await asyncio.wait([task])
            exception = task.exception()
            if exception:
                logger.exception(exception)
                await job.fail()
            else:
                await job.done(task.result())

            if len(cache.saves) > 0:
                job1 = Job('save-all-old-model-%s'%specid, "save", timeout=3600)
                await client.submit_job(job1)

        await job.with_lock(name, 1, _run)

    return run

async def main(loop, executor, specid):
    client = Client(loop)
    reader, writer = await open_connection(periodic)
    await client.connect(reader, writer)

    worker = Worker(loop)
    reader, writer = await open_connection(periodic)
    await worker.connect(reader, writer)

    await worker.add_func('run-hotgym-%s'%specid, runHotgym(loop, executor, client, specid))
    await worker.add_func('create-hotgym-%s'%specid, createHotgym(loop, executor))
    await worker.add_func('save-all-model-%s'%specid, runSaveAllModel(loop, executor, cache.get_items))
    await worker.add_func('save-all-old-model-%s'%specid, runSaveAllModel(loop, executor, cache.get_saves))
    worker.work(max_thread)

def start(specid='1'):
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_thread)
    loop.create_task(main(loop, executor, specid))
    loop.run_forever()

if __name__ == '__main__':
    import sys
    specid = '1'
    if len(sys.argv) > 1:
        specid = sys.argv[1]
    start(specid)
