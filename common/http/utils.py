from types import GeneratorType
from itertools import zip_longest


def sort_by_attr(target_attrs: list):
    """
    This function is designed to serve as *key* parameter in sort() and the same kind functions
    It will check if any of provided target_attrs is in obj.__dict__ and return it if this is the case.
    """
    def wrapped(obj):
        for _type in target_attrs:
            if _type in obj.__dict__:
                return _type
    return wrapped


def formatter(data, key=None) -> GeneratorType:
    """
    Helper function to preformat http responses data
    """
    if type(data) is dict:
        if key in data:
            yield from formatter(data[key], key)
        else:
            yield data
    elif type(data) is list:
        yield from data
    elif type(data) is GeneratorType:
        for item in data:
            yield from formatter(item, key)
    else:
        yield data


class Chunker:

    def __init__(self, items: list, limit: int=1):
        self.limit = limit
        self.items = items

    def __iter__(self):
        if len(self.items) > self.limit:
            return (list(filter(lambda x: x, item)) for item in zip_longest(*[iter(self.items)] * self.limit))
        else:
           return (self.items for _ in [1])
