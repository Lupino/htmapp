from .checkpoint import CheckPoint
from .cache import Cache, CacheItem
from aio_periodic import Blueprint, rsp
import os
import os.path
import pickle
from .base_model import BaseModel
from .config import parameters

cache = Cache()
app = Blueprint()


def prepare(is_json=False):
    def _prepare(func):
        def __prepare(job):
            name = job.name
            data = job.workload
            new_model_name = None

            if is_json:
                data = job.workload_json
                name = data.pop('name', name)
                new_model_name = data.pop('model_name', 'hotgym')

            checkpoint = CheckPoint(os.path.join(cache.checkpoint_root, name))

            model_name = checkpoint.get_model_name()
            if not model_name and new_model_name:
                model_name = new_model_name

            if not model_name:
                return rsp.json({'err': 'model not found.'})

            checkpoint.set_default_parameters(parameters.get(model_name, {}))

            Model = BaseModel.get(model_name)

            if not Model:
                return rsp.json({'err': 'model not found.'})

            model = Model(name, checkpoint, cache)

            args = [model]

            if is_json:
                args.append(data)

            return rsp.done(func(*args))

        return __prepare

    return _prepare


@app.func('reset_model')
@prepare(is_json=True)
def run_reset_model(model, parameters):
    if isinstance(parameters, dict):
        model.checkpoint.set_parameters(parameters)

    item = cache.get(model.name)
    if item:
        item.set_updated(True)

    cache.remove(model.name)
    model.checkpoint.reset()


@app.func('set_save_delay')
@prepare(is_json=True)
def run_set_save_delay(model, data):
    with model:
        model.set_save_delay(data['save_delay'])


@app.func('save_models')
def run_save_models(job):
    cache.save_items()
    return rsp.done()


@app.func('save_model')
@prepare()
def run_set_save_model(model):
    with model:
        model.save()


@app.func('get_model')
def run_get_model(job):
    name = job.name
    item = cache.get(name)
    model = None
    if item:
        model = item.get_model()

    if model is None:
        checkpoint = CheckPoint(os.path.join(cache.checkpoint_root, name))
        model = checkpoint.load()

    return rsp.done(pickle.dumps(model))


@app.func('put_model')
def run_put_model(job):
    name = job.name
    model = None
    try:
        model = pickle.loads(job.workload)
    except Exception:
        return rsp.done()

    item = cache.get(name)
    if item:
        item.set_updated(True)
    else:
        item = CacheItem(name)
        cache.set(item)

    item.set_model(model)
    cache.save_item(item)

    return rsp.done()


def get_locker(job):
    name = job.name
    data = job.workload_json
    name = data.get('name', name)
    model_name = data.get('model_name')
    model = BaseModel.get(model_name)
    if model and model.is_train(**data):
        return name, 1

    return None, None


@app.func('run_model', locker=get_locker)
@prepare(is_json=True)
def run_model(model, data):
    if not isinstance(data, dict):
        return None

    with model:
        v = model.run(**data)
        if v:
            data.update(v)

        return data
