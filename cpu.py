import asyncio
from aio_periodic import open_connection, Client
import config
import json
from time import time
import psutil


async def main(prefix=''):
    client = Client()
    await client.connect(open_connection, config.periodic_port)

    async def submit(data):
        name = '{name}{timestamp}{value}'.format(**data)
        try:
            v = await client.run_job(prefix + 'hotgym',
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
            'name': 'cpu',
            'timestamp': int(time()),
            'value': consumption
        })
        await asyncio.sleep(5)
