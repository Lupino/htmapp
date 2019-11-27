import asyncio
from aio_periodic import open_connection, Client, Job
import config
import json
import sys

import csv
import datetime
import os
import numpy as np
import random

_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_EXAMPLE_DIR, "gymdata.csv")

async def main(loop, specid):
    client = Client(loop)
    reader, writer = await open_connection(config.periodic)
    await client.connect(reader, writer)
    async def submit(data):
        name = '{name}{timestamp}{value}'.format(**data)
        job = Job('run-hotgym-%s'%specid, name, bytes(json.dumps(data), 'utf-8'), timeout=30)
        v = await client.submit_job(job)

    # Read the input file.
    records = []
    with open(_INPUT_FILE_PATH, "r") as fin:
        reader = csv.reader(fin)
        headers = next(reader)
        next(reader)
        next(reader)
        for record in reader:
            records.append(record)
    for i in range(100):
        records.append( random.choice(records) )

    for record in records:
        # Convert data string into Python date object.
        dateString = datetime.datetime.strptime(record[0], "%m/%d/%y %H:%M")
        # Convert data value string into float.
        consumption = float(record[1])

        await submit({'name': 'test', 'timestamp': dateString.timestamp(), 'value': consumption})

loop = asyncio.get_event_loop()

specid = '1'
if len(sys.argv) > 1:
    specid = sys.argv[1]
loop.run_until_complete(main(loop, specid))
