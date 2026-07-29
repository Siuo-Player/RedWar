# setup.py
from setuptools import setup
from Cython.Build import cythonize

setup(
    name='RedWar AI Evaluator C++',
    # Atualizado para apontar exatamente para o ficheiro que tens na pasta ai/
    ext_modules=cythonize("ai/evaluator.pyx", compiler_directives={'language_level': "3"}),
)