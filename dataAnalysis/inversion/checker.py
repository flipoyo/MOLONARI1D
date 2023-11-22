"""
Module that implements a decorator allowing a method of user-defined class instance to become a "checker".
Also creates a new associated error type.
"""

from functools import wraps


class ComputationOrderException(Exception):
    """Exception raised when a method with a needed tag is computed before the linked checker."""


def checker(checked_meth):
    """
    Transform a bound method of user-defined class instance to a "checker" method.
    Each method decorated with the .needed would raise a ComputationOrderException.
    It is also possible to reset the checker with .reset.

    Args:
        checked_meth (method): a bound method of user-defined class instance

    Returns:
            method: checker method
    """

    def reset():
        return None

    def needed(meth):
        @wraps(meth)
        def new_meth(self, *args, **kargs):
            if hasattr(self, chkd_name) and getattr(self, chkd_name):
                return meth(self, *args, **kargs)
            raise ComputationOrderException(
                f"{checked_meth.__name__} has to be computed before calling {meth.__name__}."
            )

        return new_meth

    @wraps(checked_meth)
    def wrapper(self, *args, **kwargs):
        nonlocal wrapper

        @wraps(checked_meth)
        def new_wrapper(*args, **kwargs):
            setattr(self, chkd_name, True)
            return checked_meth(self, *args, **kwargs)

        def reset():
            setattr(self, chkd_name, False)

        new_wrapper.needed = needed
        new_wrapper.reset = reset
        setattr(self, checked_meth.__name__, new_wrapper)
        return new_wrapper(*args, **kwargs)

    chkd_name = "__" + checked_meth.__name__
    wrapper.needed = needed
    wrapper.reset = reset
    return wrapper
