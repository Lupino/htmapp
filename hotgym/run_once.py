import time
from .checkpoint import CheckPoint
from .cache import Cache
from .models.hotgym import Model as HotGymModel
from .base_model import run
from config import model_root, parameters
import os.path

cache = Cache()


def main(name, consumption, timestamp=None):
    checkpoint = CheckPoint(os.path.join(model_root, name))
    checkpoint.set_default_parameters(parameters)
    model = HotGymModel(name, checkpoint, cache)

    if timestamp is None:
        timestamp = int(time.time())

    v = run(model, timestamp, float(consumption))
    print(v)

    model.save()
