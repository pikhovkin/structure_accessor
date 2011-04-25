#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

class LazyData(object):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, index):
        if not isinstance(self.data, (int, float, str, unicode, list, dict)):
            return path(self.data.__dict__[index])
        if isinstance(self.data, list):
            if self.data:
                if isinstance(self.data[0], LazyData):
                    return path([item.data.__dict__[index] for item in self.data])
                if not isinstance(self.data[0], (int, float, str, unicode, list, dict)):
                    return path([item.__dict__[index] for item in self.data])

        return self.__dict__['data'][index]

    def __getattr__(self, attr):
        if isinstance(self.data, dict):
            value = self.__dict__['data'][attr]
            if isinstance(value, list):
                return path(value)

            if isinstance(value, (int, float, str, unicode)):
                return (value,)

        if isinstance(self.data, list):
            if self.data:
                if isinstance(self.data[0], list):
                    concat_list = []
                    [[concat_list.append(path(item)[attr]) for item in items
                        if isinstance(item, dict) and (attr in item)]
                            for items in self.data]
                    return path(concat_list)

                return path([path(item)[attr] for item in self.data
                    if isinstance(item, dict) and (attr in item)])

    def __getslice__(self, i, j):
        return path(self.data[max(0, i):max(0, j):])


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
    >>> def infinite():
    ...      counter = 0
    ...      while True:
    ...          yield Meta(counter)
    ...          counter += 1
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
    >>> # с бесконечной последовательностью
    >>> i = 0
    >>> for item in infinite():
    ...     list(path(item)['dvalue'].a)
    ...     i += 1
    ...     if 10 == i:
    ...         break
    [0]
    [1]
    [2]
    [3]
    [4]
    [5]
    [6]
    [7]
    [8]
    [9]
    """
    if inspect.isgenerator(data):
        return path([LazyData(item) for item in data])
    else:
        return LazyData(data)

if __name__ == '__main__':
    import doctest
    doctest.testmod()