from setuptools import Extension, setup
from Cython.Build import cythonize

ext_modules = [
    Extension("MOLO_45",
              sources=["MOLO_45.pyx"],
              libraries=["m"]  # Unix-like specific
              )
]

setup(name="MOLO_setup",
      ext_modules=cythonize(ext_modules))

#After installing cython ...
#... to compile MOLO_45.pyx using linux ...
#... execute the command: python3 setup.py build_ext --inplace