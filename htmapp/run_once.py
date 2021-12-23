from .checkpoint import CheckPoint
from .cache import Cache
from .base_model import BaseModel
from .config import parameters
import os.path
import argparse
import json

import logging

logger = logging.getLogger(__name__)

cache = Cache()


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Htmapp run_once.',
                                     prog=__name__)

    parser.add_argument('--checkpoint',
                        dest='checkpoint',
                        default='models',
                        type=str,
                        help='CheckPoint Root.')

    parser.add_argument('-m',
                        '--model',
                        dest='model',
                        default='hotgym',
                        type=str,
                        help='Htmapp model.')

    parser.add_argument('metric', help='Metric name')
    parser.add_argument('data', help='Metric data')

    args = parser.parse_args(argv)
    return args


def main(args):
    BaseModel.load_models()

    checkpoint = CheckPoint(os.path.join(args.checkpoint, args.metric))

    model_name = checkpoint.get_model_name()

    if not model_name:
        model_name = args.model

    if model_name != args.model:
        logger.error('Model expect {} but got {} not match.'.format(
            model_name, args.model))
        return

    checkpoint.set_default_parameters(parameters[model_name])

    Model = BaseModel.get(model_name)

    if not Model:
        logger.error('Model {} not found.'.format(model_name))
        return

    data = json.loads(args.data)

    with Model(args.metric, checkpoint, cache) as model:
        v = model.run(**data)
        print(v)
        model.save()
