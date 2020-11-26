import asyncio
from aio_periodic import open_connection, Client
import argparse
import json
from time import time
import psutil

from htmapp.utils import get_nodes


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Htmapp examples.',
                                     prog=__name__)
    parser.add_argument('-H',
                        '--periodic_port',
                        dest='periodic_port',
                        default='tcp://:5000',
                        type=str,
                        help='Periodicd host')
    args = parser.parse_args(argv)
    return args


async def main(args):

    client = Client()
    await client.connect(open_connection, args.periodic_port)

    hr = await get_nodes(client)
    metric_name = 'cpu'
    func = hr.get_node(metric_name)

    async def submit(data):
        name = '{name}{timestamp}{value}'.format(**data)
        try:
            v = await client.run_job(func.format('hotgym'),
                                     name,
                                     bytes(json.dumps(data), 'utf-8'),
                                     timeout=30)
            try:
                data = json.loads(str(v, 'utf-8'))
                print('cpu={} anomaly={}'.format(data['value'],
                                                 data['anomaly']))
            except Exception:
                print(v)

            with open('cpu.txt', 'ab') as f:
                f.write(v)
                f.write(b'\n')
        except Exception as e:
            print(e)
            await asyncio.sleep(10)

    while True:
        consumption = psutil.cpu_percent()
        await submit({
            'name': metric_name,
            'model_name': 'hotgym',
            'timestamp': int(time()),
            'value': consumption
        })
        await asyncio.sleep(5)
