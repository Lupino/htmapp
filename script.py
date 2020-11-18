import asyncio
from importlib import import_module
import os.path
import argparse
from multiprocessing import Process
import sys
import logging
formatter = "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s"
formatter += " - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=formatter)


def fixed_module_name(module_name):
    if os.path.isfile(module_name):
        if module_name.endswith('.py'):
            module_name = module_name[:-3]

        if module_name.startswith('./'):
            module_name = module_name[2:]

        return module_name.replace('/', '.')

    return module_name


def start(module_name, argv):
    print('Start running module', module_name)
    module = import_module(fixed_module_name(module_name))

    if hasattr(module, 'parse_args'):
        argv = [module.parse_args(argv)]

    if asyncio.iscoroutinefunction(module.main):
        loop = asyncio.get_event_loop()

        task = module.main(*argv)

        if getattr(module, 'run_forever', False):
            loop.create_task(task)
            loop.run_forever()
        else:
            loop.run_until_complete(task)
    else:
        module.main(*argv)
    print('Finish running module', module_name)


def main(script, *argv):
    parser = argparse.ArgumentParser(description='Prepare and Run command.')
    parser.add_argument('-p',
                        '--processes',
                        dest='processes',
                        default=1,
                        type=int,
                        help='process size. default is 1')
    parser.add_argument('module_name',
                        type=str,
                        help='module name or module file')
    parser.add_argument('argv', nargs='*', help='module arguments')

    script_argv = []

    is_module_argv = False
    module_argv = []

    for arg in argv:
        if arg.startswith('-') and not is_module_argv:
            script_argv.append(arg)
        else:
            is_module_argv = True
            module_argv.append(arg)

    if len(module_argv) > 0:
        script_argv.append(module_argv[0])
        module_argv = module_argv[1:]

    args = parser.parse_args(script_argv)

    if args.processes > 1:
        processes = []
        for i in range(args.processes):
            p = Process(target=start, args=(args.module_name, module_argv))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
    else:
        start(args.module_name, module_argv)


if __name__ == '__main__':
    main(*sys.argv)
