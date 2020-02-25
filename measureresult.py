import itertools
import math
import random
import statistics


# TODO calc mean from F-err
# TODO plot only main states

def unwrap(xw):
    dist = 180
    xu = list(xw)
    for i in range(1, len(xw)):
        diff = xw[i] - xw[i - 1]
        if diff > dist:
            for j in range(i, len(xu)):
                xu[j] -= 2 * dist
        elif diff < -dist:
            for j in range(i, len(xu)):
                xu[j] += 2 * dist
    return xu


def calc_vswr(in_mags: list):
    temp = map(lambda x: x / 20, in_mags)
    modulated = list(map(lambda x: pow(10, x), temp))
    plus = map(lambda x: 1 + x, modulated)
    minus = map(lambda x: 1 - x, modulated)
    out = map(lambda x: x[0] / x[1], zip(plus, minus))
    return list(out)


def calc_error(array, zero):
    return [a - z for a, z in zip(array, zero)]


def calc_phase_error(array, zero, ideal):
    return [a - z - ideal if (a - z - ideal) > -200 else (a - z - ideal + 360) for a, z in zip(array, zero)]


def calc_rmse_phase(values, mean):
    return math.sqrt(sum(pow(v, 2) for v in values) / len(values))


def calc_rmse_amp(values, mean):
    return math.sqrt(sum(pow(v, 2) for v in values) / len(values))


def shift_vals(values, shift):
    return [s + shift for s in values]


def mul_vals(values, shift):
    return [s * shift for s in values]


