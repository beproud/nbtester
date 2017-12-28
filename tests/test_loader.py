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

    def test_closured_variable(self):
        d = {}
        load_cells(d, os.path.join(here, './closured.ipynb'))
        self.assertEqual(d['a'], "hello")
        self.assertEqual(d['b'], "hello")
        self.assertEqual(d['hello'](), "hello")

        self.assertEqual(d['a2'], "hello")
        self.assertEqual(d['b2'], "hello")
        self.assertEqual(d['hello2'](), "hello")

    def test_run_magic_command(self):
        d = {}
        load_cells(d, os.path.join(here, './run_1.ipynb'))
        self.assertEqual(d, {'parent': 'PARENT', 'child': 'CHILD'})
