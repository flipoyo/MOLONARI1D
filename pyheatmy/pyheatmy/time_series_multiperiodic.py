import numpy as np
import matplotlib.pyplot as plt


# à mettre dans utils (?)
def two_column_array(a1, a2):
    assert len(a1) == len(a2), "t and T must have the same length"
    L = np.zeros((2, len(a1)))
    L[0] = a1
    L[1] = a2
    return L


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
        self, amplitude, period, time_step, offset=12, duration=0, verbose=True
    ):
        if self.type == "multi_periodic":
            assert len(amplitude) == len(
                period
            ), "amplitude and period must have the same length"
            if verbose:
                print(
                    "Creating a multi-periodic signal, with the following period:",
                    period,
                    "and the following amplitude:",
                    amplitude,
                )
            if duration == 0:
                duration = max(period) * 2
            number_of_points = int(duration // time_step)

            t = np.array([i * time_step for i in range(number_of_points)])
            T = np.zeros(number_of_points)
            T += offset
            for i in range(len(amplitude)):
                T += amplitude[i] * np.sin(2 * np.pi / period[i] * t)
            self.multi_periodic = two_column_array(t, T)
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
        plt.xlabel("time : " + str(time_unit))
        plt.ylabel("temperature : °C")
        plt.show()


# testing
if __name__ == "__main__":
    mp_ts = time_series_multiperiodic("multi_periodic")
    mp_ts.create_multiperiodic_signal([10, 8, 9], [5, 10, 7], 0.01)
    mp_ts.plot()
