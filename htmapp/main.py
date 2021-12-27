from aio_periodic import Worker, open_connection
import os
import argparse
from .base_model import BaseModel
from .app import app, cache
from concurrent.futures import ThreadPoolExecutor

worker = Worker()
worker.blueprint(app)


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
    BaseModel.load_models()

    cache.size = args.cache_size
    cache.checkpoint_root = args.checkpoint

    subfix = args.subfix
    if 'PROCESS_ID' in os.environ:
        if subfix.find('{}') > -1:
            subfix = subfix.format(os.environ['PROCESS_ID'])

    worker.set_prefix(args.prefix)
    worker.set_subfix(subfix)
    worker.set_enable_tasks(args.enabled_tasks)
    executor = ThreadPoolExecutor(args.size * 2)
    worker.set_executor(executor)

    await worker.connect(open_connection, args.periodic_port)
    await worker.work(args.size)
