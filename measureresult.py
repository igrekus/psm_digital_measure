def calc_vswr(in_mags: list):
    modulated = [abs(x) for x in in_mags]
    plus = (1 + x for x in modulated)
    minus = (1 - x for x in modulated)
    out = (p / m for p, m in zip(plus, minus))
    return list(out)


class MeasureResult:

    def __init__(self, ):
        self.headers = list()
        self._freqs = list()
        self._s21s = list()
        self._s11s = list()
        self._s22s = list()
        self._states = list()

        self.ready = False

    def _init(self):
        self._freqs.clear()
        self._s21s.clear()
        self._s11s.clear()
        self._s22s.clear()
        self._states.clear()

    def process(self):
        self.ready = True

    def __bool__(self):
        return self.ready

    @property
    def raw_data(self):
        return True

    @raw_data.setter
    def raw_data(self, args):
        self._init()
        s2p, self._states = args
        self._process()
