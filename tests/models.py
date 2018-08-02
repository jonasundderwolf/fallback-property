from django.db import models

from prefetched_property import prefetched_property


class PipelineQuerySet(models.QuerySet):
    def with_total_length(self):
        return self.annotate(
            total_length=models.functions.Coalesce(
                models.Sum('segments__length', output_field=models.IntegerField()),
                0,
            ),
        )


class Pipeline(models.Model):

    objects = PipelineQuerySet.as_manager()

    class Meta:
        app_label = 'tests'

    @prefetched_property()
    def total_length(self):
        return sum(self.segments.values_list('length', flat=True))


class Segment(models.Model):
    pipeline = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='segments',
        to=Pipeline,
    )
    length = models.PositiveIntegerField()

    class Meta:
        app_label = 'tests'
