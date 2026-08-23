# setup.py
import sys

from setuptools import Extension, setup
from Cython.Build import cythonize

if sys.platform == "win32":
    extra_compile_args = ["/O2", "/GL"]
    extra_link_args = ["/LTCG"]
else:
    extra_compile_args = ["-O3", "-march=native", "-mtune=native", "-flto"]
    extra_link_args = ["-flto"]

extensions = [
    Extension(
        "ai.evaluator",
        ["ai/evaluator.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
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
