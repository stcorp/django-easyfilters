from setuptools import setup, find_packages
import sys

setup(
    name="django-easyfilters",
    version="0.7",
    url="https://github.com/stcorp/django-easyfilters",
    description="Easy creation of link-based filtering for a list of Django model objects.",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "django",
        "python-dateutil",
    ],
)
