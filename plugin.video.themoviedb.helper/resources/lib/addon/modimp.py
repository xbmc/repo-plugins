from importlib import import_module


def importmodule(module_name, import_attr=None):
    module = import_module(module_name)
    if not import_attr:
        return module
    return getattr(module, import_attr)


def lazyimport(global_dict, module_name, import_as=None, import_attr=None):
    global_name = import_as or import_attr or module_name
    if not global_dict[global_name]:
        module = import_module(module_name)
        global_dict[global_name] = getattr(module, import_attr) if import_attr else module


def lazyimport_module(global_dict, module_name, import_as=None, import_attr=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            lazyimport(global_dict, module_name, import_as, import_attr)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def lazyimport_modules(global_dict, list_kwargs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in list_kwargs:
                lazyimport(global_dict, **i)
            return func(*args, **kwargs)
        return wrapper
    return decorator
