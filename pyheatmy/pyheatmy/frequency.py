import numpy as np
import matplotlib.pyplot as plt
from pyheatmy import *
from datetime import datetime, timedelta
import os as os
import csv as csv 
from scipy.signal import butter, filtfilt, hilbert, find_peaks,peak_widths, get_window
from sklearn.metrics import r2_score
from scipy.stats import chi2

"""
Module for frequency domain analysis of temperature data.
The inputs will be the signals of the sensors, the depths of the sensors and the temperature of the river.
The aim is to retrieve values of diffusivity kappa_e and Stallman speed v_t.
"""

class frequency_analysis:
    def __init__(self, verbose=True):
        self._dates = None
        self._signals = None          # [river, s1, s2, ...] 
        self._depths = None           # [z_riv(=0), z1, z2, ...]
        self._periods_days = None
        self._amps_surface = None     # amplitudes FFT for z=0 for dominant periods
        self._phases = None           # phases FFT for z=0 (optional)
        self._theta_mu = 0.0          # mean offset
        self._kappa_e = None
        self._v_t = None

        if verbose:
            print("Frequency analysis module initialized.")
            print("This module will analyze a multi-periodic signal to estimate attenuation and phase decay coefficients.")
            print("Using phase decay and amplitude attenuation with depth, we'll retrieve kappa_e and v_t for each dominant period.")
            print("-------------------------------------")
            print("Please use set_inputs(...) to provide the necessary data before analysis.")

    def set_inputs(self, *,
                dates=None,
                signals=None,
                depths=None,
                periods_days=None,
                amps_surface=None,
                phases=None,
                theta_mu=None,
                kappa_e=None,
                v_t=None):
        
        if dates is not None:        self._dates = dates
        if signals is not None:      self._signals = signals
        if depths is not None:       self._depths = np.asarray(depths, float)
        if periods_days is not None: self._periods_days = np.asarray(periods_days, float)
        if amps_surface is not None: self._amps_surface = np.asarray(amps_surface, float)
        if phases is not None:       self._phases = np.asarray(phases, float)
        if theta_mu is not None:     self._theta_mu = float(theta_mu)
        if kappa_e is not None:      self._kappa_e = float(kappa_e)
        if v_t is not None:          self._v_t = float(v_t)
        return self 


    def effective_params(
        self,
        lambda_s,          # [W/m/K] conductivity of solid
        rho_c_s,           # [J/m³/K] volumetric heat capacity of solid
        k,                 # [m²] intrinsic permeability
        n,                 # [-] porosity
        gradH,             # [-] hydraulic head gradient (positive downward)
        # --- constants for water at 20°C
        lambda_w=0.6,      # [W/m/K]
        rho_w=1000.0,      # [kg/m³]
        c_w=4182.0,        # [J/kg/K]
        mu_w=1.002e-3,     # [Pa·s]
        g=9.81             # [m/s²]
        ):
        """
        Compute effective thermal diffusivity (kappa_e) and thermal advective velocity (v_t)
        from solid properties, porosity, intrinsic permeability and head gradient.

        Parameters
        ----------
        lambda_s : float
            Thermal conductivity of solid [W/m/K]
        rho_c_s : float
            Volumetric heat capacity of solid [J/m³/K]
        k : float
            Intrinsic permeability [m²]
        n : float
            Porosity [-]
        gradH : float
            Hydraulic head gradient (∂H/∂z) [-] (positive downward)

        Returns
        -------
        kappa_e : float
            Effective thermal diffusivity [m²/s]
        v_t : float
            Effective thermal advective velocity [m/s]
        """

        rho_c_w = rho_w * c_w  # [J/m³/K]
        rho_c_m = n * rho_c_w + (1 - n) * rho_c_s  # [J/m³/K]
        lambda_m = (n * np.sqrt(lambda_w) + (1 - n) * np.sqrt(lambda_s)) ** 2  # [W/m/K]

        kappa_e = lambda_m / rho_c_m  # [m²/s]

        # Convert intrinsic permeability to hydraulic conductivity
        K = k * rho_w * g / mu_w  # [m/s]

        v_t = - (rho_c_w / rho_c_m) * K * gradH  # [m/s]

        return kappa_e, v_t


    def set_phys_prop(self,
                  lambda_s,    # [W/m/K] solid conductivity
                  rho_c_s,     # [J/m³/K] solid volumetric heat capacity
                  k,           # [m²] intrinsic permeability
                  n,           # [-] porosity
                  gradH,       # [-] hydraulic gradient (positive downward)
                  #--------
                  lambda_w=0.6,
                  rho_w=1000.0,
                  c_w=4182.0,
                  mu_w=1.002e-3,
                  g=9.81,
                  compute_now=True,
                  verbose=True):
        """
        Store physical properties of the porous medium and, if compute_now=True,
        compute and store (kappa_e, v_t) using effective_params().

        Parameters
        ----------
        lambda_s : float
            Solid thermal conductivity [W/m/K].
        rho_c_s : float
            Solid volumetric heat capacity [J/m³/K].
        k : float
            Intrinsic permeability [m²].
        n : float
            Porosity [-].
        gradH : float
            Hydraulic gradient ∂H/∂z (positive downward).
        compute_now : bool, default True
            If True, compute and store kappa_e and v_t immediately.
        """

        # Store physical properties
        self._lambda_s = float(lambda_s)
        self._rho_c_s = float(rho_c_s)
        self._k_intrin = float(k)
        self._porosity = float(n)
        self._gradH = float(gradH)

        # Compute effective parameters if requested
        if compute_now:
            kappa_e, v_t = self.effective_params(
                lambda_s=lambda_s,
                rho_c_s=rho_c_s,
                k=k,
                n=n,
                gradH=gradH,
                lambda_w=lambda_w,
                rho_w=rho_w,
                c_w=c_w,
                mu_w=mu_w,
                g=g
            )
            self._kappa_e = float(kappa_e)
            self._v_t = float(v_t)
            if verbose:
                print(f"[set_phys_prop] Effective parameters computed:")
                print(f"  kappa_e = {kappa_e:.3e} m²/s")
                print(f"  v_t = {v_t:.3e} m/s")
        else:
            if verbose:
                print("[set_phys_prop] Physical properties stored but not yet converted into (kappa_e, v_t).")

        return self


    def _need(self, name, value, where):
        if value is None:
            raise ValueError(f"'{name}' is required but not set. "
                             f"Either pass it to {where}(...) or set it once with set_inputs({name}=...).")
        return value


    def _to_seconds(self, dates):
        d = np.asarray(dates)
        # numpy datetime64 array
        if np.issubdtype(d.dtype, np.datetime64):
            return (d - d[0]).astype('timedelta64[s]').astype(float)

        # Python datetime objects (dtype=object)
        if d.dtype == object:
            # try to compute seconds relative to first timestamp
            try:
                t0 = d[0]
                # handle if elements are datetime.datetime
                secs = np.array([float((ti - t0).total_seconds()) for ti in d], dtype=float)
                return secs
            except Exception:
                # fall through to numeric conversion
                pass

        # fallback: assume numeric array (seconds)
        return d.astype(float)


    def plot_signals(self, dates=None, signals=None, depths=None):
        """This function simply plots the input signals over time with the corresponding depths."""

        if dates is None:       dates = self._need('dates', self._dates, 'plot_signals')
        if signals is None:     signals = self._need('signals', self._signals, 'plot_signals')
        if depths is None:      depths = self._need('depths', self._depths, 'plot_signals')

        plt.figure(figsize=(9, 4))

        for i, signal in enumerate(signals):
            plt.plot(dates, signal, label=f'Signal at depth {depths[i]:.2f} m')

        plt.xticks(rotation=90)
        plt.xlabel('Date')
        plt.ylabel('Temperature (K)')
        plt.title('Temperature Signals Over Time')
        plt.legend()
        plt.show()

    def find_dominant_periods(
        self,
        dates_or_signals=None,
        signals_or_river=None,
        draw=True,
        use_hann=True,
        prom_rel=0.05,
        Q_min=10.0,
        Q_max=np.inf,
        amplitude_threshold=0.0,
        max_width_rel=0.20,
        min_cycles=3,
        store=True,            # <-- store internal state
        compute_phases=True    # <-- compute/store phases at z=0
        ):
        """
        Detection of dominant periods in the 'river' signal..

        Behavior depending on input arguments:
        - If dates_or_signals et signals_or_river are both None:
            * use self._dates and self._signals as inputs
        - Otherwise: remain compatible with your two existing signatures:
            * (dates, signals)   or   (signals, river) (legacy)

        If store=True, also store:
            self._periods_days, self._amps_surface, self._last_fft_meta, (and self._phases if compute_phases)
        """

        if dates_or_signals is None and signals_or_river is None:
            if not hasattr(self, "_dates") or self._dates is None:
                raise ValueError("No inputs provided and self._dates is not set. "
                                "Either pass (dates, signals) or call set_inputs(dates=..., signals=...).")
            if not hasattr(self, "_signals") or self._signals is None:
                raise ValueError("No inputs provided and self._signals is not set. "
                                "Either pass (dates, signals) or call set_inputs(signals=...).")
            dates = np.asarray(self._dates)
            signals = self._signals
            river = np.asarray(signals[0], dtype=float)
        else:
            # Keep compatibility with both signatures:
            def _is_datetime_array(a):
                a = np.asarray(a)
                if np.issubdtype(a.dtype, np.datetime64):
                    return True
                if a.dtype == object and a.size > 0:
                    import datetime as _dt
                    return isinstance(a[0], _dt.datetime)
                return False

            if _is_datetime_array(dates_or_signals):
                dates = np.asarray(dates_or_signals)
                signals = signals_or_river
                if signals is None:
                    raise ValueError("With signature (dates, signals), 'signals' cannot be None.")
                river = np.asarray(signals[0], dtype=float)
            else:
                signals = dates_or_signals
                river = np.asarray(signals_or_river, dtype=float)
                if not hasattr(self, '_last_dates') or self._last_dates is None:
                    raise ValueError(
                        "Legacy signature detected but no stored 'dates' found. "
                        "Call find_dominant_periods(dates, signals) first or set self._dates."
                    )
                dates = np.asarray(self._last_dates)


        # Below is really the algo...

        # FFT and amplitude peaks detection
        t = self._to_seconds(dates)
        river = np.asarray(river, dtype=float)
        if river.ndim != 1:
            raise ValueError(f"'river' must be 1D, got shape={river.shape}")
        if t.size != river.size:
            raise ValueError(f"size(t)={t.size} != size(river)={river.size}")

        m = np.isfinite(t) & np.isfinite(river)
        t = t[m]; river = river[m]
        if t.size < 8:
            raise ValueError("Not enough valid samples for FFT.")

        n = t.size
        dt = float(np.median(np.diff(t)))
        T  = n * dt
        f_res = 1.0 / T

        x = river - np.nanmean(river)
        if use_hann:
            w = get_window('hann', n, fftbins=True)
            x = x * w
            x = x / (np.sum(w)/n)

        yf = np.fft.rfft(x)
        freqs = np.fft.rfftfreq(n, d=dt)
        amp = np.abs(yf) / n

        mask = freqs > 0
        freqs_m = freqs[mask]
        amp_m   = amp[mask]

        prom = np.max(amp_m) * prom_rel
        peaks, props = find_peaks(amp_m, prominence=prom)
        if peaks.size:
            order = np.argsort(amp_m[peaks])[::-1]
            peaks = peaks[order]

        widths_bins, h_eval, left_ips, right_ips = peak_widths(amp_m, peaks, rel_height=0.5)
        df = (freqs_m[1] - freqs_m[0]) if freqs_m.size > 1 else f_res
        fwhm_hz = widths_bins * df

        f0  = freqs_m[peaks]
        A0  = amp_m[peaks]
        with np.errstate(divide='ignore', invalid='ignore'):
            Q = f0 / fwhm_hz
            width_rel = fwhm_hz / f0

        enough_cycles = (T * f0) >= min_cycles
        narrow_enough = (Q >= Q_min) & (width_rel <= max_width_rel) & (Q <= Q_max) & (A0 >= amplitude_threshold)
        accepted = enough_cycles & narrow_enough

        period_days = 1.0 / (f0 * 86400.0)

        result = {
            'period_days': period_days,
            'freq_hz': f0,
            'amplitude': A0,
            'fwhm_hz': fwhm_hz,
            'Q': Q,
            'accepted_mask': accepted,
            'f_res_hz': f_res,
            'prominence': props.get('prominences', np.full_like(A0, np.nan)),
        }

        if draw:
            plt.figure(figsize=(9,4))
            P_all = 1.0 / (freqs_m * 86400.0)

            if amplitude_threshold > 0:
                plt.hlines(amplitude_threshold, P_all[0], P_all[-1], colors='tab:orange', linestyles='--', label='Amplitude threshold')

            plt.plot(P_all, amp_m, label='FFT amplitude')
            plt.plot(period_days, A0, 'o', mfc='none', mec='tab:red', label='Detected peaks')
            plt.plot(period_days[accepted], A0[accepted], 'o', color='tab:green', label='Accepted')
            dP = fwhm_hz / (f0**2) / 86400.0
            for P, A, d in zip(period_days, A0, dP):
                plt.hlines(A, P - d/2, P + d/2, colors='gray', alpha=0.6)
            plt.xscale('log'); plt.xlabel('Period (days)'); plt.ylabel('Amplitude')
            ttl = f"River FFT — f_res={f_res:.3e} Hz (~{1/(f_res*86400):.1f} days)"
            plt.title(ttl); plt.grid(True, which='both', ls=':'); plt.legend(); plt.tight_layout(); plt.show()

        # Saving in the object state
        if store:
            mask_keep = accepted
            Pd_kept = np.asarray(period_days)[mask_keep]
            A0_kept = np.asarray(A0)[mask_keep]
            f0_kept = np.asarray(f0)[mask_keep]

            # store for next pipeline
            self._last_fft_meta = result
            self._last_dates = dates
            self._periods_days = Pd_kept
            self._amps_surface = A0_kept

            if compute_phases:
                # phases at z=0  
                phases = []
                for f in f0_kept:
                    idx = np.argmin(np.abs(freqs - f))
                    phases.append(np.angle(yf[idx]))
                self._phases = np.array(phases, float)

            # Optionally store dates and signals if not already set
            if not hasattr(self, '_dates') or self._dates is None:
                self._dates = dates
            if not hasattr(self, '_signals') or self._signals is None:
                # If we were in legacy (signals, river), we may not have it here
                try:
                    self._signals = signals
                except NameError:
                    pass

        # returns
        return period_days, f0, A0, result

    
    def fft_sensors(self, dates=None, signals=None, depths=None):
        """Compute FFT of each sensor signal.
        Plots a global figure with the amplitude spectra of all sensors.
        """
        
        if dates is None:       dates = self._need('dates', self._dates, 'fft_sensors')
        if signals is None:     signals = self._need('signals', self._signals, 'fft_sensors')
        if depths is None:      depths = self._need('depths', self._depths, 'fft_sensors')

        t = self._to_seconds(dates)
        # store the provided dates so legacy calls can reuse them
        try:
            self._last_dates = dates
        except Exception:
            self._last_dates = None
        t = np.asarray(t)
        results = []
        for signal in signals:
            signal = np.asarray(signal)
            if signal.ndim != 1:
                raise ValueError(f"signal must be 1D array, got shape {signal.shape}")
            if t.size != signal.size:
                raise ValueError(f"time axis length ({t.size}) and signal length ({signal.size}) must match")

            n = signal.size
            dt = np.median(np.diff(t))
            yf = np.fft.rfft(signal - np.mean(signal))
            amp = np.abs(yf) / n
            freqs = np.fft.rfftfreq(n, d=dt)
            results.append((freqs, amp))
        
        # Plotting the FFT results for all sensors
        plt.figure(figsize=(9, 4))
        for i, (freqs, amp) in enumerate(results):
            plt.plot(1.0 / (freqs * 86400.0), amp, label=f'Sensor at depth {depths[i]} m')

        plt.xscale('log')
        plt.xlabel('Period (days)')
        plt.ylabel('Amplitude')
        plt.title('FFT of Sensor Temperature Signals')
        plt.legend()
        plt.grid()
        plt.show()


    def estimate_a(self, dates=None, signals=None, depths=None, periods_days=None, verbose=True, draw=True, intercept=True):
        """For each signal, compute the amplitudes at peaks of dominant periods.
        Then for each period, estimate the exponential decay of the corresponding amplitude A(z, omega)/A(0, omega) = e^(-a*z)"""

        if dates is None:                   dates = self._need('dates', self._dates, 'estimate_a')
        if signals is None:                 signals = self._need('signals', self._signals, 'estimate_a')
        if depths is None:                  depths = self._need('depths', self._depths, 'estimate_a')
        if periods_days is None:   periods_days = self._need('periods_days', self._periods_days, 'estimate_a')

        amplitudes_at_peaks = []

        print("This deals only with 1D attenuation (no lateral flow).")

        for i in range(len(signals)):
            signal = signals[i]
            # Find the amplitudes at the dominant frequencies for this signal
            t = self._to_seconds(dates)
            signal = np.asarray(signal)

            n = signal.size
            dt = np.median(np.diff(t))
            yf = np.fft.rfft(signal - np.mean(signal))
            amp = np.abs(yf) / n
            freqs = np.fft.rfftfreq(n, d=dt)
             
            # Find the amplitudes at the dominant frequencies i.e the A(z)
            amplitudes_at_peaks_for_this_signal = []
            for Pd in periods_days:
                target_freq = 1.0 / (Pd * 86400.0)
                idx = (np.abs(freqs - target_freq)).argmin()
                amplitudes_at_peaks_for_this_signal.append(amp[idx])
            amplitudes_at_peaks.append(amplitudes_at_peaks_for_this_signal)

		# Store the A(z) in the list
        amplitudes_at_peaks = np.array(amplitudes_at_peaks)  # shape (n_signals, n_periods)

        # Normalize depths -> depths_all should map 1:1 to signals
        depths_arr = np.asarray(depths)
        if verbose:
            print("Detected depths:", depths_arr)

        # attempt to align amplitudes/signals with depths robustly
        n_ampl_rows = amplitudes_at_peaks.shape[0]

        # helper: try to fix duplicated river row (common mistake)
        def _drop_duplicate_river(ampl):
            if ampl.shape[0] >= 2:
                # compare first two rows across all periods
                if np.allclose(ampl[0, :], ampl[1, :], rtol=1e-6, atol=1e-9):
                    if verbose:
                        print("Detected duplicate river signal in amplitudes — removing second row.")
                    return np.delete(ampl, 1, axis=0), True
            return ampl, False

        amplitudes_aligned = amplitudes_at_peaks.copy()
        dropped = True
        # try removing duplicate river at most once
        ampl_tmp, did = _drop_duplicate_river(amplitudes_aligned)
        if did:
            amplitudes_aligned = ampl_tmp

        n_ampl_rows = amplitudes_aligned.shape[0]

        if depths_arr.size == n_ampl_rows - 1:
            depths_all = np.concatenate(([0.0], depths_arr))
        elif depths_arr.size == n_ampl_rows:
            depths_all = depths_arr
        else:
            # final diagnostic message to help the user correct inputs
            raise ValueError(
                f"Depths length ({depths_arr.size}) incompatible with number of signals ({n_ampl_rows}).\n"
                "Expected either len(depths) == n_signals-1 (sensor depths) or len(depths) == n_signals (including river).\n"
                f"Amplitude rows: {n_ampl_rows}, depths: {depths_arr}.\n"
                "If you used legacy calls, ensure fft_sensors(dates, signals) was called before find_dominant_periods so dates are set."
            )

        if verbose:
            print("Amplitudes at dominant periods for each signal computed.")
            for i, Pd in enumerate(periods_days):
                amps_for_period = amplitudes_at_peaks[:, i]
                print(f"Period {Pd:.2f} days: Amplitudes = {amps_for_period}")

        # Now estimate a for each period in periods_days
        a_values = []	# Values of "a" parameter which controls the decrease of the amplitude
        a_R2_values = []	# R^2 values of the linear regression of a.
        # Save in the class the values of amplitudes at peaks for possible later use
        self._AMPS_AT_PEAKS = amplitudes_at_peaks[:,:] # store for later use if needed

        # We'll collect plotting data per period and, if requested, draw them in a single figure
        plot_items = []
        for i, Pd in enumerate(periods_days):
            # amplitudes for all signals at this period
            A_all = amplitudes_aligned[:, i]
            z = depths_all

            # avoid division by zero on reference amplitude
            if A_all[0] == 0 or not np.isfinite(A_all[0]):
                if verbose:
                    print(f"Reference amplitude A0 invalid (={A_all[0]}). Skipping period {Pd}.")
                a_values.append(np.nan)
                a_R2_values.append(np.nan)
                plot_items.append({'Pd': Pd, 'skipped': True, 'reason': 'invalid A0'})
                continue

            with np.errstate(divide='ignore', invalid='ignore'):
                ratio = A_all / A_all[0]
                log_ratio = np.log(ratio)
            # ensure z and log_ratio have same length (defensive)
            if z.size != log_ratio.size:
                min_n2 = min(z.size, log_ratio.size)
                if verbose:
                    print(f"Warning: trimming z ({z.size}) and log_ratio ({log_ratio.size}) to min length {min_n2} before fitting")
                z = z[:min_n2]
                log_ratio = log_ratio[:min_n2]

            m = np.isfinite(log_ratio)

            if m.sum() < 2:
                a_values.append(np.nan)
                a_R2_values.append(np.nan)
                plot_items.append({'Pd': Pd, 'skipped': True, 'reason': 'not enough finite points'})
                continue

            # perform model-selection (1D linear vs 2D polynomial) on the log-amplitude
            z_m = z[m]
            y_m = log_ratio[m]

            # perform linear fit on finite data (1D assumption accepted)
            if intercept:
                # fit slope and intercept (ordinary least squares)
                coeffs = np.polyfit(z_m, y_m, 1)
                slope = coeffs[0]
                intercept_val = coeffs[1]
            else:
                # force fit through origin: slope = sum(z*y)/sum(z^2)
                denom = np.sum(z_m * z_m)
                if denom == 0:
                    if verbose:
                        print(f"Degenerate depths for period {Pd}: sum(z^2)==0, skipping")
                    a_values.append(np.nan)
                    a_R2_values.append(np.nan)
                    plot_items.append({'Pd': Pd, 'skipped': True, 'reason': 'degenerate depths'})
                    continue
                slope = np.sum(z_m * y_m) / denom
                intercept_val = 0.0
                coeffs = np.array([slope, intercept_val])

            a_fit = -slope
            # compute R^2
            y_pred = slope * z_m + intercept_val
            ss_res = np.sum((y_m - y_pred) ** 2)
            ss_tot = np.sum((y_m - np.mean(y_m)) ** 2)
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

            # store plot data for later combined plotting
            plot_items.append({'Pd': Pd, 'skipped': False, 'z': z.copy(), 'log_ratio': log_ratio.copy(), 'coeffs': np.array(coeffs).copy(), 'a_fit': a_fit, 'r2': r2, 'model': '1D'})

            # Store the fitted a value and the R^2 value
            a_values.append(a_fit)
            a_R2_values.append(r2)

        # After the loop, create a single figure with subplots if requested
        if draw:
            n_plots = len(periods_days)
            if n_plots == 0:
                pass
            else:
                ncols = min(3, n_plots)
                nrows = int(np.ceil(n_plots / ncols))
                fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4 * ncols, 4 * nrows))
                axes = np.atleast_1d(axes).ravel()
                for idx, item in enumerate(plot_items):
                    ax = axes[idx]
                    Pd = item.get('Pd')
                    ax.set_title(f"Estimation of a for period {Pd:.2f} days")
                    if item.get('skipped'):
                        ax.text(0.5, 0.5, f"Skipped: {item.get('reason')}", ha='center', va='center')
                        ax.set_xticks([]); ax.set_yticks([])
                        continue
                    z = item['z']
                    log_ratio = item['log_ratio']
                    coeffs = item['coeffs']
                    a_fit = item['a_fit']
                    ax.scatter(z, log_ratio, label='Data (log(A(z)/A(0)))')
                    z_fit = np.linspace(0, np.max(depths), 100)
                    log_ratio_fit = coeffs[0] * z_fit + coeffs[1]
                    ax.plot(z_fit, log_ratio_fit, 'r-', label=f'Fit: slope = {-a_fit:.4f}')
                    ax.set_xlabel('Depth (m)')
                    ax.set_ylabel('log(A(z)/A(0))')
                    ax.legend()
                    ax.grid()
                # hide any unused axes
                for j in range(len(plot_items), axes.size):
                    axes[j].axis('off')
                plt.tight_layout()
                plt.show()
        
        if verbose:
            print("Attenuation coefficients a estimated for each dominant period.")
            for i, Pd in enumerate(periods_days):
                print(f"Period {Pd:.2f} days: a = {a_values[i]:.4f} 1/m")
                print(f"Period {Pd:.2f} days: R^2 = {a_R2_values[i]:.4f}")

        self._a_values, self._a_R2 = np.array(a_values), np.array(a_R2_values)
        return self._a_values, self._a_R2


    def estimate_b(self, dates=None, signals=None, depths=None, periods_days=None, bw_frac=0.15, order=4, amp_thresh=None, verbose=True, draw=True, intercept=True):
        """Estimate b (phase decay) using bandpass+Hilbert method.
        periods_days: array-like in days
        Returns array of b values (rad/m)
        """

        if dates is None:           dates  = self._need('dates',  self._dates,  'estimate_b')
        if signals is None:         signals = self._need('signals',self._signals,'estimate_b')
        if depths is None:          depths = self._need('depths', self._depths, 'estimate_b')
        if periods_days is None:   periods_days = self._need('periods_days', self._periods_days, 'estimate_b')

        river = signals[0]
        sensors = signals[1:]

        t = self._to_seconds(dates)
        river = np.asarray(river)
        sensors = np.asarray(sensors)
        if sensors.ndim == 1:
            sensors = sensors[np.newaxis, :]
        depths = np.asarray(depths)

        def regularize(t_in, y_in):
            t1 = np.asarray(t_in, float); y1 = np.asarray(y_in, float)
            m = np.isfinite(t1) & np.isfinite(y1)
            t1, y1 = t1[m], y1[m]
            dt = np.median(np.diff(t1))
            tg = np.arange(t1[0], t1[-1] + 0.5*dt, dt)
            yg = np.interp(tg, t1, y1)
            return tg, yg, 1.0/dt


        # On fait un butterworth bandpass autour de la fréquence f0 à un sampling fs
        # Pourquoi ?? Car si on demande à un algo de FFT de trouver les déphasages, alors comme le signal est multipériodique,
        # Puisque les peaks sont assez proches, on risque d'avoir des interférences entre les périodes.
        # En faisant un bandpass on isole la période d'intérêt et on évite les interférences.
        def butter_band(f0, fs):
            ny = fs/2.0
            fl = max(1e-12, f0*(1 - bw_frac/2.0))
            fh = min(ny*0.99, f0*(1 + bw_frac/2.0))
            if fl >= fh:
                raise ValueError("Invalid bandpass")
            b, a = butter(order, [fl/ny, fh/ny], btype='band')
            return b, a

    # Apply Hilbert transform to obtain the analytic signal (absolute phase).
        def analytic(t_in, y_in, f0):
            tg, yg, fs = regularize(t_in, y_in)
            b, a = butter_band(f0, fs)
            yf = filtfilt(b, a, yg)
            z = hilbert(yf)
            return tg, z

        periods_days = np.atleast_1d(periods_days)

        b_values = []
        b_R2_values = []

        # collect plot items to display all fits in a single figure if requested
        plot_items_b = []
        for Pd in periods_days:
            P = Pd * 86400.0
            f0 = 1.0 / P
            tr, zr = analytic(t, river, f0)
            phases = [0.0]
            for s in sensors:
                ts, zs = analytic(t, s, f0)
                zs_i = np.interp(tr, ts, zs.real) + 1j*np.interp(tr, ts, zs.imag)
                if amp_thresh is not None:
                    m = (np.abs(zr) > amp_thresh) & (np.abs(zs_i) > amp_thresh)
                    if m.sum() < 10:
                        phases.append(np.nan)
                        continue
                    dphi = np.angle(zs_i[m] * np.conj(zr[m]))
                else:
                    dphi = np.angle(zs_i * np.conj(zr))
                ph_mean = np.angle(np.mean(np.exp(1j*dphi)))
                phases.append(ph_mean)

            ph = np.array(phases, float)
            # Be careful to unwrap the phase; otherwise the phase will be wrapped and linear fitting will fail.
            ph_unw = np.unwrap(ph)

            for k in range(1, len(ph_unw)):
                while ph_unw[k] > ph_unw[k-1]:
                    ph_unw[k] -= 2*np.pi


            # Normalize depths to match the number of sensor signals.
            # Follow the same convention as estimate_a:
            # - If `depths` has length n_sensors -> it contains only sensor depths and river is at z=0 implicitly.
            # - If `depths` has length n_sensors+1 -> it already includes the river depth (usually 0) as the first element.
            depths_arr = np.asarray(depths)
            n_sensors = sensors.shape[0]

            if depths_arr.size == n_sensors:
                # sensor depths only -> prepend river at 0
                depths_all = np.concatenate(([0.0], depths_arr))
            elif depths_arr.size == n_sensors + 1:
                # depths already include river
                depths_all = depths_arr
            else:
                # try to be helpful: trim or extend to expected size
                if depths_arr.size > n_sensors + 1:
                    if verbose:
                        print(f"Warning: provided depths length ({depths_arr.size}) > expected ({n_sensors+1}). Trimming depths.")
                    depths_all = depths_arr[:(n_sensors + 1)]
                elif depths_arr.size < n_sensors:
                    raise ValueError(f"Depths length ({depths_arr.size}) incompatible with number of sensor signals ({n_sensors}). Provide either sensor-only depths (len == n_sensors) or include river depth (len == n_sensors+1).")
                else:
                    # depths_arr.size == n_sensors - 1 (or other odd case): pad with nan to keep sizes consistent then trim later
                    if verbose:
                        print(f"Warning: provided depths length ({depths_arr.size}) unexpected. Attempting to align by padding/trimming.")
                    # pad sensors-only assumption
                    depths_all = np.concatenate(([0.0], depths_arr))

            # Now ensure phases and depths_all have the same length. ph_unw should have length 1 + n_sensors
            n_ph = ph_unw.size
            if n_ph != depths_all.size:
                if verbose:
                    print(f"Warning: number of phase entries ({n_ph}) != number of depth entries ({depths_all.size}). Aligning by trimming the longer list.")
                if n_ph > depths_all.size:
                    ph_unw = ph_unw[:depths_all.size]
                else:
                    depths_all = depths_all[:n_ph]
            m = np.isfinite(ph_unw)
            if m.sum() < 2:
                b_values.append(np.nan)
                continue

            # Fitting lineaire de la phase en beta*z = - b*z
            if intercept:
                coeffs = np.polyfit(depths_all[m], ph_unw[m], 1)
                beta = coeffs[0]
                intercept_val = coeffs[1]
            else:
                denom = np.sum(depths_all[m] * depths_all[m])
                if denom == 0:
                    if verbose:
                        print(f"Degenerate depths for period {Pd}: sum(depths^2)==0, skipping")
                    b_values.append(np.nan)
                    b_R2_values.append(np.nan)
                    continue
                beta = np.sum(depths_all[m] * ph_unw[m]) / denom
                intercept_val = 0.0
                coeffs = np.array([beta, intercept_val])

            b_val = -beta
            b_values.append(b_val)
            # Compute R^2
            residuals = ph_unw[m] - (beta * depths_all[m] + intercept_val)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((ph_unw[m] - np.mean(ph_unw[m]))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            b_R2_values.append(r2)

            # collect plotting info
            plot_items_b.append({
                'Pd': Pd,
                'skipped': False,
                'depths_all': depths_all.copy(),
                'ph_unw': ph_unw.copy(),
                'coeffs': coeffs.copy(),
                'b_val': b_val,
                'r2': r2
            })

        # After loop: draw combined subplots for b if requested
        if draw:
            n_plots_b = len(periods_days)
            if n_plots_b > 0:
                ncols_b = min(3, n_plots_b)
                nrows_b = int(np.ceil(n_plots_b / ncols_b))
                figb, axesb = plt.subplots(nrows=nrows_b, ncols=ncols_b, figsize=(4 * ncols_b, 4 * nrows_b))
                axesb = np.atleast_1d(axesb).ravel()
                for idx, item in enumerate(plot_items_b):
                    ax = axesb[idx]
                    Pd = item['Pd']
                    ax.set_title(f"Estimation of b for period {Pd:.2f} days")
                    depths_all = item['depths_all']
                    ph_unw = item['ph_unw']
                    coeffs = item['coeffs']
                    b_val = item['b_val']
                    ax.scatter(depths_all, ph_unw, label='Data (unwrapped phase)')
                    z_fit = np.linspace(0, np.max(depths), 100)
                    ph_fit = coeffs[0] * z_fit + coeffs[1]
                    ax.plot(z_fit, ph_fit, 'r-', label=f'Fit: slope = {-b_val:.4f}')
                    ax.set_xlabel('Depth (m)')
                    ax.set_ylabel('Unwrapped Phase (rad)')
                    ax.legend()
                    ax.grid()
                for j in range(len(plot_items_b), axesb.size):
                    axesb[j].axis('off')
                plt.tight_layout()
                plt.show()

        if verbose:
            print("Phase decay coefficients b estimated for each dominant period.")
            for i, Pd in enumerate(periods_days):
                print(f"Period {Pd:.2f} days: b = {b_values[i]:.4f} rad/m")
                print(f"Period {Pd:.2f} days: R^2 = {b_R2_values[i]:.4f}")

        self._b_values, self._b_R2 = np.array(b_values), np.array(b_R2_values)
        return self._b_values, self._b_R2
    

    def perform_inversion(self, a_values=None, b_values=None, periods_days=None, verbose=True):
        """Invert for kappa_e and v_t for given a, b, and periods (days).
        Returns (kappa_e, v_t)
        """

        if a_values is None:      a_values = self._need('a_values', getattr(self, '_a_values', None), 'perform_inversion')
        if b_values is None:      b_values = self._need('b_values', getattr(self, '_b_values', None), 'perform_inversion')
        if periods_days is None:  periods_days = self._need('periods_days', self._periods_days, 'perform_inversion')

        a = np.asarray(a_values, float)
        b = np.asarray(b_values, float)
        P = np.asarray(periods_days, float) * 86400.0
        kappa_e = (np.pi * 2.0 * a) / (P * b * (b**2 + a**2))
        v_t = kappa_e * (b**2 - a**2) / a
        print("Inversion complete.")

        if verbose:
            for i, Pd in enumerate(periods_days):
                print(f"Period {Pd:.2f} days: kappa_e = {kappa_e[i]:.3e} m^2/s, v_t = {v_t[i]:.3e} m/s")

        self._kappa_e_series, self._v_t_series = kappa_e, v_t
        return kappa_e, v_t

    def phys_to_a_b(self, kappa_e=None, v_t=None, periods_days=None):
        """Convert physical parameters kappa_e and v_t to attenuation (a) and phase-shift (b) coefficients.
        periods_days: array-like in days
        Returns (a_values, b_values)
        """

        if kappa_e is None:       kappa_e = self._need('kappa_e', getattr(self, '_kappa_e', None), 'phys_to_a_b')
        if v_t is None:           v_t = self._need('v_t', getattr(self, '_v_t', None), 'phys_to_a_b')
        if periods_days is None:  periods_days = self._need('periods_days', self._periods_days, 'phys_to_a_b')

        omega = 2*np.pi/(periods_days * NSECINDAY)  # angular frequencies [rad/s]
        alpha = (-v_t + np.sqrt(v_t**2 + 4j*omega*kappa_e)) / (2*kappa_e)
        a_, b_ = np.real(alpha), np.imag(alpha)
        return a_, b_

    def critere_2D(self, period_index: int = 0, deg_max: int = 2, show_reg: bool = False):
        """
        Decide whether the attenuation behaviour is best described by a 1D exponential
        (linear fit of ln(A/A0) vs z) or requires a 2D (polynomial) model.

        Parameters
        ----------
        period_index : int
            Index of the period (column) in self._AMPS_AT_PEAKS to use for the test.
        deg_max : int
            Maximum polynomial degree to test (will test degrees 1..deg_max).
        show_reg : bool
            If True, show regression plots for each tested degree.

        Returns
        -------
        dict
            Dictionary with keys: 'modele' ('1D' or '2D'), 'r2_list', 'coeffs'.
        """
        # Basic availability checks
        if not hasattr(self, '_AMPS_AT_PEAKS') or self._AMPS_AT_PEAKS is None:
            raise ValueError("_AMPS_AT_PEAKS not set. Run estimate_a(...) before calling critere_2D().")
        if not hasattr(self, '_depths') or self._depths is None:
            raise ValueError("_depths not set. Provide depths via set_inputs(depths=...) before calling critere_2D().")

        brut = np.asarray(self._AMPS_AT_PEAKS)
        if brut.ndim != 2:
            raise ValueError(f"_AMPS_AT_PEAKS must be 2D (n_signals x n_periods), got shape {brut.shape}")

        n_signals, n_periods = brut.shape
        if period_index < 0 or period_index >= n_periods:
            raise IndexError(f"period_index {period_index} out of range (0..{n_periods-1})")

        # build log ratio ln(A(z)/A0) across signals for the requested period
        A_col = brut[:, period_index].astype(float)
        if A_col[0] == 0 or not np.isfinite(A_col[0]):
            raise ValueError("Reference amplitude A0 is zero or invalid for chosen period_index")
        traite = np.log(A_col / A_col[0])

        # depths: use internal _depths (should include river at z=0 if needed)
        z_values = np.asarray(self._depths, float)

        # Align lengths: trim to the shortest
        min_len = min(z_values.size, traite.size)
        z_values = z_values[:min_len]
        traite = traite[:min_len]

        # Remove non-finite entries
        mask = np.isfinite(z_values) & np.isfinite(traite)
        z_values = z_values[mask]
        traite = traite[mask]

        if z_values.size < 2:
            raise ValueError("Not enough valid depth/amplitude points for regression")

        def regression_poly(reg, z_vals, deg, show_plot=False, return_coeffs=False):
            coeffs = np.polyfit(z_vals, reg, deg)
            p = np.poly1d(coeffs)
            y_pred = p(z_vals)
            r2 = r2_score(reg, y_pred)
            if show_plot:
                plt.scatter(z_vals, reg, label='Données FFT mesurées')
                plt.plot(z_vals, y_pred, 'r--', label=f'Ajustement poly {deg}: R²={r2:.3f}')
                plt.xlabel('Profondeur z (m)')
                plt.ylabel('Log amplitude ln(A(z)/A0)')
                plt.title(f"Régression polynomiale de degré {deg}, R²={r2:.3f}")
                plt.legend()
                plt.show()
            if return_coeffs:
                return coeffs, r2
            else:
                return r2

        r2_list = []
        coeffs_list = []
        # test degrees 1 .. deg_max (inclusive)
        for deg in range(1, deg_max + 1):
            coeff, r2 = regression_poly(traite, z_values, deg, show_plot=show_reg, return_coeffs=True)
            r2_list.append(r2)
            coeffs_list.append(coeff)

        # Decision rule: prefer 1D unless higher-degree R² significantly improves and leading coeff is meaningful
        modele = '1D'
        if len(r2_list) >= 2:
            if r2_list[0] < 0.99 and r2_list[1] > r2_list[0] and abs(coeffs_list[1][0]) > 0.1:
                modele = '2D'

        return {'modele': modele, 'r2_list': np.array(r2_list), 'coeffs': coeffs_list}

