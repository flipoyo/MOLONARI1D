# Notice on the frequential analysis tools.

This has been developped by the group "fréquentiel" in 2025. 

### Theory starting point.

You should already know that the physics behind Molonari is governed by the heat diffusion-advection equation :

$$\frac{\partial \theta}{\partial t} = \kappa_e \frac{\partial^2 \theta}{\partial z^2} + \underbrace{\frac{\rho_w c_w}{\rho_m c_m} K \frac{\partial H}{\partial z}}_{-v_t} \frac{\partial \theta}{\partial z}$$

Stallman showed that for an harmonic forcing of amplitude $\theta_\text{amp}$, offset $\theta_\mu$ and period $P$, an anlalytic answer is known :

$$
\theta(z,t) = \theta_\mu + \theta_{\text{amp}} e^{-az} \cos\!\left(\frac{2\pi}{P}t - bz\right)
$$

One can show that $a$ and $b$ are directly linked to $\kappa_e$ and $v_t$ :

$$
\begin{align*}
\dfrac{P\kappa_e}{2\pi} &= \dfrac{ a}{ b(b^2+a^2)} \\
\dfrac{v_t}{\kappa_e} &= \dfrac{b^2 - a^2}{a}
\end{align*}
$$

The aim is to deduce from temperature signals from the sensors the physical values of $\kappa_e$ and $v_t$.

> [!NOTE]
>
> Most of the work presented here is inspired by Munz paper published in 2016.



### Loading the library.

The functions and methods are coded in `frequency.py`. When using these tools, please import the library using :

```python
from frequency import frenquency_analysis
```

### How does it work ?

This framework is not made to generate signals but to extract informations from signals already generated. Consider the field case of Molonari. Using `SYNTHETIC_MOLONARI`, we generate different signals :

- A river temperature signal $T_\text{riv}(t)$.
- An hydraulic charge difference signal $\mathrm{d}H(t)$
- Three sensors temperature signals $T_{1}(t) = T(z=z_1, t), T_{2}(t)=T(z_2,t), T_3(t)=T(z_3,t)$ with $z_1 <z_2 <z_3$ the depths of the sensors.

Once all these signals are generated here is the mandatory pipeline :

1. Group all the signals into an array `signals` such that `signals[0, :]` = $T_\text{riv}(t)$ and `signals[i, :]` = $T_i(t)$.

2. Store the timesteps corresponding to the signals into an array `dates`. 
   **Make sure the timesteps are the same for the different signals.** The class is not ready to handle signals with different time resolutions.

3. Store the depths of the sensors in an array `depths`. Typically for the case of Molonari, it would be `[0, 0.1, 0.2, 0.3, 0.4]` with $0.4$ that does not correspond to a temperature sensor but to the **charge sensor**. Indeed we need to know where the $\mathrm{d}H$ is computed to get the gradient.

   However $0.4$ is just an information for the user and when dealing with the class we'll just consider : `depths = depths[:-1]` and get rid of the $0.4$ that does not correspond to a temperature signal.

### Functions.

First you need to initialize the module using :

```python
fa = frequency_analysis()
```

Then you need to set the required parameters to the class.

```python
fa.set_inputs(dates=dates, signals=signals, depths=depths[:-1])
```

Ici depths contenait le dernier point 0.4, d'où le `:-1`.

Si en plus vous disposez des paramètres physiques exacts de la simulation, vous pouvez les ajouter :

```python
POROSITE = Layer1.params[1]
LAMBDA_S = Layer1.params[2]
RHO_CS = Layer1.params[3]
K_INTRIN = 10**(-Layer1.params[0])
GRAD_H = - dH_offset / Zbottom  # gradient hydraulique

fa.set_phys_prop(lambda_s=LAMBDA_S,
                 rho_c_s=RHO_CS,
                 k=K_INTRIN,
                 n=POROSITE,
                 gradH=GRAD_H,
                 compute_now=True,
                 verbose=True)
```

Avec `compute_now` on renvoie directement les valeurs théoriques de `\kappa_e` et `v_t`.

##### Plotting the signals.

The first thing we encourage you to do is to plot the signals to see if there are no mistakes. You can do this with :

```python
fa.plot_signals()
```

##### Fast Fourier Transform of the temperature signals.

The second thing you can do is get the FFT of all the temperature signals on the same plot. We encourage you to do this everytime because it enables you to see what are the main spectral components (main frequencies). This is done with :

```python
fa.fft_sensors()
```

This will plot the amplitude spectrum of each of the given signals.

##### Automatic detection of the dominant peaks.

When you generate the river signal artifically, you already know what are the dominant frequencies in the signal (i.e the peaks in the FFT). However, as you process unknown signal from field experiments, you do not have this knowledge. Using `find_dominant_periods`, the script will return you the main peaks (main spectral components) using the FFT.

This is how you should call it :

```python
Pd, f0, A0, meta = fa.find_dominant_periods(store=True, compute_phases=True)
```

##### Estimating $a$ and $b$ parameters.

The key point is to retrieve the $a$ and $b$ parameters. Note that the values of these parameters will change according to each peak. Here is the pipeline, for each dominant peak :

- Extract the corresponding amplitude $A(P)$ for each signal (river, sensors). We end up with a list of : $\{A(z=0)=A_0, A(z=z_1), A(z=z_2), A(z=z_3)\}$.
- Extract the corresponding phase $\phi$ for each signal (river, sensors). We end up with a list of : $\{\phi(z=0)=\phi_0, \phi(z=z_1), \phi(z=z_2), \phi(z=z_3)\}$.
- Compute $\ln(A(z)/A_0)$ and fit the following law : $\ln(A(z)/A_0) = -az$.
- Compute $\phi(z) - \phi_0$ and fit the following law : $\phi(z) - \phi_0 = -bz$.

When the fitting is done for one peak of period $P$, we have the tuple $(a(P),b(P))$ and we can do this for all the peaks (and all the periods).

This is done like this :

```python
a_est, a_R2 = fa.estimate_a(allow2D=False, draw=True)
b_est, b_R2 = fa.estimate_b(draw=True)     
```

`allow2D` permet de lancer un sous-module qui détermine si on se trouve dans le cas 2D ou 1D.

##### Performing 1D inversion.

If the 1D model is valid for the input signals, one can go from $a$ and $b$ to $\kappa_e$ and $v_t$. 

> [!WARNING]
>
> However, it's not possible to go from $a$ and $b$ to $K$, $n$ and $\lambda_s$. This can be seen very easily : we have two equations for three parameters. Without an extra equations, we can't get to these three parameters. But $v_t$ and $\kappa_e$ already provide a good sense of the physics.

To perform the inversion, just launch :

```python
kappa_e, v_t = fa.perform_inversion(verbose=True) 
```

##### Recovering real parameters from a synthetic signal.

If you know what are the physical parameters of your input signals, you can check if you find the same $\kappa_e$ and $v_t$. We assume that you already know the physical parameters stored in `LAMBDA_S, RHO_CS, K_INTRIN, POROSITE, grad_H`.

Then you just need to call this function :

```python
kappa_e_phys, v_t_phys = fa.effective_params(LAMBDA_S, RHO_CS, K_INTRIN, POROSITE, grad_H)
```

Similarly, you can also recover the $a$ and $b$ values corresponding to the frequencies using :

```python
a_expected, b_expected = fa.phys_to_a_b()
```

