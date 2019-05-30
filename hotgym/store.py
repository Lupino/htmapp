import os
import os.path
import time
import pickle
import glob
import snappy

def safe_float(v):
    try:
        return float(v)
    except:
        return 0

class Store(object):
    def __init__(self, checkpoint, generation=2):
        self.checkpoint = checkpoint
        self.generation = generation

        if not os.path.isdir(checkpoint):
            os.makedirs(checkpoint)

    def remove_old_file(self):
        files = glob.glob('{}/checkpoint-*-*'.format(self.checkpoint))

        meta = {}

        for file in files:
            fns = file.split('-')
            key = '-'.join(fns[:-1])
            if key not in meta:
                meta[key] = []
            meta[key].append(safe_float(fns[-1]))

        removed = {}
        for key, val in meta.items():
            val = sorted(val, reverse=True)
            removed[key] = val[self.generation:]

        for key, val in removed.items():
            for v in val:
                fn = '{}-{}'.format(key, v)
                if os.path.isfile(fn):
                    os.remove(fn)

    def start_transaction(self, name):
        return {'name': name, "commit_id": str(time.time())}

    def commit(self, trans):
        with open(self.get_commit_file_name(trans['name']), 'w') as f:
            f.write(trans['commit_id'])

        self.remove_old_file();

    def get_commit_file_name(self, name):
        return '{}/checkpoint-{}'.format(self.checkpoint, name)

    def get_file_name(self, trans):
        return '{}/checkpoint-{}-{}'.format(self.checkpoint, trans['name'], trans['commit_id'])

    def save(self, name, obj):
        trans = self.start_transaction(name)
        try:
            with open(self.get_file_name(trans), 'wb') as f:
                data = pickle.dumps(obj)
                f.write(snappy.compress(data))
        finally:
            self.commit(trans)

    def load(self, name):
        chk = self.get_commit_file_name(name)
        if not os.path.isfile(chk):
            return None

        commit_id = None
        with open(chk, 'r') as f:
            commit_id = f.read()

        if not commit_id:
            return None

        fn = self.get_file_name({'name': name, 'commit_id': commit_id})
        if not os.path.isfile(fn):
            return None

        with open(fn, 'rb') as f:
            data = f.read()
            return pickle.loads(snappy.uncompress(data))
