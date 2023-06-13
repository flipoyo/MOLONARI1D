from setuptools import setup, find_namespace_packages

setup(name='molonaviz',
    version='1.0',
    description='Graphical tool for the MOLONARI project.',
    author='Guillaume Vigne',
    package_dir = {'' : 'src'},
    packages=find_namespace_packages('src'),
    zip_safe=False,
    install_requires = ['pyqt5', 'pandas', 'numpy', 'matplotlib', 'tqdm', 'scipy', 'numba'],
    entry_points = {'console_scripts':
                    ['molonaviz = molonaviz.main:main']},

    package_data = {'molonaviz.docs' : ["*.png", ".pdf", ".md"],
                    'molonaviz.imgs' : ["*.png, *.jpg*", "*.jpeg*"],
                    'molonaviz.frontend.ui' : ["*.ui"],
                    'molonaviz.interactions' : ["*.txt"]
                    },

    include_package_data = False)
