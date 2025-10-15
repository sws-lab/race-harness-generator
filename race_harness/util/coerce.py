import functools

def with_coercion_methods(cls):
    for name, attr in list(vars(cls).items()):
        if name.startswith('as_') and callable(attr):
            to_name = 'to_' + name[3:]
            if to_name in cls.__dict__:
                continue

            as_name = name

            def make_to(as_name=as_name):
                as_func = getattr(cls, as_name)

                @functools.wraps(as_func)
                def to(self, *args, **kwargs):
                    as_meth = getattr(self, as_name)  # resolve overridden methods
                    return self._coerce(as_meth(*args, **kwargs))

                try:
                    to.__annotations__ = dict(getattr(as_func, '__annotations__', {}))
                except Exception:
                    pass

                to.__name__ = 'to_' + as_name[3:]
                return to

            setattr(cls, to_name, make_to())

    return cls