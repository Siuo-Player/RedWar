# setup.py
import sys

from setuptools import setup
from Cython.Build import cythonize

if sys.platform == "win32":
    extra_compile_args = ["/O2"]
else:
    extra_compile_args = ["-O3", "-march=native", "-mtune=native"]

setup(
    name="RedWar AI Evaluator C++",
    ext_modules=cythonize(
        "ai/evaluator.pyx",
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "initializedcheck": False,
            "cdivision": True,
        },
    ),
    extra_compile_args=extra_compile_args,
)
