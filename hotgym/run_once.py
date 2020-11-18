import time
from .checkpoint import CheckPoint
from .cache import Cache
from .models.hotgym import Model as HotGymModel
from config import model_root, parameters
import os.path

cache = Cache()


def main(name, consumption, timestamp=None):
    checkpoint = CheckPoint(os.path.join(model_root, name))
    checkpoint.set_default_parameters(parameters)

    if timestamp is None:
        timestamp = int(time.time())

    with HotGymModel(name, checkpoint, cache) as model:
        v = model.run(timestamp, float(consumption))
        print(v)
        model.save()
