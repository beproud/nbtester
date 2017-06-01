import os
import unittest
from nbtester.loader import load_cells


here = os.path.dirname(__file__)


class TestLoadCells(unittest.TestCase):
    def test_it(self):
        d = {}
        load_cells(d, os.path.join(here, './define_variable.ipynb'))
        self.assertEqual(d, {'a': 'test', 'b': 'test2'})

    def test_specify_cells(self):
        d = {}
        load_cells(d, os.path.join(here, './define_variable.ipynb'), [0])
        self.assertEqual(d, {'a': 'test'})

    def test_syntax_error(self):
        d = {}
        with self.assertRaises(AssertionError):
            load_cells(d, os.path.join(here, './syntax_error.ipynb'))
