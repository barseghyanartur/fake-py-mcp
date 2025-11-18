===========
fake-py-mcp
===========
.. External references

.. _fake.py: https://github.com/barseghyanartur/fake.py

.. Internal references

.. _Read the Docs: http://fake-py-mcp.readthedocs.io/
.. _Contributor guidelines: https://fakepy.readthedocs.io/en/latest/contributor_guidelines.html
.. _llms.txt: https://fake-py-mcp.readthedocs.io/en/latest/llms.txt

This project exposes all `Faker` class methods from `fake.py`_ as MCP tools
using FastMCP 2.0.

.. image:: https://img.shields.io/pypi/v/fake-py-mcp.svg
   :target: https://pypi.python.org/pypi/fake-py-mcp
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/fake-py-mcp.svg
    :target: https://pypi.python.org/pypi/fake-py-mcp/
    :alt: Supported Python versions

.. image:: https://github.com/barseghyanartur/fake-py-mcp/actions/workflows/test.yml/badge.svg?branch=main
   :target: https://github.com/barseghyanartur/fake-py-mcp/actions
   :alt: Build Status

.. image:: https://readthedocs.org/projects/fake-py-mcp/badge/?version=latest
    :target: http://fake-py-mcp.readthedocs.io
    :alt: Documentation Status

.. image:: https://img.shields.io/badge/docs-llms.txt-blue
    :target: https://fake-py-mcp.readthedocs.io/en/latest/llms.txt
    :alt: llms.txt - documentation for LLMs

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/barseghyanartur/fake-py-mcp/#License
   :alt: MIT

.. image:: https://coveralls.io/repos/github/barseghyanartur/fake-py-mcp/badge.svg?branch=main&service=github
    :target: https://coveralls.io/github/barseghyanartur/fake-py-mcp?branch=main
    :alt: Coverage

Features
========

- 80+ `fake.py`_ fake data methods (names, text, internet, files,
  primitives, dates, geo, books, banking, file content), dynamically
  registered (no manual boilerplate), categorised and documented.
- Binary outputs (e.g., images, PDFs) are returned as base64-encoded strings.
- ``server_info`` tool for introspection.

Prerequisites
=============
Python 3.9+

Installation
============

   .. code-block:: sh

      pip install fake-py-mcp

Usage
=====
Run the server
--------------

STDIO
~~~~~

   .. code-block:: sh

      fake-py-mcp

HTTP
~~~~

   .. code-block:: sh

      fake-py-mcp http

SSE
~~~

   .. code-block:: sh

      fake-py-mcp http

Connect with any MCP client to access all fake.py tools
-------------------------------------------------------
Developers need good tools. Unfortunately, FastMCP does not come with a
GUI (like OpenAPI/Swagger), but there are good tools available.

Option 1: MCP Inspector
~~~~~~~~~~~~~~~~~~~~~~~
**Installation**

.. code-block:: sh

   brew install mcp-inspector

**Usage**

.. code-block:: sh

   mcp-inspector ~/.venv/bin/python ~/fakepy_mcp.py

Option 2: mcpo
~~~~~~~~~~~~~~
**Installation**

.. code-block:: sh

   uv tool install mcpo

**Usage**

.. code-block:: sh

   mcpo --config ./mcp-config.json --port 8006

Open http://127.0.0.1:8006/docs and enjoy OpenAPI Swagger comfort.

Documentation
=============
- Documentation is available on `Read the Docs`_.

Tests
=====

Run the tests with unittest:

.. code-block:: sh

    python -m unittest fakepy_mcp.py

Or pytest:

.. code-block:: sh

    pytest

Writing documentation
=====================

Keep the following hierarchy.

.. code-block:: text

    =====
    title
    =====

    header
    ======

    sub-header
    ----------

    sub-sub-header
    ~~~~~~~~~~~~~~

    sub-sub-sub-header
    ^^^^^^^^^^^^^^^^^^

    sub-sub-sub-sub-header
    ++++++++++++++++++++++

    sub-sub-sub-sub-sub-header
    **************************

License
=======

MIT

Support
=======
For security issues contact me at the e-mail given in the `Author`_ section.

For overall issues, go to `GitHub <https://github.com/barseghyanartur/fake-py-mcp/issues>`_.

Author
======

Artur Barseghyan <artur.barseghyan@gmail.com>
