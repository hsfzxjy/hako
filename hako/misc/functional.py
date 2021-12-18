import typing as t

R = t.TypeVar("R")


def zip_strict(*iterables):
    if not iterables:
        return
    iterators = tuple(iter(iterable) for iterable in iterables)
    try:
        while True:
            items = []
            for iterator in iterators:
                items.append(next(iterator))
            yield tuple(items)
    except StopIteration:
        pass
    if items:
        i = len(items)
        raise ValueError(i, i - 1, "shorter")
    sentinel = object()
    for i, iterator in enumerate(iterators[1:], 1):
        if next(iterator, sentinel) is not sentinel:
            raise ValueError(i, i - 1, "longer")
