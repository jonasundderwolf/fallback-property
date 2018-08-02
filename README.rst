===================
prefetched-property
===================

.. image:: https://img.shields.io/pypi/v/prefetched-property.svg
    :target: https://pypi.python.org/pypi/prefetched-property

.. image:: https://travis-ci.org/jonasundderwolf/prefetched-property.png?branch=master
    :target: http://travis-ci.org/jonasundderwolf/prefetched-property
    :alt: Build Status

.. image:: https://coveralls.io/repos/jonasundderwolf/prefetched-property/badge.png?branch=master
    :target: https://coveralls.io/r/jonasundderwolf/prefetched-property
    :alt: Coverage

.. image:: https://img.shields.io/pypi/pyversions/prefetched-property.svg

.. image:: https://img.shields.io/pypi/status/prefetched-property.svg

.. image:: https://img.shields.io/pypi/l/prefetched-property.svg

A ``@property`` like decorator which uses a fallback function if no value was assigned.


Requirements
============

- Python 3.6


What is it?
===========

``prefetched_property`` transforms a function into a property and uses the
decorated function as fallback if no value was assigned to the property itself.
A special descriptor (``prefetched_property.PrefetchedDescriptor``)
is used internally.


Django (or similar frameworks)
------------------------------

``prefetched_property`` might be useful if you have a function that aggregates
values from related objects, which could already be fetched using an annotated
queryset.
The decorator will favor the precalculated value over calling the actual method.

It is especially helpful, if you optimize your application and want to
replace "legacy" or performance critical properties with precalulated values
using ``.annotate()``.


How to use it?
==============

Simply define a function and use the decorator ``prefetched_property`` ::

    from prefetched_property import prefetched_property

    class Foo:

        @prefetched_property()
        def fallback_func(self):
            return 7


Arguments
---------

The ``prefetched_property()`` has two optional arguments.

``cached: bool = True``
    If the property is accessed multiple times, call the fallback function only once.

``logging: bool = False``
    Log a warning if the fallback function had to be used.


Usage Example (Django)
======================

Suppose we have the following models ::

    from django.db import models


    class Pipeline(model.Model):
        @property
        def total_length(self):
            return sum(self.parts.values_list('length', flat=True))


    class Parts(models.Model):
        length = models.PositiveIntegerField()
        pipeline = models.ForeignKey(Pipeline, related_name='parts')


Calling ``pipline.total_length`` will always trigger another query and is
even more expensive when dealing with multiple objects. This can be
optimized by using ``.annotate()`` and ``prefetched_property()`` ::

    from django.db import models, QuerySet
    from django.db.functions import Coalesce
    from django.db.models import Sum
    from prefetched_property import prefetched_property


    class PipelineQuerySet(QuerySet):

        def with_total_length(self):
            return self.annotate(
                total_length=Coalesce(
                    Sum('parts__length', output_field=models.IntegerField()),
                    0,
                )
            )


    class Pipeline(model.Model):

        @prefetched_property(logging=True)
        def total_length(self):
            return sum(self.parts.values_list('length', flat=True))


You can now access the ``total_length`` without triggering another query or
get a warning, when the fallback function is used ::

    pipeline = Pipeline.objects.with_total_length().first()
    print(pipeline.total_length)


**Take note that the annotated value and the property must have the same name.**


What about related objects?
---------------------------

This does not work well if you want to prefetch related objects.
The following example is a bit far-fetched, since this could also be achieved
with a simple ``select_related()``.
But for sake of illustration we use it any way ::

    from django.db import models, QuerySet
    from django.db.functions import Coalesce
    from django.db.models import F
    from prefetched_property import prefetched_property


    class PartQuerySet(QuerySet):

        def with_owner(self):
            return self.annotate(
                owner=Coalesce(
                    F('_owner'),
                    F('pipeline__owner'),
                    None,
                )
            )


    class Pipeline(model.Model):
        owner = models.ForeignKey(User)


    class Parts(models.Model):
        _owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
        length = models.PositiveIntegerField()
        pipeline = models.ForeignKey(Pipeline, related_name='parts')

        objects = PartQuerySet()

        @prefetched_property()
        def owner(self):
            return self._owner or self.pipline.owner


    print(Part.objects.with_owner().first().owner)
    1


You might expect to get an instance of ``User``, but instead we just get the
value of the primary key.
This is due to limitations of the django orm.


Development
===========

This project is using `poetry <https://poetry.eustace.io/>`_ to manage all
dev dependencies.
Clone this repository and run ::

   poetry develop


to create a virtual enviroment with all dependencies.
You can now run the test suite using ::

  poetry run pytest


This repository follows the `angular commit conventions <https://github.com/marionebl/commitlint/tree/master/@commitlint/config-angular>`_.
You can register a pre-commit hook to validate your commit messages by using
`husky <https://github.com/typicode/husky>`_. The configurations are already in place if
you have nodejs installed. Just run ::

   npm install


and the pre-commit hook will be registered.
