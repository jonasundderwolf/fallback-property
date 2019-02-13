import functools
import logging
from typing import Type, TypeVar, Generic, Callable, Optional, Union

logger = logging.getLogger(__name__)

Class = TypeVar("Class")
Value = TypeVar("Value")
FuncType = Callable[[Class], Value]
Method = TypeVar('Method', bound=FuncType)

CUSTOM_WRAPPER_ASSIGNMENTS = (
    'admin_order_value',
    'allow_tags',
    'boolean',
    'empty_value_display',
    'short_description',
)
# TODO mypy sees `WRAPPER_ASSIGNMENT` as `Sequence[str]`, even if its actually defined as
#      `Tuple[str, ...]`. mypy raises an error, since combining a `Sequence` and a `Typle`
#      using `+` is invalid,
WRAPPER_ASSIGNMENTS = CUSTOM_WRAPPER_ASSIGNMENTS + functools.WRAPPER_ASSIGNMENTS  # type: ignore  # NOQA


class FallbackDescriptor(Generic[Class, Value]):
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
        # TODO mypy expects a `Callable` as first argument, even though it is not required
        functools.update_wrapper(self, func, assigned=WRAPPER_ASSIGNMENTS)  # type: ignore
        self.func = func
        self.cached = cached
        self.logging = logging
        self.prop_name = f"__{self.func.__name__}"

    def __get__(self, obj: Class, cls: Type[Class]) -> Value:
        """
        Get the value.

        Return either the cached value or call the underlying function and
        optionally cache its result.
        """
        # https://stackoverflow.com/a/21629855/7774036
        if obj is None:
            return self
        if not hasattr(obj, self.prop_name):
            if self.logging:
                logger.warning("Using `%s` without prefetched value.", self.func)

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


def fallback_property(
    method: Optional[Method] = None, cached: bool = True, logging: bool = False
) -> Union[Callable[[Method], FallbackDescriptor], FallbackDescriptor]:
    """
    Decorate a class method to return a precalculated value instead.

    This might be useful if you have a function that aggregates values from
    related objects, which could already be fetched using an annotated queryset.
    The decorated methods will favor the precalculated value over calling the
    actual method.

    NOTE: The annotated value must have the same name as the decorated function!
    """

    def decorator(func: Method) -> FallbackDescriptor:
        return FallbackDescriptor(func, cached=cached, logging=logging)

    # https://stackoverflow.com/a/4408489/7774036
    if method:
        # This was an actual decorator call, ex: @cached_property
        return decorator(method)
    # This is a factory call, ex: @cached_property()
    return decorator
