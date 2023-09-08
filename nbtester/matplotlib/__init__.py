import re
import sys
from itertools import dropwhile
from unittest import mock

import matplotlib.pyplot as plt
import numpy as np

from ..loader import load_cells, run_cell

_plt = plt


class MyMagicMock(mock.MagicMock):
    mocks = []  # type: list[MyMagicMock]
    in_matplotlib_test = False

    def __init__(self, add=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if add:
            MyMagicMock.mocks.append(self)


def _subplots(nrows=1, ncols=1, **kwargs):
    if MyMagicMock.mocks and MyMagicMock.mocks[0]._mock_name == "plt":
        args = list(reversed(list(dropwhile(lambda x: x == 1, (ncols, nrows)))))  # noqa
        MyMagicMock.mocks[0].mock_calls.append(mock.call.subplots(*args, **kwargs))
    fig = MyMagicMock(name="fig", add=True)
    if nrows == 1 and ncols == 1:
        return fig, MyMagicMock(name="ax", add=True)
    if nrows == 1 or ncols == 1:
        return fig, [MyMagicMock(name=f"axes[{i}]", add=True) for i in range(nrows * ncols)]
    i1, i2 = np.indices((nrows, ncols))
    return fig, [MyMagicMock(name=f"axes[{i}, {j}]", add=True) for i, j in zip(i1.flat, i2.flat)]


def get_args(s):
    """name, args, kwargsを返す"""
    m = mock.MagicMock()
    try:
        eval("m." + s)
    except SyntaxError:
        return None, None, None
    p1 = None
    if len(m.mock_calls) >= 2:
        lst0 = list(m.mock_calls[0])
        r = re.match(r"([^.]+).__getitem__$", lst0[0])
        if r:
            p1 = rf"{r.group(1)}.__getitem__\(\)"
            p2 = f"{r.group(1)}[{lst0[1][0]}]"
    c = m.mock_calls[-1]
    res = list(c)
    if p1:
        res[0] = re.sub(p1, p2, res[0])
    return res


def call_test(pr, c, na, ar, kw):
    # actual: (name, args, kwargs)
    # expected: (na, ar, kw)
    name, args, kwargs = c
    n = len(args) - len(ar)
    if n < 0:
        return False
    if n > 0:
        kwargs.update(dict(zip(kw.keys(), args[-n:])))
        args = args[:-n]
    for ky in kwargs.keys() - kw.keys():
        kwargs.pop(ky)
    return f"{pr}.{name}" == na and args == ar and kwargs == kw


def dict2list(d):
    return [f"{k}={repr(v)}" for k, v in d.items()]


def call2str(name, args, kwargs):
    return f'{name}({", ".join(list(map(repr, args)) + dict2list(kwargs))})'


def conv_expected(s, conv_dict):
    esc = r"\*+.?{}()[]^$|/"
    p = "|".join(t.translate({ord(c): "\\" + c for c in esc}) for t in conv_dict)
    return re.sub(f"({p})", lambda m: conv_dict[m.group(0)], s)  # noqa


def matplotlib_test(ipynb, expected=None, conv_dict=None):
    if MyMagicMock.in_matplotlib_test:
        return False
    MyMagicMock.mocks = []
    with mock.patch("matplotlib.pyplot", name="plt") as p:
        p.subplots = _subplots
        MyMagicMock.mocks.append(p)
        try:
            MyMagicMock.in_matplotlib_test = True
            d = {}
            if ipynb.endswith(".ipynb"):
                load_cells(d, ipynb)
            else:
                run_cell(ipynb, d)
        finally:
            MyMagicMock.in_matplotlib_test = False
    a_lst = [(m._mock_name, c) for m in MyMagicMock.mocks for c in m.mock_calls]
    if expected is None:
        done = set()
        for a in a_lst:
            s = f"{a[0]}.{call2str(*a[1])}"
            if s not in done:
                print(s)
                done.add(s)
        return False
    for e in expected.splitlines():
        if e.startswith("#"):
            continue
        na, ar, kw = get_args(e)
        if conv_dict:
            e = conv_expected(e, conv_dict)
        if na is None:
            print(f"Error: No function call ({e})", file=sys.stderr)
            return False
        for a in a_lst:
            if call_test(*a, na, ar, kw):
                break  # 期待するコマンドあり
        else:
            print(f"{e} が存在しません", file=sys.stderr)
            return False
    return True
