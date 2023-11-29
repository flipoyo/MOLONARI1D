# Bug Report for MOLONARI Edition 2023

To be fixed asap by the 2023 Team

## Major bug in pyheatmy

Multi-layer doesn't work in direct modelling

When launching a stratified computation, a Figure appears for the visualisation of an initial state, which shouldn't, and then MolonaviZ freezes (no computation done, while it works in a monolayer configuration)

When trying to launch a new simulation, the message "Please wait while for the previous computation to end" always appears in the dialog box


## MolonaviZ

Compute window --> permeability value stated in m/s while it is set up at 1e-12 by default, which is an intrinsec permeability value. Do you confirm that it is intrinsec permeability, if yes the unit need to be changed in m2

Temperature window
The comparison of simulated temperatures with observed temperatures has not been merged (check Etienne Debricon branch please)


Major bug for next team concerns the fact that once a MCMC inversion has been lauch, MCMC is always launched whatever the user request, which is calculated after a MCMC calculation. For instance, if i ask for a direct simulation after a MCMC, the programm will repeat the MCMC and then perform the direct simulation and update the figures in accordance with the direct calculation only (pdfd disappear in the distribution window) 

