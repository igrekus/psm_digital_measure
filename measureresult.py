def calc_vswr(in_mags: list):
    module = [abs(x) for x in in_mags]
    plus = (1 + x for x in module)
    minus = (1 - x for x in module)
    return list(p / m for p, m in zip(plus, minus))


class MeasureResult:

    def __init__(self, ):
        self.headers = list()
        self._freqs = list()
        self._s21s = list()
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
        self._s11s.clear()
        self._s22s.clear()
        self._states.clear()

        self._vswr_in.clear()
        self._vswr_out.clear()

    def _process(self):
        self._calc_vwsr_in()
        self._calc_vwsr_out()
        self.ready = True

    def _calc_vwsr_in(self):
        self._vswr_in = [calc_vswr(s) for s in self._s11s]

    def _calc_vwsr_out(self):
        self._vswr_out = [calc_vswr(s) for s in self._s22s]

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
