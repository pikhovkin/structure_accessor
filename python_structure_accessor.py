#!/usr/bin/env python
# -*- coding: utf-8 -*-

class BaseObject(object):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, index):
        return self.__dict__['data'][index]


class LazyDict(BaseObject):
    def __getattr__(self, key):
        if isinstance(self.data, list):
            return [item[key] for item in self.data]

        try:
            value = self.__dict__['data'][key]
            if isinstance(value, list):
                return path(value)
        except TypeError:
            pass

        if isinstance(self.__dict__['data'], dict):
            if isinstance(value, (int, float, str, unicode)):
                return (value,)


class LazyList(BaseObject):
    def __getattr__(self, key):
        if isinstance(self.data, list):
            if self.data:
                if self.data[0].__class__.__name__ == 'Meta':
                    return [item[key] for item in self.data]
                if isinstance(self.data[0], dict):
                    return path([LazyDict(item)[key] for item in self.data
                        if isinstance(item, dict) and (key in item)])
                if isinstance(self.data[0], LazyDict):
                    return [item[key] for item in self.data]
                if isinstance(self.data[0], list):
                    concat_list = []
                    [[concat_list.append(LazyDict(item)[key]) for item in items
                        if isinstance(item, dict) and (key in item)]
                            for items in self.data]
                    return path(concat_list)
            return [path(item[key]) for item in self.__dict__['data']
                if isinstance(item, dict) and (key in item)]

        return super(LazyList, self).__getitem__(index)

    def __getitem__(self, index):
        if isinstance(self.data, list):
            if self.data:
                if self.data[0].__class__.__name__ == 'Meta':
                    return path([LazyMeta(item)[index] for item in self.data])
                if isinstance(self.data[0], list):
                    return path([path(item)[index] for item in self.data])

        return self.__dict__['data'][index]

    def __getslice__(self, i, j):
        return path(self.data[max(0, i):max(0, j):])


class LazyMeta(BaseObject):
    def __getitem__(self, index):
        if isinstance(self.data, list):
            return path([item[index] for item in self.data])

        return path(self.data.__dict__[index])


def is_generator(data):
    return True if 'next' in dir(data) else False

def path(data):
    """Эта функция предназначена для выбора подмножества данных из переданного
    ей словаря, списка или iterable объекта.

    Так же, она позволяет получать атрибуты объектов или ключи словарей,
    а так же выбирать данные внутри них. Для
    этого используется синтаксис типа "XPath".

    Все вычисления "ленивые". В процессе работы, функция, по возможности,
    не должна создавать лишних списков и словарей
    и должна работать "на лету", позволяя обрабатывать бесконечный поток
    структурированных данных.

    >>> class Meta(object):
    ...     def __init__(self, value):
    ...         self.value = value
    ...         self.dvalue = dict(a = value)
    ...     def __repr__(self):
    ...         return u'<meta: %s>' % self.value
    >>>
    >>> data = {
    ...     'voices': 100500,
    ...     'items': [
    ...         {
    ...             'id': 1,
    ...             'name': 'User1',
    ...             'meta': Meta(123),
    ...         },
    ...         {
    ...             'id': 2,
    ...             'name': 'User2',
    ...             'meta': Meta(456),
    ...         },
    ...         'text item',
    ...         {
    ...             'name': 'Without id',
    ...         },
    ...     ]
    ... }
    >>> hasattr(path(data).items, '__iter__')
    True
    >>> list(path(data).voices)
    [100500]
    >>> list(path(data).items)
    [{'meta': <meta: 123>, 'id': 1, 'name': 'User1'}, {'meta': <meta: 456>, 'id': 2, 'name': 'User2'}, 'text item', {'name': 'Without id'}]
    >>> list(path(data).items.id)
    [1, 2]
    >>> list(path(data).items.meta['value'])
    [123, 456]
    >>> list(path(data).items.meta['dvalue'].a)
    [123, 456]
    >>> list(path(data).items[2:].name)
    ['Without id']
    >>> items = path(data).items
    >>> list(items.name)
    ['User1', 'User2', 'Without id']
    >>> list(items.id)
    [1, 2]
    >>> # так же должно работать со списком данных
    >>> list(path([data, data]).items.meta['dvalue'].a)
    [123, 456, 123, 456]
    >>> # и с обычными объектами тоже
    >>> list(path(Meta(123))['dvalue'].a)
    [123]
    >>> # и с генераторами
    >>> list(path(Meta(x) for x in xrange(10))['dvalue'].a)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    """
    if isinstance(data, list):
        return LazyList(data)
    if isinstance(data, dict):
        return LazyDict(data)
    if is_generator(data):
        return LazyMeta([path(item) for item in data])
    if data.__class__.__name__ == 'Meta':
        return LazyMeta(data)
    return data

if __name__ == '__main__':
    import doctest
    doctest.testmod()