import pytest

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
