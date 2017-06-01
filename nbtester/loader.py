import nbformat


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
    for cell in code_cells:
        try:
            exec(cell['source'], globals(), variables)
        except Exception as err:
            raise AssertionError("""

{errtype}: {err}

Code
=======================================
{code}
=======================================
""".format(errtype=type(err), err=err, code=cell['source']))
