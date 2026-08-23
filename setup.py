from setuptools import setup
from Cython.Build import cythonize

COMMON_FLAGS = ["-O3", "-march=native", "-mtune=native", "-flto", "-DNDEBUG"]

setup(
    name="RedWar AI Evaluator C++",
    ext_modules=cythonize(
        "ai/evaluator.pyx",
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
        annotate=False,
    ),
    extra_compile_args=COMMON_FLAGS,
    extra_link_args=["-flto"],
)
