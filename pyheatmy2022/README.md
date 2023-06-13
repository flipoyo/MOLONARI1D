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

There is a jupyter notebook called ``demo2022.ipynb`` which can be used to check the installation and see how the package works.

## Please note :

The notebooks are in the .gitignore file to avoid conflicts. 

The ``simu_exp_&_validation`` folder has three notebooks. Two of them are tutorials :
- ``demo_gen_test.ipynb`` for ``gen_test.py`` experimental observation simulator
- ``demo_val_direct.ipynb`` for ``val_analy.py`` analytical solution generator

``demo_cas_test.ipynb`` can generate multiple test cases and show the results.

To ensure consistent results, a checker is added where the user cannot call results if he has not executed the corresponding methods.

***

## License

MIT

2021 Mathis Bourdin & Youri Tchouboukoff
2022 Amélie Impéror, Antoine Poirier, Guillaume de Rochefort, Loris Megy, Paul Bonin Ciosi, Valentin Alleaume, Xinbei Jiang