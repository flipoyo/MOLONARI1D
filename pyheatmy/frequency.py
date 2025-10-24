import numpy as np
import matplotlib.pyplot as plt
from pyheatmy import *
from datetime import datetime, timedelta
import os as os
import csv as csv 
from scipy.signal import butter, filtfilt, hilbert, find_peaks

"""
Module for frequency domain analysis of temperature data.
The inputs will be the signals of the sensors, the depths of the sensors and the temperature of the river.
The aim is to retrieve values of diffusivity kappa_e and Stallman speed v_t.
"""

class frequentiel_analysis:
    def __init__(self, verbose=True):
        if verbose:
            print("Frequentiel analysis module initialized.")
            print("This module will analyze a multi-periodic signal to estimate attenuation and phase decay coefficients.")
            print("Using phase decay and amplitude attenuation with depth, we'll retrieve kappa_e and v_t for each dominant period.")

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
    
    def find_dominant_periods(self, dates, signals, draw=True):
        """Find dominant periods in river signal using FFT.
		This is an automatic processing. It takes the FFT spectrum and returns highest 
		peak with threshold.
        Returns (periods_days, amplitudes, frequencies)
        """
        # Support two calling styles for backward compatibility:
        # 1) find_dominant_periods(dates, signals, draw=True)
        #    where signals = [river, sensor1, sensor2, ...]
        # 2) legacy: find_dominant_periods(signals, river, draw=True)
        #    where the user passed (signals_list, river_array)
        # Require explicit dates array (physical times) as first argument.
        dates_arr = np.asarray(dates)
        is_dates = False
        try:
            if np.issubdtype(dates_arr.dtype, np.datetime64):
                is_dates = True
            elif dates_arr.dtype == object and len(dates_arr) > 0:
                import datetime as _dt
                is_dates = isinstance(dates_arr[0], _dt.datetime)
        except Exception:
            is_dates = False

        if not is_dates:
            # Try to use stored dates from a prior fft_sensors(dates, ...) call
            if hasattr(self, '_last_dates') and self._last_dates is not None:
                dates = self._last_dates
                t = self._to_seconds(dates)
                # interpret legacy calling style: first arg 'dates' was actually signals list
                signals_list = dates_arr
                signals = signals_list
                river = signals[0]
            else:
                raise ValueError(
                    "find_dominant_periods requires a 'dates' array as the first argument (numpy.datetime64 or list of datetime).\n"
                    "If you used the legacy call find_dominant_periods(signals, river), call fft_sensors(dates, signals, ...) first so dates are stored, or call find_dominant_periods(dates, signals) directly."
                )
        else:
            t = self._to_seconds(dates)
            river = signals[0]

        # Perform rFFT of the river temperature signal.
        river = np.asarray(river)
        t = np.asarray(t)
        if river.ndim != 1:
            raise ValueError(f"river must be 1D array, got shape {river.shape}")
        if t.size != river.size:
            raise ValueError(f"time axis length ({t.size}) and river signal length ({river.size}) must match")

        n = river.size
        dt = np.median(np.diff(t))
        yf = np.fft.rfft(river - np.mean(river))
        amp = np.abs(yf) / n
        freqs = np.fft.rfftfreq(n, d=dt)

    # Now use find_peaks to identify dominant frequencies. This is automatic and we have a threshold to choose.
        mask = freqs > 0
        amps_masked = amp[mask]
        freqs_masked = freqs[mask]
        # Use a prominence threshold (fraction of max amplitude) to avoid too many small peaks
        prom_thresh = np.max(amps_masked) * 0.05  # tuneable (5% of max amplitude)
        peaks, props = find_peaks(amps_masked, prominence=prom_thresh)

        # sort peaks by amplitude (descending) so dominant peaks appear first
        if peaks.size:
            order = np.argsort(amps_masked[peaks])[::-1]
            peaks = peaks[order]

        dominant_freqs = freqs_masked[peaks]
        dominant_periods_days = (1.0 / dominant_freqs) / 86400.0

        print("Dominant periods analysis complete")
        print("Found periods (days):", dominant_periods_days)

		# Plotting if draw is enabled.
        if draw:
            plt.figure(figsize=(8, 4))
            plt.plot(1.0 / (freqs_masked * 86400.0), amps_masked, label='FFT Amplitude Spectrum')
            plt.plot(dominant_periods_days, amps_masked[peaks], 'ro', label='Dominant Periods')
            plt.xscale('log')
            plt.xlabel('Period (days)')
            plt.ylabel('Amplitude')
            plt.title('FFT of River Temperature Signal')
            plt.legend()
            plt.grid()
            plt.show()

        return dominant_periods_days, dominant_freqs, amps_masked[peaks]
    
    def fft_sensors(self, dates, signals, depths):
        """Compute FFT of each sensor signal.
        Returns list of (frequencies, amplitudes) for each signal.
        """
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
        plt.figure(figsize=(10, 6))
        for i, (freqs, amp) in enumerate(results):
            plt.plot(1.0 / (freqs * 86400.0), amp, label=f'Sensor at depth {depths[i]} m')

        plt.xscale('log')
        plt.xlabel('Period (days)')
        plt.ylabel('Amplitude')
        plt.title('FFT of Sensor Temperature Signals')
        plt.legend()
        plt.grid()
        plt.show()

    def plot_temperatures(self, dates, signals, depths):
        """Plot the temperature profiles on the same figure."""
        plt.figure(figsize=(10, 6))

        for signal, depth in zip(signals, depths):
            plt.plot(dates, signal, label="Sensor at depth "+str(depth)+" m")

        plt.xlabel('Date')
        plt.ylabel('Temperature (°C)')
        plt.title('Temperature Profiles')
        plt.legend()
        plt.grid()
        plt.show()

    def estimate_a(self, dates, signals, depths, dominant_periods_days, verbose=True, draw=True):
        """For each signal, compute the amplitudes at peaks of dominant periods.
        Then for each period, estimate the exponential decay of the corresponding amplitude A(z, omega)/A(0, omega) = e^(-a*z)"""
        amplitudes_at_peaks = []

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
            for Pd in dominant_periods_days:
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
            for i, Pd in enumerate(dominant_periods_days):
                amps_for_period = amplitudes_at_peaks[:, i]
                print(f"Period {Pd:.2f} days: Amplitudes = {amps_for_period}")

        # Now estimate a for each period in dominant_periods_days
        a_values = []	# Values of "a" parameter which controls the decrease of the amplitude
        a_R2_values = []	# R^2 values of the linear regression of a.


        for i, Pd in enumerate(dominant_periods_days):
            # amplitudes for all signals at this period
            A_all = amplitudes_aligned[:, i]
            z = depths_all

            # avoid division by zero on reference amplitude
            if A_all[0] == 0 or not np.isfinite(A_all[0]):
                if verbose:
                    print(f"Reference amplitude A0 invalid (={A_all[0]}). Skipping period {Pd}.")
                a_values.append(np.nan)
                a_R2_values.append(np.nan)
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
                continue
            # perform linear fit on finite data
            z_m = z[m]
            y_m = log_ratio[m]
            coeffs = np.polyfit(z_m, y_m, 1)
            a_fit = -coeffs[0]
            # compute R^2
            y_pred = np.polyval(coeffs, z_m)
            ss_res = np.sum((y_m - y_pred) ** 2)
            ss_tot = np.sum((y_m - np.mean(y_m)) ** 2)
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

            if draw:
                plt.figure(figsize=(4, 4))
                plt.title(f"Estimation of a for period {Pd:.2f} days")
                plt.scatter(z, log_ratio, label='Data (log(A(z)/A(0)))')
                z_fit = np.linspace(0, np.max(depths), 100)
                log_ratio_fit = coeffs[0] * z_fit + coeffs[1]
                plt.plot(z_fit, log_ratio_fit, 'r-', label=f'Fit: slope = {-a_fit:.4f}')
                plt.xlabel('Depth (m)')
                plt.ylabel('log(A(z)/A(0))')
                plt.legend()
                plt.grid()
                plt.show()

            # Store the fitted a value and the R^2 value
            a_values.append(a_fit)
            a_R2_values.append(r2)
        
        if verbose:
            print("Attenuation coefficients a estimated for each dominant period.")
            for i, Pd in enumerate(dominant_periods_days):
                print(f"Period {Pd:.2f} days: a = {a_values[i]:.4f} 1/m")
                print(f"Period {Pd:.2f} days: R^2 = {a_R2_values[i]:.4f}")

        return np.array(a_values), np.array(a_R2_values)


    def estimate_b(self, dates, signals, depths, periods_days, bw_frac=0.15, order=4, amp_thresh=None, verbose=True, draw=True):
        """Estimate b (phase decay) using bandpass+Hilbert method.
        periods_days: array-like in days
        Returns array of b values (rad/m)
        """

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

        # On passe pas Hilbert pour avoir un signal analytique avec phase absolue.
        def analytic(t_in, y_in, f0):
            tg, yg, fs = regularize(t_in, y_in)
            b, a = butter_band(f0, fs)
            yf = filtfilt(b, a, yg)
            z = hilbert(yf)
            return tg, z

        periods_days = np.atleast_1d(periods_days)

        b_values = []
        b_R2_values = []

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
            # Attention à bien unwrap car sinon la phase va se faire automatiquement bornée et on ne pourra pas faire de fit linéaire.
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
            coeffs = np.polyfit(depths_all[m], ph_unw[m], 1)
            beta = coeffs[0]
            b_val = -beta
            b_values.append(b_val)
            # Compute R^2
            residuals = ph_unw[m] - (coeffs[0] * depths_all[m] + coeffs[1])
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((ph_unw[m] - np.mean(ph_unw[m]))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            b_R2_values.append(r2)

            if draw:
                plt.figure(figsize=(4, 4))
                plt.title(f"Estimation of b for period {Pd:.2f} days")
                plt.scatter(depths_all, ph_unw, label='Data (unwrapped phase)')
                z_fit = np.linspace(0, np.max(depths), 100)
                ph_fit = coeffs[0] * z_fit + coeffs[1]
                plt.plot(z_fit, ph_fit, 'r-', label=f'Fit: slope = {-b_val:.4f}')
                plt.xlabel('Depth (m)')
                plt.ylabel('Unwrapped Phase (rad)')
                plt.legend()
                plt.grid()
                plt.show()

        if verbose:
            print("Phase decay coefficients b estimated for each dominant period.")
            for i, Pd in enumerate(periods_days):
                print(f"Period {Pd:.2f} days: b = {b_values[i]:.4f} rad/m")
                print(f"Period {Pd:.2f} days: R^2 = {b_R2_values[i]:.4f}")

        return np.array(b_values), np.array(b_R2_values)

    def perform_inversion(self, a_values, b_values, periods_days, verbose=True):
        """Invert for kappa_e and v_t for given a, b, and periods (days).
        Returns (kappa_e, v_t)
        """
        a = np.asarray(a_values, float)
        b = np.asarray(b_values, float)
        P = np.asarray(periods_days, float) * 86400.0
        kappa_e = (np.pi * 2.0 * a) / (P * b * (b**2 + a**2))
        v_t = kappa_e * (b**2 - a**2) / a
        print("Inversion complete.")

        if verbose:
            for i, Pd in enumerate(periods_days):
                print(f"Period {Pd:.2f} days: kappa_e = {kappa_e[i]:.3e} m^2/s, v_t = {v_t[i]:.3e} m/s")

        return kappa_e, v_t
    
    def check_constantes(self, a_values, b_values):
        rapport = (b_values**2 - a_values**2)/a_values
        print("Verification des constantes")
        print(rapport)
        return None
    

    # def reconstruct_signal(self, signals, a_values, b_values, periods_days, depths, verbose=True):
    #     """Attempting to reconstruct the signal given the river and the spectral components."""
    #     """A FAIRE !"""


if __name__ == "__main__":
    # Exemple.
    # --- Paramètres de la simulation ---

    t_debut = (2011, 1, 1)
    t_fin = (2011, 2, 28, 23, 59, 59)
    dt = 15*NSECINMIN # pas de temps en (s)

    zeroT = 0
    zeroT += ZERO_CELSIUS 

    T_riv_amp = 1
    T_riv_offset = 12  + zeroT
    nday = 1
    P_T_riv = nday*NHOURINDAY*4*dt #monthly   period

    T_aq_amp = 0
    T_aq_offset = 12 + zeroT
    P_T_aq = -9999  

    dH_amp = 0
    dH_offset = .5
    P_dh = -9999 #14*24*4*dt

    depth_sensors = [.2, .4, .6, .8]
    Zbottom = .8

    """Bruit de mesure"""
    sigma_meas_P = 0.001
    sigma_meas_T = 0.1

    print("dt={0:.1f}s".format(dt))

    # --- Génération des données synthétiques ---

    # Création du signal multipériodique de la rivière.
    liste_params_river = [[T_riv_amp, P_T_riv, T_riv_offset], [T_riv_amp, P_T_riv/2, 0]]

    time_series_dict_user1 = {
    "offset":.0,
    "depth_sensors":depth_sensors,
	"param_time_dates": [t_debut, t_fin, dt], 
    "param_dH_signal": [dH_amp, P_dh, dH_offset], #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
	"param_T_riv_signal":liste_params_river, #list of list for multiperiodic signal
    "param_T_aq_signal": [T_aq_amp, P_T_aq, T_aq_offset],
    "sigma_meas_P": sigma_meas_P,
    "sigma_meas_T": sigma_meas_T, #float
    }
    # instanciation du simulateur de données
    emu_observ_test_user1 = synthetic_MOLONARI.from_dict(time_series_dict_user1)

    # l'utilisateur génère un dictionnaire avec les données importantes de la colonne
    Couche = {
        "name": "Couche en sable",
        "zLow": Zbottom,
        "moinslog10IntrinK":11,
        "n": 0.1,
        "lambda_s": 1,
        "rhos_cs": 4e6,
        "q_s": 1e-20,
    }

    # modèle une couche
    Layer1 = Layer.from_dict(Couche)

    print(f"Layer: {Layer1}")

    nbcells = 100
    # on utilise les mesures générées précédemment dans les init "dH_measures" et "T_measures"
    col_dict = {
        "river_bed": 1.0, 
        "depth_sensors": depth_sensors, #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
        "offset": .0,
        "dH_measures": emu_observ_test_user1._molonariP_data,
        "T_measures": emu_observ_test_user1._T_Shaft_measures,
        "nb_cells" : nbcells,
        "sigma_meas_P": 0.01, #float
        "sigma_meas_T": 0.1, #float
    }
    col = Column.from_dict(col_dict,verbose=True)
    col.set_layers(Layer1)
    col.compute_solve_transi()

    emu_observ_test_user1._measures_column_one_layer(col)

    # Now find the dominant periods in the river signal
    fa = frequentiel_analysis()
    dates = emu_observ_test_user1._dates
    river = emu_observ_test_user1._T_riv
    temps_all = col.get_temperature_at_sensors()
    # temps_all shape: (n_sensors + 2, n_time) -> [0]=river, [1..n]=sensors, [-1]=aq
    sensors = temps_all[1:-1]
    signals = [river] + [sensors[i, :] for i in range(sensors.shape[0])]

    # Take the 3 first values and add 0 
    depth_sensors = col.depth_sensors[:3]
    depth_sensors = [0] + depth_sensors

    # Plotting check figures
    fa.fft_sensors(dates, signals, depth_sensors)
    fa.plot_temperatures(dates, signals, depth_sensors)

    # Finding dominant periods
    dominant_periods_days, dominant_freqs, dominant_amps = fa.find_dominant_periods(signals, river, draw=True)

    # Estimate a and b for these dominant periods
    depths = np.array(depth_sensors)
    a_est, a_R2 = fa.estimate_a(dates, signals, depths, dominant_periods_days, verbose=True, draw=True)
    b_est, b_R2 = fa.estimate_b(dates, signals, depths, dominant_periods_days, verbose=True, draw=True)

    # Checking constants
    fa.check_constantes(a_est, b_est)

    kappa_e, v_t = fa.perform_inversion(a_est, b_est, dominant_periods_days, verbose=True)
