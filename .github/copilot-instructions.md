# MOLONARI1D Scientific Computing Ecosystem

MOLONARI1D is a Python ecosystem for monitoring local stream-aquifer water and heat exchanges. It consists of two main packages: **pyheatmy** (MCMC-based physical inference) and **Molonaviz** (PyQt5 GUI for device management).

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Required Python Version
- **pyheatmy**: Python 3.9+
- **Molonaviz**: Python 3.10+ (CRITICAL - will not work with earlier versions)
- Recommended: Python 3.12 (tested and working)

### Bootstrap and Install Both Packages

**CRITICAL**: This environment may experience network timeouts with PyPI. If pip installations fail with ReadTimeoutError, retry or use PYTHONPATH workarounds below.

1. Install test dependencies first:
   ```bash
   pip install pytest nbmake
   ```
   - Takes ~5 seconds. NEVER CANCEL.

2. Install pyheatmy:
   ```bash
   cd pyheatmy/
   pip install --timeout 300 -e .
   ```
   - Takes ~10 seconds normally. NEVER CANCEL. Set timeout to 300+ seconds.
   - **If this fails with network timeouts**: Use PYTHONPATH approach (see troubleshooting)

3. Install Molonaviz dependencies manually:
   ```bash
   pip install --timeout 300 pyqt5 pandas scipy matplotlib setuptools
   ```
   - Takes ~30-60 seconds for PyQt5. Set timeout to 300+ seconds. NEVER CANCEL.
   - **KNOWN ISSUE**: `pip install -e Molonaviz/` consistently fails due to network timeouts when fetching setuptools build dependencies
   - **Required Workaround**: Install dependencies manually, then use PYTHONPATH for development

### Running Tests
- **pyheatmy tests**: 
  ```bash
  cd pyheatmy/
  pytest tests/
  ```
  - Takes ~5 seconds. NEVER CANCEL.

- **Molonaviz tests**:
  ```bash
  cd Molonaviz/
  export PYTHONPATH="$PWD/src:$PYTHONPATH"
  pytest tests/
  ```
  - Takes ~1 second. NEVER CANCEL.

- **Both packages** (as in CI):
  ```bash
  pytest pyheatmy/ Molonaviz/
  ```
  - Takes ~5 seconds. NEVER CANCEL.

### Jupyter Notebook Testing
- **Core notebooks** (stable and working):
  ```bash
  cd pyheatmy/
  pytest --nbmake --nbmake-timeout=600 demoPyheatmy.ipynb demo_genData.ipynb
  ```
  - Takes ~85 seconds (1.5 minutes). NEVER CANCEL. Set timeout to 600+ seconds.

- **Note**: `demoPyheatmyMultilayer.ipynb` may fail with numerical instability (ValueError: NaN values) but runs for ~65 seconds before failing

### Validation Scenarios
**ALWAYS** run these validation steps after making changes:

1. **Test basic imports**:
   ```python
   import pyheatmy
   print("pyheatmy import successful")
   ```

2. **Test Molonaviz structure** (import will fail in headless mode but validates code structure):
   ```bash
   cd Molonaviz/src/
   export PYTHONPATH="$PWD:$PYTHONPATH"
   python -c "import molonaviz; print('Structure validation passed')"
   ```
   - Expected: ImportError about Qt5Agg backend in headless mode (this is normal)

3. **Run core functionality tests**:
   ```bash
   cd pyheatmy/
   pytest --nbmake --nbmake-timeout=600 demoPyheatmy.ipynb
   ```
   - Validates the complete MCMC inference pipeline

## Critical Installation Notes

### Molonaviz Installation Issues
- **KNOWN ISSUE**: `pip install -e Molonaviz/` frequently times out due to setuptools build dependency fetching
- **WORKAROUND**: Install dependencies manually first:
  ```bash
  pip install --timeout 300 pyqt5 pandas scipy matplotlib setuptools
  ```
- **FOR TESTING**: Use PYTHONPATH approach:
  ```bash
  export PYTHONPATH="/path/to/Molonaviz/src:$PYTHONPATH"
  ```

### GUI Limitations
- **Molonaviz cannot run in headless environments** (servers, CI, Docker without X11)
- Import will fail with: "Cannot load backend 'Qt5Agg' which requires the 'qt' interactive framework"
- This is expected behavior - tests validate code structure only

## CI/Workflow Integration

### GitHub Actions Workflow
- Tests both packages on ubuntu-latest, macos-latest, windows-latest
- Python versions: 3.9, 3.10, 3.11, 3.12
- Timeout settings for notebook tests: 600 seconds (10 minutes)

### Before Committing
- Run full test suite: `pytest pyheatmy/ Molonaviz/`
- Test core notebooks: `pytest --nbmake --nbmake-timeout=600 pyheatmy/demoPyheatmy.ipynb pyheatmy/demo_genData.ipynb`
- Check imports work correctly

## Common Development Tasks

### Working with pyheatmy
- **Main class**: `Column` in `pyheatmy/core.py`
- **Demo notebooks**: `demoPyheatmy.ipynb` (basic), `demo_genData.ipynb` (data generation)
- **Research folder**: Contains experimental features not yet in main package

### Working with Molonaviz
- **Entry point**: `src/molonaviz/main.py`
- **Structure**: Frontend (PyQt5) + Backend (SQL database)
- **Testing**: Unit tests only (no GUI functional tests possible in headless mode)

### Repository Structure
```
├── pyheatmy/          # MCMC inference package
│   ├── pyheatmy/      # Source code
│   ├── tests/         # Unit tests
│   ├── demo*.ipynb    # Demonstration notebooks
│   └── research/      # Experimental features
├── Molonaviz/         # GUI application
│   ├── src/molonaviz/ # Source code
│   └── tests/         # Unit tests
├── data/              # Sample datasets
├── dataAnalysis/      # Analysis notebooks and tools
└── Device/            # Hardware-related code and documentation
```

## Performance Expectations

### Timing Guidelines (with 50% safety buffer)
- Package installation (pyheatmy): 5 seconds
- Package installation (PyQt5 deps): 30 seconds  
- Unit tests (both packages): 5 seconds
- Core notebook execution: 85 seconds (1.5 minutes)
- Full notebook test suite: 150 seconds (2.5 minutes)

### Timeout Recommendations
- Installation commands: 300 seconds (5 minutes)
- Unit tests: 120 seconds (2 minutes)  
- Notebook tests: 600 seconds (10 minutes)
- NEVER CANCEL any command before timeout

## Troubleshooting

### Network Timeouts
- **Common Issue**: ReadTimeoutError from pypi.org during pip install
- **For pyheatmy installation failures**: Use PYTHONPATH workaround:
  ```bash
  export PYTHONPATH="/path/to/pyheatmy:$PYTHONPATH"
  ```
- **For Molonaviz installation failures**: Use PYTHONPATH workaround:
  ```bash
  export PYTHONPATH="/path/to/Molonaviz/src:$PYTHONPATH"
  ```
- **General timeout fix**: Always use `--timeout 300` with pip commands
- **Retry strategy**: If installation fails, retry 2-3 times before using PYTHONPATH workaround

### Import Errors
- Check Python version (3.10+ for Molonaviz)
- Verify PYTHONPATH for development installs
- Qt backend errors in headless mode are expected

### Numerical Issues
- Some research notebooks may have numerical instability
- Core notebooks (demoPyheatmy.ipynb, demo_genData.ipynb) are stable
- NaN errors in multilayer demos are known issues under investigation