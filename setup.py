import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.rst")).read()

setup(
    name="nbtester",
    version="0.5.1",
    install_requires=["nbformat"],
    packages=["nbtester"],
    author="Hiroki KIYOHARA",
    author_email="hirokiky@gmail.com",
    description="Test utilities for Jupyter Notebook file",
    long_description=README,
)
