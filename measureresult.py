import random
import statistics
import numpy as np

from ml_metrics import rmse


def calc_vswr(in_mags: list):
    temp = map(lambda x: x / 20, in_mags)
    modulated = list(map(lambda x: pow(10, x), temp))
    plus = map(lambda x: 1 + x, modulated)
    minus = map(lambda x: 1 - x, modulated)
    out = map(lambda x: x[0] / x[1], zip(plus, minus))
    return list(out)


def calc_error(array, zero):
    # TODO remove on prod
    # return [a - z + random.uniform(-0.5, 0.5) for a, z in zip(array, zero)]
    return [a - z + random.uniform(-0.1, 0.1) for a, z in zip(array, zero)]


def calc_rmse(array, zero):
    return [rmse(a, z) for a, z in zip(array, zero)]


# + 1) vswr for dB values for s11, s22

# TODO 3) calc unwrapped phase -> graph phase error Fn - F0 (raw phase - mean phase)
# TODO 4) phraph rms phase
# TODO 2) s21 amps -- raw - mean db -> rms for db

class MeasureResult:

    def __init__(self, ):
        self.headers = list()
        self._freqs = list()
        self._s21s = list()
        self._s21s_err = list()
        self._s21s_rmse = list()
        self._s21s_ph = list()
        self._s21s_ph_err = list()
        self._s21s_ph_rmse = list()
        self._s11s = list()
        self._s22s = list()
        self._states = list()

        self._vswr_in = list()
        self._vswr_out = list()

        self.ready = False

    def __bool__(self):
        return self.ready

    def _init(self):
        self._freqs.clear()
        self._s21s.clear()
        self._s21s_err.clear()
        self._s21s_rmse.clear()
        self._s21s_ph.clear()
        self._s21s_ph_err.clear()
        self._s21s_ph_rmse.clear()
        self._s11s.clear()
        self._s22s.clear()
        self._states.clear()

        self._vswr_in.clear()
        self._vswr_out.clear()

    def _process(self):
        self._calc_vwsr_in()
        self._calc_vwsr_out()
        self._calc_phase_err()
        self._calc_s21_err()
        self.ready = True

    def _calc_vwsr_in(self):
        self._vswr_in = [calc_vswr(s) for s in self._s11s]

    def _calc_vwsr_out(self):
        self._vswr_out = [calc_vswr(s) for s in self._s22s]

    def _calc_phase_err(self):
        self._s21s_ph = [np.unwrap(s, discont=np.rad2deg(np.pi)) for s in self._s21s_ph]
        ph0 = self._s21s_ph[0]
        self._s21s_ph_err = [calc_error(s, ph0) for s in self._s21s_ph[1:]]

        means = [statistics.mean(vs) for vs in zip(*self._s21s_ph_err)]
        self._s21s_ph_rmse = [calc_rmse(s, means) for s in self._s21s_ph[1:]]

    def _calc_s21_err(self):
        means = [statistics.mean(vs) for vs in zip(*self._s21s)]
        self._s21s_err = [calc_error(s, means) for s in self._s21s]

        self._s21s_rmse = [calc_rmse(s, means) for s in self._s21s]

        self._misc = [self._s21s_err[0]]


    @property
    def raw_data(self):
        return True

    @raw_data.setter
    def raw_data(self, args):
        print('process result')
        self._init()
        points, s2p, self._states = args

        for pars in s2p:
            for i in range(9):
                array = pars[i * points: i * points + points]
                if i == 0:
                    self._freqs = array
                elif i == 1:
                    self._s11s.append(array)
                elif i == 3:
                    self._s21s.append(array)
                elif i == 4:
                    self._s21s_ph.append(array)
                elif i == 7:
                    self._s22s.append(array)
        self._process()

    @property
    def freqs(self):
        return self._freqs

    @property
    def s21(self):
        return self._s21s

    @property
    def vswr_in(self):
        # TODO return actual VSWR
        return self._vswr_in

    @property
    def vswr_out(self):
        # TODO return actual VSWR
        return self._vswr_out

    @property
    def phase(self):
        return self._s21s_ph

    @property
    def phase_err(self):
        return self._s21s_ph_err

    @property
    def phase_rmse(self):
        return self._s21s_ph_rmse

    @property
    def s21_err(self):
        return self._s21s_err

    @property
    def s21_rmse(self):
        return self._s21s_rmse

    @property
    def misc(self):
        return self._misc
