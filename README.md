[![PyPi](https://img.shields.io/pypi/v/django-admin-view.svg)](https://pypi.python.org/pypi/django-admin-view)
[![Build Status](https://travis-ci.org/Apkawa/django-admin-view.svg?branch=master)](https://travis-ci.org/Apkawa/django-admin-view)
[![codecov](https://codecov.io/gh/Apkawa/django-admin-view/branch/master/graph/badge.svg)](https://codecov.io/gh/Apkawa/django-admin-view)
[![Requirements Status](https://requires.io/github/Apkawa/django-admin-view/requirements.svg?branch=master)](https://requires.io/github/Apkawa/django-admin-view/requirements/?branch=master)
[![PyUP](https://pyup.io/repos/github/Apkawa/django-admin-view/shield.svg)](https://pyup.io/repos/github/Apkawa/django-admin-view)
[![PyPI](https://img.shields.io/pypi/pyversions/django-admin-view.svg)](https://pypi.python.org/pypi/django-admin-view)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)


# Installation

```bash
pip install django-admin-view

```

or from git

```bash
pip install -e git+https://githib.com/Apkawa/django-admin-view.git#egg=django-admin-view
```

## Django and python version


| Python<br/>Django | 3.5 | 3.6 | 3.7 | 3.8 |
|:-----------------:|-----|-----|-----|-----|
| 1.8               |  ✘  |  ✘  |  ✘  |  ✘  |
| 1.11              |  ✔  |  ✔  |  ✔  |  ✘  |
| 2.2               |  ✔  |  ✔  |  ✔  |  ✔  |
| 3.0               |  ✘  |  ✔  |  ✔  |  ✔  |

# Usage



# Contributing

## run example app

```bash
pip install -r requirements-dev.txt
./test/manage.py migrate
./test/manage.py runserver
```

## run tests

```bash
pip install -r requirements-dev.txt
pytest
tox
```

## Update version

```bash
python setup.py bumpversion
```

## publish pypi

```bash
python setup.py publish
```






