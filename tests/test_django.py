import pytest
from django.contrib.admin.utils import label_for_field

from fallback_property import FallbackDescriptor, fallback_property

from . import models

LENGTH_SEGMENT1 = 100
LENGTH_SEGMENT2 = 300
TOTAL_LENGTH = LENGTH_SEGMENT1 + LENGTH_SEGMENT2


@pytest.fixture
def pipeline():
    pipe = models.Pipeline.objects.create()
    models.Segment.objects.create(pipeline=pipe, length=LENGTH_SEGMENT1)
    models.Segment.objects.create(pipeline=pipe, length=LENGTH_SEGMENT2)
    return pipe


@pytest.mark.django_db
def test_fallback_property(pipeline, django_assert_num_queries):
    pipeline = models.Pipeline.objects.get(pk=pipeline.pk)
    with django_assert_num_queries(1):
        assert pipeline.total_length == TOTAL_LENGTH

    pipeline = models.Pipeline.objects.with_total_length().get(pk=pipeline.pk)
    with django_assert_num_queries(0):
        assert pipeline.total_length == TOTAL_LENGTH


def test_admin_special_properties():
    """
    Copy special attribute to the decorator.

    The django `ModelAdmin` uses special attributes to alter the behaviour of a
    property/method displayed in the admin.
    """
    from django.db import models as django_models

    BOOLEAN = True
    EMPTY = 'empty'
    LABEL = "LABEL"
    ORDER_VALUE = 'foo_bar'

    class Foo(django_models.Model):
        def _bar(self):
            """
            Test.
            """
            return 1
        _bar.admin_order_value = ORDER_VALUE
        _bar.boolean = BOOLEAN
        _bar.empty_value_display = EMPTY
        _bar.short_description = LABEL
        bar = fallback_property(_bar, logging=False)

    descriptor = getattr(Foo, 'bar')
    assert isinstance(descriptor, FallbackDescriptor)

    assert descriptor.admin_order_value == ORDER_VALUE
    assert descriptor.boolean == BOOLEAN
    assert descriptor.empty_value_display == EMPTY
    assert descriptor.short_description == LABEL

    # Django should be able to extract the label
    assert label_for_field('bar', Foo) == LABEL
