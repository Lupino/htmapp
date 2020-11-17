from .cache import CacheItem
import time

class BaseModel:
    def __init__(self, name, store, cache=None):
        self.name = name
        self.initialized = False
        self._store = store
        self.last_save_time = 0
        self.save_delay = 10 # 超过一定时间，自动保存 model
        self._cache = cache
        self._cache_item = None

        self.save_keys = ['last_save_time', 'save_delay']


    def more_save_keys(self, save_keys):
        self.save_keys += save_keys


    def create(self):
        raise NotImplementedError("you must rewrite at sub class")


    def prepare(self, model):
        for key in self.save_keys:
            setattr(self, key, model.get(key, None))


    def prepare_save(self):
        saved = {}

        for key in self.save_keys:
            val = getattr(self, key, None)
            saved[key] = val

        return saved


    def save(self):
        obj = self.prepare_save()
        self._store.save(self.name, obj)
        self.last_save_time = time.time()


    def auto_save(self):
        if self.last_save_time + self.save_delay < time.time():
            self.save()


    def set_save_delay(self, delay):
        self.save_delay = delay


    def load(self):
        if self._cache:
            item = self._cache.get(self.name)
            if item and item.get_model():
                self.prepare(item.get_model())
                self.initialized = True
                self._cache_item = item
                return True

        model = self._store.load(self.name)
        if model is None:
            return False

        if self._cache:
            self._cache_item = CacheItem(self.name, model)
            self._cache.set(self._cache_item)

        self.prepare(model)
        self.initialized = True

        return True


    def initialize(self):
        if not self.initialized:
            if not self.load():
                if not self.create():
                    return False

            if self._cache:
                self._cache_item = CacheItem(self.name, self.prepare_save())
                self._cache.set(self._cache_item)

        return self.initialized


    def __del__(self):
        self.auto_save()

        if self._cache_item:
            self._cache_item.set_model(self.prepare_save())


    def run(self, *args, **kwargs):
        raise NotImplementedError("you must rewrite at sub class")


def run(model, *args, **kwargs):
    if not model.initialized():
        return None

    model.run(*args, **kwargs)
