.. Chyp documentation master file, created by
   sphinx-quickstart on Mon Oct 14 14:39:46 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Chyp's documentation!
================================

Chyp is an interactive theorem prover for string diagrams. For installation, usage, and basic configuration, see the README_ on GitHub.

Here is a small example chyp document:

.. code-block:: chyp

    # define some generators
    gen u : 0 -> 1 "ffdddd"
    gen m : 2 -> 1 "ddddff"

    # define some rules
    rule unitL : u * id ; m = id
    rule unitR : id * u ; m = id
    rule assoc : m * id ; m = id * m ; m

    # perform a rewrite-style proof
    rewrite random_monoid_eq :
      id * u * u * id ; m * m ; m
      = id * u * id ; id * m ; m by simp(unitL, unitR, assoc)




.. _README: https://github.com/akissinger/chyp#readme
.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
