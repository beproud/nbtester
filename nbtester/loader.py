import os
import re
import warnings
import nbformat
import sys
import numpy as np
import matplotlib.pyplot as plt
_plt = plt
from unittest import mock
from itertools import dropwhile, takewhile


def run_cell(source, variables=None, nb_path=''):
    def repl(m):
        command, args = m.groups()
        if command != 'run':
            return ''
        fnam = os.path.join(os.path.dirname(nb_path), args)
        return 'load_cells(locals(), "%s")' % fnam

    if source.startswith('%%'):
        return
    # Parsing Magic Commands
    source = re.sub(r'^\%\s*(?P<command>\w+)[ ]*(?P<args>.*)$', repl, source, flags=re.M)
    source = re.sub(r'^!.*$', '', source, flags=re.M)
    try:
        lines = source.splitlines()
        ptn = r"(from\s+\S+\s+|)import\s+\w+"
        n = len(list(takewhile(lambda x: not x or re.match(ptn, x), lines)))
        for pl in [lines[:n], lines[n:]]:
            g = globals()
            if variables:
                g.update(variables)
            exec("\n".join(pl), g, variables)

    except Exception as err:
        raise AssertionError("""

{errtype}: {err}

Code
=======================================
{code}
=======================================
""".format(errtype=type(err), err=err, code=source))


def load_cells(variables, nb_path, cell_indexes=None):
    """
    Jupyter Notebook:

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

    class Test(TestCase):
        def test_it(self):
            d = {}
            load_cells(d, "test.ipynb")
            self.assertEqual(d['num'], 8)
    """
    notebook = nbformat.read(nb_path, as_version=4)
    cells = notebook['cells']
    indexes = cell_indexes or range(len(cells))
    code_cells = [
        cell for i, cell in enumerate(cells)
        if cell['cell_type'] == 'code' and i in indexes
    ]

    # Ignore "can't resolve package from __spec__ or __package__,
    # falling back on __name__ and __path__" warning
    # in importlib/_bootstrap.py
    warnings.simplefilter(
        action="ignore",
        category=ImportWarning
    )

    for cell in code_cells:
        run_cell(cell['source'], variables, nb_path)


class MyMagicMock(mock.MagicMock):
    mocks = []
    in_matplotlib_test = False

    def __init__(self, add=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if add:
            MyMagicMock.mocks.append(self)


def _subplots(nrows=1, ncols=1, **kwargs):
    if MyMagicMock.mocks and MyMagicMock.mocks[0]._mock_name == 'plt':
        args = list(reversed(list(dropwhile(lambda x: x == 1, (ncols, nrows)))))  # npqa
        MyMagicMock.mocks[0].mock_calls.append(mock.call.subplots(*args, **kwargs))
    fig = MyMagicMock(name='fig', add=True)
    if nrows == 1 and ncols == 1:
        return fig, MyMagicMock(name='ax', add=True)
    if nrows == 1 or ncols == 1:
        return fig, [MyMagicMock(name=f'axes[{i}]', add=True) for i in range(nrows * ncols)]
    i1, i2 = np.indices((nrows, ncols))
    return fig, [
        MyMagicMock(name=f'axes[{i}, {j}]', add=True) for i, j in zip(i1.flat, i2.flat)
    ]


def get_args(*args, **kwargs):
    return args, kwargs


def call_test(pr, c, na, ar, kw):
    # actual: (name, args, kwargs)
    # expected: (na, ar, kw)
    name, args, d = c
    kwargs = kw.copy()
    kwargs.update(d)
    n = len(args) - len(ar)
    if n < 0:
        return False
    if n > 0:
        kwargs.update(dict(zip(kw.keys(), args[-n:])))
        args = args[:-n]
    for ky in kwargs.keys() - kw.keys():
        kwargs.pop(ky)
    return f'{pr}.{name}' == na and args == ar and kwargs == kw


def matplotlib_test(ipynb, expected=None):
    if MyMagicMock.in_matplotlib_test:
        return False
    MyMagicMock.mocks = []
    with mock.patch('matplotlib.pyplot', name='plt') as p, \
            mock.patch('matplotlib.pyplot.subplots', _subplots):
        MyMagicMock.mocks.append(p)
        try:
            MyMagicMock.in_matplotlib_test = True
            d = {}
            if ipynb.endswith('.ipynb'):
                load_cells(d, ipynb)
            else:
                run_cell(ipynb, d)
        finally:
            MyMagicMock.in_matplotlib_test = False
    alst = [(m._mock_name, c) for m in MyMagicMock.mocks for c in m.mock_calls]
    if expected is None:
        for a in alst:
            print(f'{a[0]}{str(a[1])[4:]}')
        return False
    for e in expected.splitlines():
        m = re.match(r'([a-zA-Z_][a-zA-Z0-9_.\[\]]*)\(([^)]*)\)', e)
        if not m:
            print(f'Error: No function call ({e})', file=sys.stderr)
            return False
        na, ar, kw = m.group(1), *eval(f'get_args({m.group(2)})')
        for a in alst:
            if call_test(*a, na, ar, kw):
                break  # 期待するコマンドあり
        else:
            print(f'{e} が存在しません', file=sys.stderr)
            return False
    return True
