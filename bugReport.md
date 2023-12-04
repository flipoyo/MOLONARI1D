# Bug Report for MOLONARI Edition 2023

bugs remain, mostly in MolonaviZ

To be fixed asap by the 2023 Team


## MolonaviZ

Not all the advances of the MolonaviZ team are merged in the main branch:


1. Temperature window : The comparison of simulated temperatures with observed temperatures has not been merged (check Etienne Debricon branch please)

2. The compute window doesn't display properly the last values of parameters :
    - After a mono-layer forward model, only the default parameter values are displayed in the compute window
    - After a multi-layer forrward model permeability is not displayed properly. Using 4 layers, the two intermediate ones display None for the parameter values
    - There is nowhere to view the best MCMC results (parameters that correspond to quantile 0). I am surprise because the MolonaviZ team showed me this facility once.
    - After a mono-layer MCMC, only the default parameter values are displayed in the compute window
    - After a multi-layer MCMC, same issue than for a multi-layer forward model

3. Compute window --> permeability value stated in m/s while it is set up at 1e-12 by default, which is an intrinsec permeability value. Do you confirm that it is intrinsec permeability, if yes the unit need to be changed in m2. There is then a pb in the Fluxes windows. The value of the advective fluxes is always very low as well as the water flow. I think the intrinsec permeability, k [m2], is used directly in the flux calculation, rather than the permeability K [m/s]. --> __To be Done jointly with pyheatmy team__

4. Data arrays and plots: The display of the Temperatures is upside down. Sensor 0 displays Temp1, .... 3 Temp4 and sensor 4 displays RiverBed. Riverbed must be sensor 0 and then sensotr i is temp i


Major bug for next team (ie 2024) concerns the fact that once a MCMC inversion has been lauch, MCMC is always launched whatever the user request, which is calculated after a MCMC calculation. For instance, if i ask for a direct simulation after a MCMC, the programm will repeat the MCMC and then perform the direct simulation and update the figures in accordance with the direct calculation only (pdfd disappear in the distribution window) 

## pyheatmy 

Last bug to check is the unit of permeability which should be intrinsec permeability in [m2] in compute windows, and then check calculation of advective and conductive fluxes in Fluxes window, which units are for now wrong

Multi-layer works in both forward modelling and multi-chain MCMC --> bravo


