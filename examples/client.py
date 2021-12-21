import asyncio
from aio_periodic import open_connection, Client
import argparse
import json

import csv
import datetime
import os
import random
from htmapp.utils import get_nodes

_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_EXAMPLE_DIR, "gymdata.csv")


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
    metric_name = 'test'
    func = hr.get_node(metric_name)
    if not func:
        func = '{}'

    await client.run_job(func.format('reset_model'), 'test')

    async def submit(data):
        name = '{name}{timestamp}{consumption}'.format(**data)
        try:
            v = await client.run_job(func.format('run_model'),
                                     name,
                                     bytes(json.dumps(data), 'utf-8'),
                                     timeout=30)
            try:
                data = json.loads(str(v, 'utf-8'))
                print('value={} anomaly={}'.format(data['value'],
                                                   data['anomaly']))
            except Exception:
                print(v)

        except Exception as e:
            print(e)
            await asyncio.sleep(10)

    # Read the input file.
    records = []
    with open(_INPUT_FILE_PATH, "r") as fin:
        reader = csv.reader(fin)
        next(reader)
        next(reader)
        next(reader)
        for record in reader:
            records.append(record)
    for i in range(100):
        records.append(random.choice(records))

    for record in records:
        # Convert data string into Python date object.
        dateString = datetime.datetime.strptime(record[0], "%m/%d/%y %H:%M")
        # Convert data value string into float.
        consumption = float(record[1])

        await submit({
            'name': metric_name,
            'timestamp': dateString.timestamp(),
            'model_name': 'hotgym',
            'consumption': consumption
        })
