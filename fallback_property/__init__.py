import functools
import logging
from typing import Callable, Generic, Optional, Type, TypeVar

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
    def __init__(
        self, func: Optional[Method] = None, cached: bool = True, logging: bool = False,
    ) -> None:
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


        `func` is not `None`, when the descriptor is used as a "function", eg.

            def _bar(...) -> ...:
                 ...
            bar = fallback_property(_bar)
        """
        self.cached = cached
        self.logging = logging

        if func is not None:
            self.__call__(func)

    def __call__(self, func: Method) -> 'fallback_property':
        """
        Apply decorator to specific method.

        Arguments
        ---------
        func
            Fallback function if no value exists.


        This method is either called from the constructor, when descriptor is used like

            def _bar(...) -> ...:
                ...
            bar = fallback_property(_bar)

        or directly after the descriptor has been created and the function will be wrapped

            # case 1
            @fallback_property
            def foo(self) -> ...:
                ...

            # case 2
            @fallback_property(...)
            def foo(self) -> ...:
                ...
        """
        # copy attribute from method to descriptor
        # TODO mypy expects a `Callable` as first argument, even though it is not required
        functools.update_wrapper(self, func, assigned=WRAPPER_ASSIGNMENTS)  # type: ignore

        # bind descriptor to method
        self.func = func
        self.prop_name = f"__{self.func.__name__}"

        return self

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


fallback_property = FallbackDescriptor
