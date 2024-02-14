import inspect


class ResolutionError(Exception):

    def __init__(self):
        self._stack = []
        self._last_path = None

    def add(self, cls, cls_settings,
            factory, factory_settings, factory_kwargs, parameter):
        rows = []
        if cls:
            rows.append(f'    cls={repr(cls)}')
        if cls_settings:
            rows.append(f'    cls_settings={repr(cls_settings)}')
        if factory:
            rows.append(f'    factory={repr(factory)}')
        if factory_settings:
            rows.append(f'    factory_settings={repr(factory_settings)}')
        if factory_kwargs:
            rows.append(f'    factory_kwargs={repr(factory_kwargs)}')
        if parameter:
            rows.append(f'    last_factory_kwarg={repr(parameter.name)}')

        rows = ",\n".join(rows)
        self._stack.append(f'<Resolve(\n{rows}\n)>')

    def __str__(self):
        return '\n'.join(list(reversed(self._stack)))
