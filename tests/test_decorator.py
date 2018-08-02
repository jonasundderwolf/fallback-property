from prefetched_property import PrefetchedDescriptor, prefetched_property


class Product:
    def __init__(self, price: float, units: int) -> None:
        self.price = price
        self.units = units

    def _total(self):
        return self.units * self.price

    @prefetched_property()
    def total(self):
        return self._total()

    @prefetched_property(cached=False)
    def total_without_caching(self):
        return self._total()

    @prefetched_property(logging=True)
    def total_with_logging(self):
        return self._total()


def test_prefetched_property__get(mocker):
    mocker.spy(PrefetchedDescriptor, '__get__')
    mocker.spy(Product, '_total')
    product = Product(1.5, 3)

    assert product.total == 4.5
    assert PrefetchedDescriptor.__get__.call_count == 1
    assert product._total.call_count == 1


def test_prefetched_property__set(mocker):
    mocker.spy(PrefetchedDescriptor, '__get__')
    mocker.spy(PrefetchedDescriptor, '__set__')
    mocker.spy(Product, '_total')

    product = Product(1.5, 3)
    product.total = 2
    assert PrefetchedDescriptor.__set__.call_count == 1

    assert product.total == 2
    assert product._total.call_count == 0
    assert PrefetchedDescriptor.__get__.call_count == 1


def test_prefetched_property__delete(mocker):
    mocker.spy(PrefetchedDescriptor, '__get__')
    mocker.spy(PrefetchedDescriptor, '__delete__')

    product = Product(1.5, 3)
    # delete should not fail if no value is available
    del product.total
    assert PrefetchedDescriptor.__delete__.call_count == 1

    product.total = 2
    assert product.total == 2
    assert PrefetchedDescriptor.__get__.call_count == 1

    del product.total
    assert PrefetchedDescriptor.__delete__.call_count == 2

    assert product.total == 4.5
    assert PrefetchedDescriptor.__get__.call_count == 2


def test_prefetched_property__with_cache(mocker):
    mocker.spy(PrefetchedDescriptor, '__get__')
    mocker.spy(Product, '_total')
    product = Product(1.5, 3)

    product.total
    assert PrefetchedDescriptor.__get__.call_count == 1
    assert product._total.call_count == 1

    product.total
    assert PrefetchedDescriptor.__get__.call_count == 2
    assert product._total.call_count == 1


def test_prefetched_property__without_cache(mocker):
    mocker.spy(PrefetchedDescriptor, '__get__')
    mocker.spy(Product, '_total')
    product = Product(1.5, 3)

    product.total_without_caching
    assert PrefetchedDescriptor.__get__.call_count == 1
    assert product._total.call_count == 1

    product.total_without_caching
    assert PrefetchedDescriptor.__get__.call_count == 2
    assert product._total.call_count == 2


def test_prefetched_property__logging(caplog):
    product = Product(1.5, 3)

    product.total
    assert caplog.text == ''

    product.total_with_logging
    assert 'without prefetched value.' in caplog.text
    assert 'Product.total_with_logging' in caplog.text
