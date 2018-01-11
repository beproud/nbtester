import os
import re
import warnings

import nbformat


MAGIC_COMMAND_RE = re.compile(r'^\%\s*(?P<command>\w+)[ ]*(?P<args>.*)$', re.M)


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
    def repl(m):
        command, args = m.groups()
        if command != 'run':
            return ''
        fnam = os.path.join(os.path.dirname(nb_path), args)
        return 'load_cells(locals(), "%s")' % fnam
    
    for cell in code_cells:
        source = cell['source']

        # Parsing Magic Commands
        source = MAGIC_COMMAND_RE.sub(repl, source)
        try:
            g = globals()
            g.update(variables)

            exec(source, g, variables)
        except Exception as err:
            raise AssertionError("""

{errtype}: {err}

Code
=======================================
{code}
=======================================
""".format(errtype=type(err), err=err, code=cell['source']))
