import django
from django.conf import settings


def pytest_configure():
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            },
        },
        ROOT_URLCONF='tests.urls',
        INSTALLED_APPS=(
            'tests',
        ),
    )

    django.setup()
