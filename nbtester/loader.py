import os
import re
import warnings
from itertools import takewhile

import nbformat
from IPython import get_ipython


def run_cell(source, variables=None, nb_path="", ip=None, show_styler=False):
    def repl(m):
        command, args = m.groups()
        if command != "run":
            return ""
        filename = os.path.join(os.path.dirname(nb_path), args)
        return 'load_cells(locals(), "%s")' % filename

    if source.startswith("%%"):
        return
    if show_styler:
        from pandas.io.formats.style import Styler
    # Parsing Magic Commands
    source = re.sub(r"^\%\s*(?P<command>\w+)[ ]*(?P<args>.*)$", repl, source, flags=re.M)
    source = re.sub(r"^!.*$", "", source, flags=re.M)
    try:
        lines = source.splitlines()
        ptn = r"(from\s+\S+\s+|)import\s+[^(]+$"
        n = len(list(takewhile(lambda x: not x or re.match(ptn, x), lines)))
        for pl in [lines[:n], lines[n:]]:
            src = "\n".join(pl)
            if ip:
                res = ip.run_cell(src)
                err = res.error_before_exec or res.error_in_exec
                if err:
                    raise err
                if show_styler and isinstance(res.result, Styler):
                    print(res.result.to_html())
            else:
                g = globals()
                if variables:
                    g.update(variables)
                exec(src, g, variables)

    except Exception as err:
        raise AssertionError(
            """

{err_type}: {err}

Code
=======================================
{code}
=======================================
""".format(
                err_type=type(err), err=err, code=source
            )
        )


def load_cells(variables, nb_path, cell_indexes=None, use_ipython=False, show_styler=False):
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
    cells = notebook["cells"]
    indexes = cell_indexes or range(len(cells))
    code_cells = [
        cell for i, cell in enumerate(cells) if cell["cell_type"] == "code" and i in indexes
    ]

    # Ignore "can't resolve package from __spec__ or __package__,
    # falling back on __name__ and __path__" warning
    # in importlib/_bootstrap.py
    warnings.simplefilter(action="ignore", category=ImportWarning)

    ip = None if not use_ipython else get_ipython()
    for cell in code_cells:
        run_cell(cell["source"], variables, nb_path, ip=ip, show_styler=show_styler)
