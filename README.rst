===================
fallback-property
===================

.. image:: https://img.shields.io/pypi/v/fallback-property.svg
    :target: https://pypi.python.org/pypi/fallback-property

.. image:: https://travis-ci.org/jonasundderwolf/fallback-property.png?branch=master
    :target: http://travis-ci.org/jonasundderwolf/fallback-property
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/jonasundderwolf/fallback-property/badge.svg?branch=master
   :target: https://coveralls.io/github/jonasundderwolf/fallback-property?branch=master

.. image:: https://img.shields.io/pypi/pyversions/fallback-property.svg
    :target: https://pypi.python.org/pypi/fallback-property


Requirements
============

- Python 3.6+


What is it?
===========

``fallback_property`` transforms a function into a property and uses the
decorated function as fallback if no value was assigned to the property itself.
A special descriptor (``fallback_property.FallbackDescriptor``)
is used internally.


Django (or similar frameworks)
------------------------------

``fallback_property`` is useful if you have a function that aggregates
values from related objects, which could already be fetched using an annotated
queryset.
The decorator will favor the precalculated value over calling the actual method.

It is especially helpful, if you optimize your application and want to
replace legacy or performance critical properties with precalulated values
using ``.annotate()``.


How to use it?
==============

Simply define a function and use the decorator ``fallback_property`` ::

    from fallback_property import fallback_property

    class Foo:

        @fallback_property()
        def fallback_func(self):
            return 7


Arguments
---------

The ``fallback_property()`` has two optional arguments.

``cached: bool = True``
    If the property is accessed multiple times, call the fallback function only once.

``logging: bool = False``
    Log a warning if there was a fallback to the decorated, original method.


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
optimized by using ``.annotate()`` and ``fallback_property()`` ::

    from django.db import models, QuerySet
    from django.db.functions import Coalesce
    from django.db.models import Sum
    from fallback_property import fallback_property


    class PipelineQuerySet(QuerySet):

        def with_total_length(self):
            return self.annotate(
                total_length=Coalesce(
                    Sum('parts__length', output_field=models.IntegerField()),
                    0,
                )
            )


    class Pipeline(model.Model):

        @fallback_property(logging=True)
        def total_length(self):
            return sum(self.parts.values_list('length', flat=True))


You can now access the ``total_length`` without triggering another query or
get a warning, when the fallback function is used ::

    pipeline = Pipeline.objects.with_total_length().first()
    print(pipeline.total_length)


**Important: The annotated value and the property must have the same name.**


Related objects
---------------

When dealing with related objects in Django be aware that the ORM imposes certain limitations:

In the following example one might expect to get an instance of ``User``, but instead the
value of the primary key is returned::

    from django.db import models, QuerySet
    from django.db.functions import Coalesce
    from django.db.models import F
    from fallback_property import fallback_property


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

        @fallback_property()
        def owner(self):
            return self._owner or self.pipline.owner


    >>> print(Part.objects.with_owner().first().owner)
    >>> 1


Development
===========

This project is using `poetry <https://poetry.eustace.io/>`_ to manage all
dev dependencies.

Clone this repository and run ::

   poetry develop
   poetry run pip install django

to create a virtual environment with all dependencies.

You can now run the test suite using ::

  poetry run pytest


This repository follows the `angular commit conventions <https://github.com/marionebl/commitlint/tree/master/@commitlint/config-angular>`_.
You can register a pre-commit hook to validate your commit messages by using
`husky <https://github.com/typicode/husky>`_. The configurations are already in place if
you have nodejs installed. Just run ::

   npm install


and the pre-commit hook will be registered.
