"""Useful decorators to simplify creating callbacks to be passed to INDIGO"""


from typing import Callable

from astropy.io.fits import HDUList


def handles_errors(error_handler: Callable) -> Callable:
    """Decorator factory to add error catching to INDIGO callbacks

    Because they are Python callables executed from C code, exceptions can't propagate
    from inside of them. This decorator allows to add error handler that accepts
    exception occured during callback.

    Good idea is to use it as the most outer decorator, like this. Notice parenthesis, because
    it's a decorator FACTORY, not decorator itself

    >>> @handles_errors()
    >>> @any_other_decorator
    >>> ...
    >>> def my_custom_callback(str):
    >>>     process_string_from_INDIGO(str)
    """

    def decorator(callback: Callable) -> Callable:
        def decorated_callback(*args):
            try:
                callback(*args)
            except Exception as e:
                error_handler(e)
        return decorated_callback

    return decorator


def error_printer(e: Exception):
    """Simple error handler for handles_errors decorator factory"""
    print(f'Exception occured in INDIGO callback: {e}')


prints_errors = handles_errors(error_handler=error_printer)


def accepts_hdu_list(callback: Callable) -> Callable:
    """Decorator to automatically tries to convert all bytes object passed to callback
    to astropy's HDULists representing inmemory FITS files

    Useful for take_shot calbacks to work with HDUList on user level"""
    def decorated_callback(*args):
        converted_args = []
        for arg in args:
            if isinstance(arg, bytes):
                try:
                    new_arg = HDUList.fromstring(arg)
                except Exception:
                    new_arg = arg
            else:
                new_arg = arg
            converted_args.append(new_arg)
        callback(*converted_args)
    return decorated_callback
