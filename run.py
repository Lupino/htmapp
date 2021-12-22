import sys
import logging
from htmapp import run


@run.before_start
async def before_start(module):
    pass


@run.after_stop
async def after_stop(module):
    cache = getattr(module, 'cache', None)
    if cache:
        cache.save_items()

if __name__ == '__main__':
    formatter = "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=formatter)
    run.main(*sys.argv)
