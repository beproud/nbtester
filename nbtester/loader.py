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
        if cell['cell_type'] == 'code' and i in indexes and cell['execution_count']
    ]
    sorted_code_cells = sorted(code_cells, key=lambda x: x['execution_count'])
    for cell in sorted_code_cells:
        try:
            g = globals()
            g.update(variables)
            exec(cell['source'], g, variables)
        except Exception as err:
            raise AssertionError("""

{errtype}: {err}

Code
=======================================
{code}
=======================================
""".format(errtype=type(err), err=err, code=cell['source']))
