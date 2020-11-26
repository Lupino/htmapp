import os
import os.path
from time import time
import glob
import pickle
import json

import logging
logger = logging.getLogger(__name__)

try:
    import snappy
except Exception:
    snappy = None


def safe_float(v):
    try:
        return float(v)
    except Exception:
        return 0


class CheckPoint(object):
    def __init__(self, checkpoint, generation=2, compress=True):
        self.checkpoint = checkpoint
        self.checkpoint_path = os.path.join(self.checkpoint, 'checkpoint')
        if not os.path.isdir(checkpoint):
            os.makedirs(checkpoint)

        self.generation = generation

        self.compress = compress
        if snappy is None:
            self.compress = False

    def _get_checkpoint(self):
        if not os.path.isfile(self.checkpoint_path):
            return None

        with open(self.checkpoint_path, 'r') as f:
            return f.read().strip()

    def _new_checkpoint(self):
        return 'checkpoint-{}'.format(time())

    def _write_checkpoint(self, checkpoint):
        with open(self.checkpoint_path, 'w') as f:
            f.write(checkpoint)

    def _get_parameters_path(self):
        return '{}/parameters.json'.format(self.checkpoint)

    def _get_model_name_path(self):
        return '{}/model_name'.format(self.checkpoint)

    def set_default_parameters(self, parameters):
        path = self._get_parameters_path()
        if not os.path.isfile(path):
            self.set_parameters(parameters)

    def set_parameters(self, parameters):
        path = self._get_parameters_path()
        with open(path, 'w') as f:
            json.dump(parameters, f, indent=2)

    def get_parameters(self):
        path = self._get_parameters_path()
        if not os.path.isfile(path):
            return None

        with open(path, 'r') as f:
            return json.load(f)

    def set_model_name(self, model_name):
        path = self._get_model_name_path()
        with open(path, 'w') as f:
            f.write(model_name)

    def get_model_name(self):
        path = self._get_model_name_path()
        if not os.path.isfile(path):
            return None

        with open(path, 'r') as f:
            return f.read().strip()

    def remove_old_file(self):
        files = glob.glob('{}/checkpoint-*'.format(self.checkpoint))

        checkpoints = []
        for file in files:
            fns = file.split('-')
            checkpoints.append(safe_float(fns[-1]))

        checkpoints = sorted(checkpoints, reverse=True)
        removed = checkpoints[self.generation:]

        for t in removed:
            fn = '{}/checkpoint-{}'.format(self.checkpoint, t)
            if os.path.isfile(fn):
                os.remove(fn)

    def save(self, obj):
        checkpoint = self._new_checkpoint()
        path = os.path.join(self.checkpoint, checkpoint)
        logger.info('Save checkpoint: {}'.format(path))
        with open(path, 'wb') as f:
            data = pickle.dumps(obj)
            if self.compress:
                data = snappy.compress(data)
            f.write(data)
        self._write_checkpoint(checkpoint)
        self.remove_old_file()

    def load(self):
        checkpoint = self._get_checkpoint()
        if not checkpoint:
            return None

        path = os.path.join(self.checkpoint, checkpoint)
        if not os.path.isfile(path):
            return None

        try:
            with open(path, 'rb') as f:
                data = f.read()
                if self.compress:
                    data = snappy.uncompress(data)
                return pickle.loads(data)
        except Exception:
            return None

    def reset(self):
        files = glob.glob('{}/checkpoint-*'.format(self.checkpoint))

        for file in files:
            os.remove(file)
