import numpy as np
import matplotlib.pyplot as plt
from pyheatmy.synthetic_MOLONARI import *
from pyheatmy.config import *
from pyheatmy.utils import create_periodic_signal


# à mettre dans utils (?)
def two_column_array(a1, a2):
    assert len(a1) == len(a2), "t and T must have the same length"
    return np.array([a1, a2])


class time_series_multiperiodic:
    def __init__(self, type):
        assert type in [
            "ts",
            "multi_periodic",
        ], "type must be either ts or multi_periodic"
        self.type = type

    def values_time_series(self, t, T):
        if self.type == "ts":
            self.time_series = two_column_array(t, T)
        else:
            return "This is not a time series"

    def create_multiperiodic_signal(
        self, amplitude, periods, dates, dt, offset=DEFAULT_T_riv_offset, verbose=True
    ):
        if self.type == "multi_periodic":
            assert len(amplitude) == len(
                periods
            ), "amplitude and periods must have the same length"
            if verbose:
                print(
                    "Creating a multi-periodic signal, with the following period:",
                    periods,
                    "and the following amplitude:",
                    amplitude,
                )
            for i in range(len(periods)):
                periods[i] = convert_period_in_second(periods[i][0], periods[i][1])
                if verbose :
                    print("periods :", periods)
            T = create_periodic_signal(
                dates,
                dt,
                [amplitude[0], periods[0], offset],
                signal_name="TBD",
                verbose=False,
            )

            for i in range(1, len(amplitude)):
                T += create_periodic_signal(
                    dates,
                    dt,
                    [amplitude[i], periods[i], 0],
                    signal_name="TBD",
                    verbose=False,
                )
            self.multi_periodic = two_column_array(dates, T)
        else:
            return "This is not a multi-periodic type"

    def plot(self, time_unit="s"):
        if self.type == "multi_periodic":
            a = self.multi_periodic
        if self.type == "ts":
            a = self.time_series
        assert a.ndim == 2 and len(a[0]) == len(a[1]), "a must be a n * 2 array"
        assert type(time_unit) == str, "time_unit must be of type str"

        plt.plot(a[0], a[1])
        plt.title("Temperature profile")
        plt.xlabel("date")
        plt.ylabel("temperature : °C")
        plt.show()


# testing
if __name__ == "__main__":
    from datetime import datetime, timedelta

    timestamp = 1485714600
    date_0 = datetime.fromtimestamp(timestamp)
    step = timedelta(days=2, hours=3)
    dates = [date_0 + i * step for i in range(1000)]

    mp_ts = time_series_multiperiodic("multi_periodic")
    mp_ts.create_multiperiodic_signal(
        [10, 5, 3], [[1, "y"], [2, "m"], [21, "d"]], dates, dt=2 * NSECINDAY + 3 * NSECINHOUR
    )
    mp_ts.plot()
