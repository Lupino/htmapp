import time
from .checkpoint import CheckPoint
from .cache import Cache
from .models.hotgym import Model as HotGymModel
from config import parameters
import os.path
import argparse

cache = Cache()


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Htmapp run_once.',
                                     prog=__name__)
    parser.add_argument('-H',
                        '--periodic_port',
                        dest='periodic_port',
                        default='tcp://:5000',
                        type=str,
                        help='Periodicd host')
    parser.add_argument('-t',
                        '--timestamp',
                        dest='timestamp',
                        default=0,
                        type=int,
                        help='Timestamp of metric')

    parser.add_argument('--checkpoint',
                        dest='checkpoint',
                        default='models',
                        type=str,
                        help='CheckPoint Root.')

    parser.add_argument('metric', help='Metric name')
    parser.add_argument('value', type=int, help='Metric value')

    args = parser.parse_args(argv)
    return args


def main(args):
    checkpoint = CheckPoint(os.path.join(args.checkpoint, args.metric))
    checkpoint.set_default_parameters(parameters)

    timestamp = args.timestamp

    if timestamp == 0:
        timestamp = int(time.time())

    with HotGymModel(args.metric, checkpoint, cache) as model:
        v = model.run(timestamp, args.value)
        print(v)
        model.save()
