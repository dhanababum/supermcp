class SingletonDictionary:
    _instance = None
    _data = {}  # The actual dictionary to be managed as a singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonDictionary, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # __init__ will be called every time a new "instance" is created,
        # but the actual dictionary (_data) is only initialized once
        # through the _instance check in __new__.
        pass

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()
