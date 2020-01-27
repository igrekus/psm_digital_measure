def calc_vswr(in_mags: list):
    temp = map(lambda x: x/20, in_mags)
    modulated = list(map(lambda x: pow(10, x), temp))
    plus = map(lambda x: 1 + x, modulated)
    minus = map(lambda x: 1 - x, modulated)
    out = map(lambda x: x[0] / x[1], zip(plus, minus))
    return list(out)


def find_freq_index(freqs: list, threshold):
    df = freqs[1] - freqs[0]
    return next((i for i, f in enumerate(freqs) if (threshold - df) < f < (threshold + df)), 0)


def pts_stats(gamma_inp, ind_dn_frq, ind_up_frq):
    eps = 1e-1
    threshold = 1.5
    return [[1 for g in gamma[ind_dn_frq:ind_up_frq + 1] if g > threshold + eps] for gamma in gamma_inp]


class MeasureResult:

    def __init__(self, ):
        self.headers = list()
        self._freqs = list()
        self._mag_s21s = list()
        self._phs_s21s = list()
        self._mag_s11s = list()
        self._mag_s22s = list()
        self._states = list()

        self._gamma_input = list()
        self._gamma_output = list()
        self._phases = list()
        self._phase_errs = list()

        self._low_threshold = 1.21e9
        self._high_threshold = 1.31e9
        self._low_index = 0
        self._high_index = 0

        self._s21_maxs = list()
        self._s21_mins = list()
        self._s21_deltas = list()

        self._delta_Kp = 0.0
        self._s21_MAX = 0.0
        self._s21_MIN = 0.0
        self._avg_Kp = 0.0

        self._swr_in_max = 0
        self._swr_out_max = 0
        self._phase_err_max = 0
        self._phase_err_min = 0

        self._s21_max_in_range = 0
        self._s21_delta_max = 0

        self._ref_pnt_inp = list()
        self._ref_pnt_outp = list()

        self._summ_inp = list()
        self._summ_outp = list()

        self.ready = False
        self._raw_data_set = dict()
        self._data_set = dict()

    def init(self):
        return True

    def process(self):
        self._freqs = self._freqs[:151]
        self._mag_s21s = [m[:151] for m in self._mag_s21s]
        self._phs_s21s = [m[:151] for m in self._phs_s21s]
        self._mag_s11s = [m[:151] for m in self._mag_s11s]
        self._mag_s22s = [m[:151] for m in self._mag_s22s]

        self._calc_gammas()
        self._calc_phases()
        self._find_freqs()
        self._calc_limits()
        self._calc_out_params()
        self._calc_ref_points()
        self._calc_out_stats()
        self._data_set = {state: dataset for state, dataset in zip(self._states, zip(self._mag_s21s, self._gamma_input, self._gamma_output, self._phases, self._phase_errs))}
        self.ready = True

    def invalidate(self):
        self._clear()
        self._raw_data_set.clear()
        self._data_set.clear()
        self.ready = False

    def _clear(self):
        self._freqs.clear()
        self._mag_s21s.clear()
        self._phs_s21s.clear()
        self._mag_s11s.clear()
        self._mag_s22s.clear()
        self._states.clear()

        self._gamma_input.clear()
        self._gamma_output.clear()
        self._phases.clear()
        self._phase_errs.clear()

        self._low_index = 0
        self._high_index = 0

        self._s21_maxs.clear()
        self._s21_mins.clear()
        self._s21_deltas.clear()

        self._delta_Kp = 0.0
        self._s21_MAX = 0.0
        self._s21_MIN = 0.0
        self._avg_Kp = 0.0

        self._swr_in_max = 0
        self._swr_out_max = 0
        self._phase_err_max = 0
        self._phase_err_min = 0

        self._s21_max_in_range = 0
        self._s21_delta_max = 0

        self._ref_pnt_inp.clear()
        self._ref_pnt_outp.clear()

        self._summ_inp = 0
        self._summ_outp = 0

    def _calc_gammas(self):
        self._gamma_input = [calc_vswr(mags) for mags in self._mag_s11s]
        self._gamma_output = [calc_vswr(mags) for mags in self._mag_s22s]

    def _calc_phases(self):
        zeros = self._phs_s21s[0]

        for phases in self._phs_s21s[1:]:
            print(phases)
            tmp_list = list()
            for p, z in zip(phases, zeros):
                if p - z < 0:
                    tmp_list.append(p - z)
                else:
                    tmp_list.append(p - z - 360)
            self._phases.append(tmp_list)

        for phases, state in zip(self._phases, self._states[1:]):
            self._phase_errs.append([p + state for p in phases])

    def _find_freqs(self):
        self._low_index = find_freq_index(self._freqs, threshold=self._low_threshold)
        self._high_index = find_freq_index(self._freqs, threshold=self._high_threshold)

    def _calc_limits(self):
        for i, data in enumerate(self._mag_s21s):
            temp = data[self._low_index:self._high_index + 1]
            mx, mn = max(temp), min(temp)
            s21_delta = mx - mn
            self._s21_maxs.append(mx)
            self._s21_mins.append(mn)
            self._s21_deltas.append(s21_delta)

            print('\nphase=', self._states[i])
            print('s21_max=', mx)
            print('s21_min=', mn)
            print('delta_s21=', s21_delta)

    def _calc_out_params(self):
        self._s21_MAX = max(self._s21_maxs)
        self._s21_MIN = min(self._s21_mins)
        self._delta_Kp = abs(self._s21_MAX) - abs(self._s21_MIN)
        self._avg_Kp = (self._s21_MAX + self._s21_MIN) / 2

    def _calc_ref_points(self):
        self._ref_pnt_inp = pts_stats(self._gamma_input, self._low_index, self._high_index)
        self._ref_pnt_outp = pts_stats(self._gamma_output, self._low_index, self._high_index)

    def _calc_out_stats(self):
        self._summ_inp = sum([sum(pts) for pts in self._ref_pnt_inp])
        self._summ_outp = sum([sum(pts) for pts in self._ref_pnt_outp])

        self._swr_in_max = max([max(gm[self._low_index:self._high_index]) for gm in self._gamma_input])
        self._swr_out_max = max([max(gm[self._low_index:self._high_index]) for gm in self._gamma_output])

        self._phase_err_max = max([max(pe[self._low_index:self._high_index]) for pe in self._phase_errs])
        self._phase_err_min = min([min(pe[self._low_index:self._high_index]) for pe in self._phase_errs])

        self._s21_max_in_range = max([max(gm[self._low_index:self._high_index]) for gm in self._mag_s21s])

        self._s21_delta_max = max(self._s21_deltas)

    def __bool__(self):
        return self.ready

    @property
    def raw_data(self):
        return self._freqs, self._mag_s21s, self._phs_s21s, self._mag_s11s, self._mag_s22s, self._states

    @raw_data.setter
    def raw_data(self, args):
        self._freqs, self._mag_s21s, self._phs_s21s, self._mag_s11s, self._mag_s22s, self._states = args
        self._raw_data_set = {state: dataset for state, dataset in zip(self._states, zip(self._mag_s21s, self._phs_s21s, self._mag_s11s, self._mag_s22s))}

    @property
    def freqs(self):
        return self._freqs

    @property
    def raw_datasets(self):
        return self._raw_data_set

    @property
    def datasets(self):
        return self._data_set

    @property
    def swr_out(self):
        return self._gamma_output

    @property
    def swr_in(self):
        return self._gamma_input

    @property
    def phase(self):
        return self._phases

    @property
    def phase_err(self):
        return self._phase_errs
