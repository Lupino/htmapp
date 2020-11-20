from aio_periodic import open_connection, Client
import json
import argparse
import sys

from .utils import get_func_name


async def save_models(client):
    st = await client.status()
    funcs = [k for k in st.keys() if k.find('save_models') > -1]

    for func in funcs:
        await run_job(client, func, 'metric')


async def run_job(client,
                  func_name,
                  metric_name,
                  value='',
                  is_json=False,
                  output=None):
    data = await client.run_job(func_name,
                                metric_name,
                                timeout=30,
                                workload=value)

    if output:
        with open(output, 'wb') as f:
            f.write(data)
    else:
        if is_json:
            data = json.loads(str(data, 'utf-8'))
            print(data)


def prepare_value(args):
    if getattr(args, 'parameters', None):
        with open(args.parameters, 'rb') as f:
            return f.read()

    if getattr(args, 'model', None):
        with open(args.model, 'rb') as f:
            return f.read()

    if getattr(args, 'delay', None):
        return bytes(json.dumps({'save_delay': args.delay}), 'utf-8')

    return ''


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Htmapp cli.', prog=__name__)

    parser.add_argument('-H',
                        '--periodic_port',
                        dest='periodic_port',
                        default='tcp://:5000',
                        type=str,
                        help='Periodicd host')

    subparsers = parser.add_subparsers(help='sub-command help',
                                       title='subcommands',
                                       description='valid subcommands')

    parser_get_model = subparsers.add_parser('get_model', help='Get model')
    parser_get_model.add_argument('metric', type=str, help='The metric name.')
    parser_get_model.add_argument('output',
                                  type=str,
                                  help='The output file name.')
    parser_get_model.set_defaults(func=run_job, action='get_model')

    parser_put_model = subparsers.add_parser('put_model', help='Put model')
    parser_put_model.add_argument('metric', type=str, help='The metric name.')
    parser_put_model.add_argument('model',
                                  type=str,
                                  help='The model file name.')
    parser_put_model.set_defaults(func=run_job, action='put_model')

    parser_save_model = subparsers.add_parser('save_model', help='Save model')
    parser_save_model.add_argument('metric', type=str, help='The metric name.')
    parser_save_model.set_defaults(func=run_job, action='save_model')

    parser_reset_model = subparsers.add_parser('reset_model',
                                               help='Reset model')
    parser_reset_model.add_argument('metric',
                                    type=str,
                                    help='The metric name.')
    parser_reset_model.add_argument('-p',
                                    '--parameters',
                                    type=str,
                                    help='The parameters.json file path.')
    parser_reset_model.set_defaults(func=run_job, action='reset_model')

    parser_save_models = subparsers.add_parser('save_models',
                                               help='Save all model')
    parser_save_models.set_defaults(func=save_models, action='save_models')

    parser_set_save_delay = subparsers.add_parser('set_save_delay',
                                                  help='Set model save delay')
    parser_set_save_delay.add_argument('metric',
                                       type=str,
                                       help='The metric name.')
    parser_set_save_delay.add_argument('delay',
                                       type=float,
                                       help='The save delay.')
    parser_set_save_delay.set_defaults(func=run_job, action='set_save_delay')

    args = parser.parse_args(argv)
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)

    return args


async def main(args):
    client = Client()
    await client.connect(open_connection, args.periodic_port)

    if hasattr(args, 'metric'):
        func_name = await get_func_name(client, args.action, args.metric)
        await args.func(client,
                        func_name,
                        args.metric,
                        output=getattr(args, 'output', None),
                        value=prepare_value(args))

    if args.action == 'save_models':
        await args.func(client)