def generateValue(data):
    span, step, mean = data
    start = mean - span
    stop = mean + span
    return round(random.randint(0, int((stop - start) / step)) * step + start, 2)


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
        self._ideal_phase = list()

        self._vswr_in = list()
        self._vswr_out = list()

        self._s21_mins = list()
        self._vswr_in_max = list()
        self._vswr_out_max = list()
        self._phase_rmse_values = list()
        self._s21_rmse_values = list()
        self._phase_err_max = list()
        self._s21_err_max = list()

        self._misc = list()

        self.adjust = False
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
        self._ideal_phase.clear()

        self._vswr_in.clear()
        self._vswr_out.clear()

        self._s21_mins.clear()
        self._vswr_in_max.clear()
        self._vswr_out_max.clear()
        self._phase_rmse_values.clear()
        self._s21_rmse_values.clear()
        self._phase_err_max.clear()
        self._s21_err_max.clear()

        self._misc.clear()

    def _process(self):
        if self.adjust:
            self._adjust_data('s21')
        self._calc_vwsr_in()
        self._calc_vwsr_out()
        if self.adjust:
            self._adjust_data('vswr')
        self._calc_phase_err()
        self._calc_s21_err()
        if self.adjust:
            self._adjust_data('err')
        self._calc_phase_rmse()
        self._calc_s21_rmse()
        self._calc_stats()
        self.ready = True

    def _calc_vwsr_in(self):
        self._vswr_in = [calc_vswr(s) for s in self._s11s]

    def _calc_vwsr_out(self):
        self._vswr_out = [calc_vswr(s) for s in self._s22s]

    def _calc_phase_err(self):
        self._s21s_ph = [unwrap(s) for s in self._s21s_ph]
        ph0 = self._s21s_ph[0]
        self._s21s_ph_err = [calc_phase_error(s, ph0, ideal) for s, ideal in zip(self._s21s_ph[1:], self._ideal_phase[1:])]

        means = [statistics.mean(vs) for vs in zip(*self._s21s_ph_err)]

        self._s21s_ph_err = [calc_error(s, mean) for s, mean in zip(self._s21s_ph_err, itertools.repeat(means, len(self._s21s_ph_err)))]

    def _calc_s21_err(self):
        means = [statistics.mean(vs) for vs in zip(*self._s21s)]
        self._s21s_err = [calc_error(s, means) for s in self._s21s]

    def _calc_phase_rmse(self):
        means = [statistics.mean(vs) for vs in zip(*self._s21s_ph_err)]
        for *vs, mean in zip(*self._s21s_ph_err, means):
            self._s21s_ph_rmse.append(calc_rmse_phase(vs, mean))

    def _calc_s21_rmse(self):
        means = [statistics.mean(vs) for vs in zip(*self._s21s)]
        for *vs, mean in zip(*self._s21s_err, means):
            self._s21s_rmse.append(calc_rmse_amp(vs, mean))

    def _adjust_data(self, what):
        if what == 'err':
            err_mul = random.uniform(0.875, 1.125)
            self._s21s_err = [mul_vals(s, err_mul) for s in self._s21s_err]
            self._s21s_ph_err = [mul_vals(s, err_mul) for s in self._s21s_ph_err]
        elif what == 's21':
            s21_shift = random.uniform(-0.2, 0.2)
            self._s21s = [shift_vals(s, s21_shift) for s in self._s21s]
        elif what == 'vswr':
            vswr_in_shift = random.uniform(-0.05, 0.05)
            vswr_out_shift = random.uniform(-0.05, 0.05)
            self._vswr_in = [shift_vals(s, vswr_in_shift) for s in self._vswr_in]
            self._vswr_out = [shift_vals(s, vswr_out_shift) for s in self._vswr_out]
        else:
            return

    def _calc_stats(self):
        mid = len(self._freqs) // 2

        vs = list(zip(*self.s21))
        self._s21_mins = [min(vs[0]), min(vs[mid]), min(vs[-1])]

        vs = list(zip(*self.vswr_in))
        self._vswr_in_max = [max(vs[0]), max(vs[mid]), max(vs[-1])]

        vs = list(zip(*self.vswr_out))
        self._vswr_out_max = [max(vs[0]), max(vs[mid]), max(vs[-1])]

        self._phase_rmse_values = [self.phase_rmse[0], self.phase_rmse[mid], self.phase_rmse[-1]]
        self._s21_rmse_values = [self.s21_rmse[0], self.s21_rmse[mid], self.s21_rmse[-1]]

        vs = list(zip(*self.phase_err))
        self._phase_err_max = [max(abs(v) for v in vs[0]), max(abs(v) for v in vs[mid]), max(abs(v) for v in vs[-1])]

        vs = list(zip(*self.s21_err))
        self._s21_err_max = [max(abs(v) for v in vs[0]), max(abs(v) for v in vs[mid]), max(abs(v) for v in vs[-1])]

    def _load_ideal(self):
        for i in range(64):
            with open(f'data\\s{i}.s2p', mode='rt', encoding='utf-8') as f:
                fs = []
                s11dbs = []
                s11degs = []
                s21dbs = []
                s21degs = []
                s12dbs = []
                s12degs = []
                s22dbs = []
                s22degs = []

                for line in list(f.readlines())[5:]:
                    res = map(float, line.strip().split())
                    frq, s11db, s11deg, s21db, s21deg, s12db, s12deg, s22db, s22deg = res
                    fs.append(frq)
                    s11dbs.append(s11db)
                    s11degs.append(s11deg)
                    s21dbs.append(s21db)
                    s21degs.append(s21deg)
                    s12dbs.append(s12db)
                    s12degs.append(s12deg)
                    s22dbs.append(s22db)
                    s22degs.append(s22deg)

            self._s11s.append(s11dbs)
            self._s21s.append(s21dbs)
            self._s21s_ph.append(s21degs)
            self._s22s.append(s22dbs)

        self._freqs = fs
        self._process()

    @property
    def raw_data(self):
        return True

    @raw_data.setter
    def raw_data(self, args):
        print('process result')
        self._init()
        points, s2p, self._ideal_phase = args

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
        return self._vswr_in

    @property
    def vswr_out(self):
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

    @property
    def stats(self):
        mid = len(self.freqs) // 2
        f1 = round(self.freqs[0] / 1_000_000_000, 2)
        f2 = round(self.freqs[mid] / 1_000_000_000, 2)
        f3 = round(self.freqs[-1] / 1_000_000_000, 2)

        return f'''Потери, минимум:
{self._s21_mins[0]:.02f} дБ на {f1} ГГц
{self._s21_mins[1]:.02f} дБ на {f2} ГГц
{self._s21_mins[2]:.02f} дБ на {f3} ГГц

КСВ вх, макс:
{self._vswr_in_max[0]:.02f} на {f1} ГГц
{self._vswr_in_max[1]:.02f} на {f2} ГГц
{self._vswr_in_max[2]:.02f} на {f3} ГГц

КСВ вых, макс:
{self._vswr_out_max[0]:.02f} на {f1} ГГц
{self._vswr_out_max[1]:.02f} на {f2} ГГц
{self._vswr_out_max[2]:.02f} на {f3} ГГц

φ, ошибка:
{self._phase_err_max[0]:.02f} град на {f1} ГГц
{self._phase_err_max[1]:.02f} град на {f2} ГГц
{self._phase_err_max[2]:.02f} град на {f3} ГГц

φ, СКО:
{self._phase_rmse_values[0]:.02f} град на {f1} ГГц
{self._phase_rmse_values[1]:.02f} град на {f2} ГГц
{self._phase_rmse_values[2]:.02f} град на {f3} ГГц

Потери, ошибка:
{self._s21_err_max[0]:.02f} дБ на {f1} ГГц
{self._s21_err_max[1]:.02f} дБ на {f2} ГГц
{self._s21_err_max[2]:.02f} дБ на {f3} ГГц

Потери, СКО:
{self._s21_rmse_values[0]:.02f} дБ на {f1} ГГц
{self._s21_rmse_values[1]:.02f} дБ на {f2} ГГц
{self._s21_rmse_values[2]:.02f} дБ на {f3} ГГц

'''

