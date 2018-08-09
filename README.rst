========
nbtester
========

Test Utility for Jupyter Notebook file.

Loader
======

Jupyter Notebook File (test.ipynb)::

     ...
     "cells": [
      {
       "cell_type": "code",
       "execution_count": null,
       "metadata": {
        "collapsed": true
       },
       "outputs": [],
       "source": ["num = 8"]
      }
     ],
     ...

.. code-block:: python

   import unittest
   from nbtester.loader import load_cells


   class Test(TestCase):
       def test_it(self):
          d = {}
          load_cells(d, "test.ipynb")
          self.assertEqual(d['num'], 8)


Supported Magic Commands
========================

* ``% run child.ipynb``
* ``%% ...``
