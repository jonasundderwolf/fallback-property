import logging
from typing import Type, TypeVar, Generic, Callable

logger = logging.getLogger(__name__)

Class = TypeVar('Class')
Value = TypeVar('Value')
Method = Callable[[Class], Value]


class PrefetchedDescriptor(Generic[Class, Value]):
    def __init__(self, func: Method, cached: bool = True, logging: bool = False) -> None:
        """
        Initialize the descriptor.

        Arguments
        ---------
        func
            Fallback function if no value exists.
        cached
            Cache the value calculated by `func`.
        logging
            Log a warning if fallback function is used.
        """
        self.__doc__ = getattr(func, "__doc__")  # keep the docs
        self.func = func
        self.cached = cached
        self.logging = logging
        self.prop_name = f'__{self.func.__name__}'

    def __get__(self, obj: Class, cls: Type[Class]) -> Value:
        """
        Get the value.

        Return either the cached value or call the underlying function and
        optionally cache its result.
        """
        if not hasattr(obj, self.prop_name):
            if self.logging:
                logger.warning(
                    'Using `%s` without prefetched value.',
                    self.func,
                )

            value: Value = self.func(obj)
            if self.cached:
                self.__set__(obj, value)
            else:
                return value

        return getattr(obj, self.prop_name)

    def __set__(self, obj: Class, value: Value) -> None:
        """
        Store value in a private property.
        """
        setattr(obj, self.prop_name, value)

    def __delete__(self, obj: Class) -> None:
        """
        Clear current value from private property.
        """
        if hasattr(obj, self.prop_name):
            delattr(obj, self.prop_name)


def prefetched_property(
    cached: bool = True,
    logging: bool = False,
) -> Callable[[Method], PrefetchedDescriptor]:
    """
    Decorate a class method to return a precalculated value instead.

    This might be useful if you have a function that aggregates values from
    related objects, which could already be fetched using an annotated queryset.
    The decorated methods will favor the precalculated value over calling the
    actual method.

    NOTE: The annotated value must have the same name as the decorated function!
    """

    def inner(func: Method) -> PrefetchedDescriptor:
        return PrefetchedDescriptor(func, cached=cached, logging=logging)
    return inner
