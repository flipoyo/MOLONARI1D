import numpy as np
import matplotlib.pyplot as plt


# à mettre dans utils (?)
def two_column_array(a1, a2):
    assert len(a1) == len(a2), "t and T must have the same length"
    L = np.zeros(len(a1), 2)
    for i in range(len(t)):
        L[i, 0] = a1[i]
        L[i, 1] = a2[i]
    return L


class time_series_multiperiodic:
    def __init__(self, type):
        assert type in [
            "ts",
            "multi_periodic",
        ], "type must be either ts or multi_periodic"
        self.type = type

    if type == "ts":

        def values_time_series(self, t, T):
            self.time_series = two_column_array(t, T)

    if type == "multi_periodic":

        def create_multiperiodic_signal(
            self, amplitude, period, number_of_points, offset=12
        ):
            assert len(amplitude) == len(
                period
            ), "amplitude and period must have the same length"
            p_max = max(period)
            step = p_max / number_of_points
            t = np.array([i * step for i in range(number_of_points)])
            T = np.zeros(number_of_points)
            T += offset
            for i in range(len(amplitude)):
                T += amplitude[i] * np.sin(2 * np.pi / period[i] * t)
            self.multi_periodic = two_column_array(t, T)

    def plot(self, time_unit="s"):
        if self.type == "multi_periodic":
            a = self.multi_periodic
        if self.type == "ts":
            a = self.time_series
        assert a.ndim == 2 and len(a[0]) == len(a[1]), "a must be a n * 2 array"
        assert type(time_unit) == str, "time_unit musty be of type str"
        plt.plot(a[0], a[1])
        plt.title("Temperature profile")
        plt.xlabel("time" + str(time_unit))
        plt.ylabel("temperature °C")
        plt.show()


if __name__ == "__main__":
    mp_ts = time_series_multiperiodic("multi_periodic")
    mp_ts.create_multiperiodic_signal([1, 2, 3], [5, 2, 8], 1000)
    mp_ts.plot()
