from fallback_property import FallbackDescriptor, fallback_property


class Product:
    def __init__(self, price: float, units: int) -> None:
        self.price = price
        self.units = units

    def _total(self):
        return self.units * self.price

    @fallback_property()
    def total(self):
        return self._total()

    @fallback_property(cached=False)
    def total_without_caching(self):
        return self._total()

    @fallback_property(logging=True)
    def total_with_logging(self):
        return self._total()


def test_fallback_property__get(mocker):
    mocker.spy(FallbackDescriptor, '__get__')
    mocker.spy(Product, '_total')
    product = Product(1.5, 3)

    assert product.total == 4.5
    assert FallbackDescriptor.__get__.call_count == 1
    assert product._total.call_count == 1


def test_fallback_property__set(mocker):
    mocker.spy(FallbackDescriptor, '__get__')
    mocker.spy(FallbackDescriptor, '__set__')
    mocker.spy(Product, '_total')

    product = Product(1.5, 3)
    product.total = 2
    assert FallbackDescriptor.__set__.call_count == 1

    assert product.total == 2
    assert product._total.call_count == 0
    assert FallbackDescriptor.__get__.call_count == 1


def test_fallback_property__delete(mocker):
    mocker.spy(FallbackDescriptor, '__get__')
    mocker.spy(FallbackDescriptor, '__delete__')

    product = Product(1.5, 3)
    # delete should not fail if no value is available
    del product.total
    assert FallbackDescriptor.__delete__.call_count == 1

    product.total = 2
    assert product.total == 2
    assert FallbackDescriptor.__get__.call_count == 1

    del product.total
    assert FallbackDescriptor.__delete__.call_count == 2

    assert product.total == 4.5
    assert FallbackDescriptor.__get__.call_count == 2


def test_fallback_property__with_cache(mocker):
    mocker.spy(FallbackDescriptor, '__get__')
    mocker.spy(Product, '_total')
    product = Product(1.5, 3)

    product.total
    assert FallbackDescriptor.__get__.call_count == 1
    assert product._total.call_count == 1

    product.total
    assert FallbackDescriptor.__get__.call_count == 2
    assert product._total.call_count == 1


def test_fallback_property__without_cache(mocker):
    mocker.spy(FallbackDescriptor, '__get__')
    mocker.spy(Product, '_total')
    product = Product(1.5, 3)

    product.total_without_caching
    assert FallbackDescriptor.__get__.call_count == 1
    assert product._total.call_count == 1

    product.total_without_caching
    assert FallbackDescriptor.__get__.call_count == 2
    assert product._total.call_count == 2


def test_fallback_property__logging(caplog):
    product = Product(1.5, 3)

    product.total
    assert caplog.text == ''

    product.total_with_logging
    assert 'without prefetched value.' in caplog.text
    assert 'Product.total_with_logging' in caplog.text


def test_use_like_property():
    """
    Use as a function should be possible.
    """
    class Foo:
        @fallback_property
        def bar(self):
            """
            Test.
            """
            return 1

    assert Foo().bar == 1


def test_use_as_function():
    """
    Use as a function should be possible.
    """
    class Foo:
        def _bar(self):
            """
            Test.
            """
            return 1
        bar = fallback_property(_bar, logging=False)

    assert Foo().bar == 1
