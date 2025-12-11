Release history and notes
=========================

.. External references

.. _fake.py: https://github.com/barseghyanartur/fake.py/

`Sequence based identifiers
<http://en.wikipedia.org/wiki/Software_versioning#Sequence-based_identifiers>`_
are used for versioning (schema follows below):

.. code-block:: text

    major.minor[.revision]

- It is always safe to upgrade within the same minor version (for example,
  from 0.3 to 0.3.4).
- Minor version changes might be backwards incompatible. Read the
  release notes carefully before upgrading (for example, when upgrading from
  0.3.4 to 0.4).
- All backwards incompatible changes are mentioned in this document.

0.2.3
-----
2025-12-11

- Support more input types.

0.2.2
-----
2025-12-03

- Minor fixes.

0.2.1
-----
2025-11-21

- Add new `fake.py`_ providers (`emails`, `free_emails`, `company_emails`).

0.2
---
2025-11-19

- Minor fixes and documentation improvements.

0.1
---
2025-11-19

.. note::

    Release is dedicated to my dear mother (Anna). Happy birthday!

- Initial beta release.
