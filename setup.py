# setup.py
import sys

from setuptools import Extension, setup
from Cython.Build import cythonize

if sys.platform == "win32":
    extra_compile_args = ["/O2"]
else:
    extra_compile_args = ["-O3", "-march=native", "-mtune=native"]

extensions = [
    Extension(
        "ai.evaluator",
        ["ai/evaluator.pyx"],
        extra_compile_args=extra_compile_args,
    )
]

setup(
    name="RedWar AI Evaluator C++",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "initializedcheck": False,
            "cdivision": True,
        },
    ),
)
