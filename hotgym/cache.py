import time

class CacheItem(object):
    def __init__(self, name, model = None):
        self.name = name
        self.model = model
        self.timestamp = time.time()

    def __eq__(self, item):
        return self.name == item.name

    def get_name(self):
        return self.name

    def get_model(self):
        self.timestamp = time.time()
        return self.model

    def get_timestamp(self):
        return self.timestamp

    def set_model(self, model):
        self.model = model
        self.timestamp = time.time()

class Cache(object):
    def __init__(self, size=10):
        self.size = size
        self.items = []
        self.saves = []

    def set(self, new):
        for item in self.items:
            if item == new:
                return

        self.items.append(new)

        if len(self.items) > self.size:
            items = sorted(self.items, key=lambda x: x.timestamp)
            self.saves.append(items[0])
            self.items.remove(items[0])

    def get(self, name):
        for item in self.items:
            if item.get_name() == name:
                return item

        return None

    def get_items(self):
        return self.items

    def get_saves(self):
        saves = self.saves[:]
        self.saves = []
        return saves
