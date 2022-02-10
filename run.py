import sys
import logging
import runner


@runner.before_start
async def before_start(module):
    pass


@runner.after_stop
async def after_stop(module):
    cache = getattr(module, 'cache', None)
    if cache:
        cache.save_items()


if __name__ == '__main__':
    formatter = "[%(asctime)s] %(name)s:%(lineno)d %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=formatter)
    runner.main(*sys.argv)
