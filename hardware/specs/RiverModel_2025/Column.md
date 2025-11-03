# Implementation of the working column

## 0. Introduction

In order to test out the different prototypes of sensors and algorithms in a controlled environment, we decided to build two physical models of rivers, for 1D and pseudo-2D testing.

The column model is reserved for 1D testing, and has its pros and cons :

- Pros :
        - easier to build than 2D model
        - requires simpler equipment than 2D model
        - accurate for 1D sensor calibration and testing

- Cons : 
        - requires to detach sensors from MOLONARI device in order to fit them on a thinner rod to avoid edge effects (linked to the small distance between the surface of the column and the surface of the regular MOLONARI device rod)
        - only 1D modelling

## 1. Design 

The model should work as follows : a pump induces vertical water flow throughout the porous material in the column, all the parameters should be known prior to testing. The sensors are planted inside the material at the distances required for testing (for temperature sensors, every 10cm, and for the differential pressure sensor, at the bottom and top of the porous material). 


### Equipment required : 

- plastic tube (Ø60mm approx.) with a cap on one side
- a pump
- plastic tubing to link the column to the pump
- a brass barbed fitting
- MOLONARI device
- a piece of fabric to act as a filter to not clog the pump at the bottom
- your porous material of choice (sand, beads, gravel...)

- tools to cut into plastic (small saw, cutter, a drill bit adapted to the size of your barbed fitting...)

### Construction instructions : 

- To keep things simple, we recycled a plastic ion exchanger tube (Ø60mm) with its plastic cap on one side. 

- We made a hole in the cap in order to fit a brass barbed fitting at the bottom of the column, which enables water flow through the porous material. 

- In order not to clog the pump with the porous material, we put a piece of fabric on top of the barbed fitting, at the bottom of the column to filter the water flow. We kept it in place using a small piece from a smaller plastic tube and the weight of the sand and marbles we use to model the porous material.

## 2. Calculating parameters of in-lab porous material

The aim of this section is to explain the method used in order to calculate the parameters 

- n (porosity of porous material)

- k (intrinsic permeability of porous material)

- c (massic thermal conductivity of porous material)


in our experimental testing column, to check whether the inversion model finds the right parameters after acquiring the data.

### Calculating porosity

When using a controlled porous material, such as silica glass beads, the technical sheet (or slightly more research, some experiments and a bit of density calculations) should allow you to find two important parameters of the media you're going to use :

- $\rho_{material}$ the density of the raw material (in $kg/m^3$ or equivalent unit)
- $\rho_{bulk}$ the density of the beads in bulk (in $kg/m^3$ or equivalent unit), which refers to the density of the system {beads+air} in a designated volume


With this information, we can deduce the porosity $n$ of one given material (in the case of beads, for any diameter, as neither the packing efficiency nor the porosity depend on the diameter of the beads) : 

$$\boldsymbol{n = 1 - \frac{\rho_{bulk}}{\rho_{material}}} $$


### Calculating permeability :

To simplify, we will consider here that all grains are spherical.

For a specific bead diameter :

#### a) Bead arrangement

Given the porosity $n$ (void ratio, hence $1-$Atomic packing factor), we can determine the equivalent combination of cubic arrangements (Primitive cubic, Body-centered cubic, Face-centered cubic), by taking the barycentric proportions of the two closest cubic arrangement void ratios : 

- fcc : 0.26

- bcc : 0.32

- cP : 0.48


E.g : If $n = 0.29$ for the porous material we chose, then we can say that the bead arrangement is half fcc, half bcc. If $n= 0.36$, we can say that the bead arrangement is 3/4 bcc and 1/4 cP, etc.


#### b) Equivalent tube radius

For each cristal arrangement, we can calculate an equivalent tube radius by the following general formula : 

$$V_{vertically-linked-interstices} = \pi R_{eq}^2 * a$$

where 

- $V_{vertically-linked-interstices}$ is quite eponym (however, remain mindful that the lattices are linked together and form two by two the actual volumes that water can flow through vertically, this means that for bcc for example, you need to take twice the volume of the vertically linked interstices in one lattice.) We calculate this volume as follows:

$$
 V_{vertically-linked-interstices} = \frac{V_{lattice} - V_{beads}}{N_{tubes/cell}} 
$$
r being the radius of the beads and $N_{tubes/cell}$ the number of vertically linked interstices in a unit cell ;

- $R_{eq}$ is the equivalent tube radius we are attempting to find

- $a$ is the size of the unit cell ($2r$ for cP)


#### c) Macroscopic model - Darcy :

The Darcy model gives the macroscopic flow rate as a function of the hydraulic head gradient, using porosity :
$$
Q_D = -K S \nabla h = -\frac{\rho g S k}{\mu L}\Delta h
$$
$\rho$ being the density of water, g the g-force, S the section of the column, L the height of the column and $\mu$ the dynamic viscosity;

#### d) Microscopic model - Hagen-Poiseuille :

The Hagen-Poiseuille equation gives the microscopic flow rate in each of the equivalent tubes of the cristal system:
$$
Q_P = -\frac{\pi R_{eq}^4 \rho g}{8 \mu L}\Delta h
$$
$R_{eq}$ being the equivalent radius calculated in section b), weighted regarding the equivalent combination of cubic arrangement and L the length of the equivalent tube, hence the length of the column.


#### e) Number of equivalent microscopic tubes per column section :

Given the number of unit cells on a column section ($\frac{S}{a_{w}}$, $a_w$ being the weighted lattice constant) and the average number of equivalent tubes per unit cell (1 for cP, 2 for bcc), we determine the number of equivalent tubes per column section $N_{tubes}$.

#### f) Conclusion :

We finally obtain the following equation that we can resolve for k: 
$$Q_D = N_{tubes}Q_P$$


$\boldsymbol{E.g.:}$ For the 7mm diameter glass beads, the arrangement of beads is 54\% cP and 46\% bcc. Thus, there is an average of 1.46 equivalent tubes per cell, the average cell size is $a_{app} = 54\% . 2r + 46\% . \frac{4}{\sqrt{3}}r$ and the equivalent tube radius is
$$
R_{eq} = 54\% \sqrt{\frac{1}{\pi}(4-\frac{2}{3}\pi)}r +46\% \sqrt{\frac{1}{\pi}\frac{8-\sqrt{3}\pi}{3}}r
$$
Solving for k, we obtain:
$$
\boldsymbol{ k=0.024r^2}
$$


