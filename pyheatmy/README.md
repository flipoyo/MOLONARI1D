# PyHeatMy

This version of `pyheatmy` is a development release. Some features are either not yet implemented or are incomplete. Bugs may also be present; please feel free to report any issues you encounter.

We do not guarantee the accuracy of the calculated results at this stage. However, the data format will remain consistent throughout the full implementation. Consider this code as a template that will be stabilized once the features produce reliable results.

`pyheatmy` is built around the monolithic `Column` class in `core.py`. It can be executed from this class. Calculation, data retrieval, and plotting are methods provided by the `Column` class.

## Installation :

```sh
pip install -r requirements.txt
pip install -e .
```

## Tutorial :

There is a jupyter notebook called ``demoPyheatmy.ipynb`` which can be used to check the installation and see how the package works. This notebook describe direct simulation, and inversion with a simple MCMC. The multiple chain inversion is described in `DREAM_VX.ipynb`.

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

Project manager : Nicolas Flipo
 