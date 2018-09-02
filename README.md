[![Build Status](https://travis-ci.org/Apkawa/django-admin-view.svg?branch=master)](https://travis-ci.org/Apkawa/django-admin-view)
[![Coverage Status](https://coveralls.io/repos/github/Apkawa/django-admin-view/badge.svg)](https://coveralls.io/github/Apkawa/django-admin-view)
[![codecov](https://codecov.io/gh/Apkawa/django-admin-view/branch/master/graph/badge.svg)](https://codecov.io/gh/Apkawa/django-admin-view)
[![Requirements Status](https://requires.io/github/Apkawa/django-admin-view/requirements.svg?branch=master)](https://requires.io/github/Apkawa/django-admin-view/requirements/?branch=master)
[![PyUP](https://pyup.io/repos/github/Apkawa/django-admin-view/shield.svg)](https://pyup.io/repos/github/Apkawa/django-admin-view)
[![PyPI](https://img.shields.io/pypi/pyversions/django-admin-view.svg)]()

Project for merging different file types, as example easy thumbnail image and unpacking archive in one field

# Installation

```bash
pip install django-admin-view

```

or from git

```bash
pip install -e git+https://githib.com/Apkawa/django-admin-view.git#egg=django-admin-view
```

## Django and python version

* python-2.7 - django>=1.8,<=1.11
* python-3.4 - django>=1.8,<=1.11
* python-3.5 - django>=1.8,<=1.11
* python-3.6 - django>=1.11,<2.0


# Usage



# Contributing

## run example app

```bash
pip install -r requirements.txt
./test/manage.py migrate
./test/manage.py runserver
```

## run tests

```bash
pip install -r requirements.txt
pytest
tox
```

## publish pypi

```bash
python setup.py sdist upload -r pypi
```






