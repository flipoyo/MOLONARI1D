# PyHeatMy

This version of pyheatmy is a development version. Some features are not yet implemented or are incomplete.
Some bugs may also appear, do not hesitate if you have any problem.

We do not guarantee any reliability on the resulting values of the calculations, however the data format will remain constant during their full implementation. Think of this code as a template that will remain persistent when the features are reliable in their results.

## Installation :

```sh
pip install -r requirements.txt
pip install -e .
```

## Tutorial :

There is a jupyter notebook called ``demo2023.ipynb`` which can be used to check the installation and see how the package works.

## Please note :

The folder 'research' contains projects that are not yet implemented in the src files of pyheatmy

Among them, ``synthetic_cases_generator`` was issued in by the MOLONARI 2022 edition. It was implemented in pyheatmy in ``gen_test.py``, which contains the class ``Time_series``. The folder contaions three notebooks. Two of them are tutorials :
- ``demo_gen_test.ipynb`` for ``gen_test.py`` experimental observation simulator
- ``demo_val_direct.ipynb`` for ``val_analy.py`` analytical solution generator

``demo_cas_test.ipynb`` can generate multiple test cases and show the results.

All the other projects are from the MOLONARI 2023 edition.


## License
EPL v2.0

2021 Mathis Bourdin & Youri Tchouboukoff
2022 Amélie Impéror, Antoine Poirier, Guillaume de Rochefort, Loris Megy, Paul Bonin Ciosi, Valentin Alleaume, Xinbei Jiang
2023 Mattéo Leturcq-Daligaux, Nicolas Matte, Mathis Chevé, Zhan Jing, Dan Maurel
 