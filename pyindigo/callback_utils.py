from typing import Callable

from astropy.io.fits import HDUList


def error_printer(e: Exception):
    """Simples error handler for handles_errors decorator"""
    print(f'Exception occured during INDIGO callback: {e}')


def handles_errors(error_handler: Callable = error_printer) -> Callable:
    """Decorator factory to add error catching to INDIGO callbacks

    Because they are Python callables executed from C code, exceptions can't propagate
    from inside of them. This decorator allows to add error handler that accepts
    exception occured during callback. By default it uses error_printer that just
    prints error message

    Good idea is to use it as the most outer decorator, like this. Notice parenthesis, because
    it's a decorator FACTORY, not decorator itself

    >>> @handles_errors()
    >>> @any_other_pyindigo_decorator
    >>> ...
    >>> def my_custom_callback(str):
    >>>     process_string_from_INDIGO(str)
    """

    def decorator(callback: Callable) -> Callable:
        def decorated_calback(*args):
            try:
                callback(*args)
            except Exception as e:
                error_handler(e)
        return decorated_calback

    return decorator


prints_errors = handles_errors()


def accepts_hdu_list(callback: Callable) -> Callable:
    """Decorator to automatically convert bytes object passed from INDIGO
    to astropy's HDUList (representing inmemory FITS file

    Useful for take_shot calbacks to work with HDUList on user level"""
    def decorated_calback(b: bytes):
        callback(HDUList.fromstring(b))
    return decorated_calback
