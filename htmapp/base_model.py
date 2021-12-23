from .cache import CacheItem
from importlib import import_module
import time
import os
import os.path
from glob import glob


class ModelError(Exception):
    pass


class BaseModel(object):
    model_name = 'base_model'
    models = {}

    def __init__(self, name, checkpoint, cache=None):
        self.name = name
        self.initialized = False
        self.checkpoint = checkpoint
        self.last_save_time = 0
        self.save_delay = 0  # 超过一定时间，自动保存 model
        self._cache = cache
        self._cache_item = None

        self.save_keys = ['last_save_time', 'save_delay']

    def more_save_keys(self, save_keys):
        self.save_keys += save_keys

    def create(self):
        raise NotImplementedError("you must rewrite at sub class")

    def prepare(self, model):
        for key in self.save_keys:
            val = model.get(key)
            if val is None:
                return False

            setattr(self, key, val)

        self.initialized = True
        return True

    def prepare_save(self):
        saved = {'model_name': self.model_name}

        for key in self.save_keys:
            val = getattr(self, key, None)
            saved[key] = val

        return saved

    def save(self):
        self.last_save_time = time.time()
        self.checkpoint.save(self.prepare_save())
        self.checkpoint.set_model_name(self.model_name)

    def auto_save(self):
        if self.save_delay == 0:
            return

        if self.last_save_time + self.save_delay < time.time():
            self.save()

    def set_save_delay(self, delay):
        self.save_delay = delay

    def load(self):
        if self._cache:
            self._cache_item = self._cache.get(self.name)
            if self._cache_item and self._cache_item.get_model():
                self._cache_item.set_updated(False)
                return self.prepare(self._cache_item.get_model())

        model = self.checkpoint.load()
        if model is None:
            return False

        if self._cache:
            self._cache_item = CacheItem(self.name, model)
            self._cache.set(self._cache_item)

        return self.prepare(model)

    def initialize(self):
        if not self.initialized:
            if not self.load():
                self.create()
                self.initialized = True

        return self.initialized

    def run(self, *args, **kwargs):
        raise NotImplementedError("you must rewrite at sub class")

    def __enter__(self):
        if not self.initialize():
            raise ModelError('Initialize failed.')

        return self

    def __exit__(self, type, value, traceback):
        if self._cache_item:
            if self._cache_item.get_updated():
                return
            self._cache_item.set_updated(True)

        self.auto_save()

        if self._cache_item:
            self._cache_item.set_model(self.prepare_save())

    @classmethod
    def load_models(cls):
        path = os.path.dirname(__file__)
        for model in glob(os.path.join(path, 'models', '*.py')):
            module_name = os.path.basename(model)[:-3]
            module = import_module('htmapp.models.' + module_name)
            for cls_name in dir(module):
                cls = getattr(module, cls_name, None)
                if hasattr(cls, 'model_name'):
                    if cls.model_name == 'base_model':
                        continue

                    cls.models[cls.model_name] = cls

    @classmethod
    def get(cls, name):
        return cls.models.get(name, None)
