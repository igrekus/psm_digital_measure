class MeasureResult:
    def __init__(self, freqs=None, mag_s11s=None, mag_s22s=None, mag_s21s=None, phs_s21s=None, phases=None):
        self.headers = list()
        self._freqs = freqs
        self._mag_s11s = mag_s11s
        self._mag_s22s = mag_s22s
        self._mag_s21s = mag_s21s
        self._phs_s21s = phs_s21s
        self._phase_values = phases

    def init(self):
        return True

    def process_raw_data(self, freqs=None, mag_s11s=None, mag_s22s=None, mag_s21s=None, phs_s21s=None, phases=None):
        self._freqs = freqs
        self._mag_s11s = mag_s11s
        self._mag_s22s = mag_s22s
        self._mag_s21s = mag_s21s
        self._phs_s21s = phs_s21s
        self._phase_values = phases

    @property
    def freqs(self):
        return self._freqs

    @property
    def mag_s21s(self):
        return self._mag_s21s

    @property
    def phs_s21s(self):
        return self._phs_s21s

    @property
    def mag_s11s(self):
        return self._mag_s11s

    @property
    def mag_s22s(self):
        return self._mag_s22s

    @property
    def phase_values(self):
        return self._phase_values

    @property
    def measurements(self):
        return self.freqs, self.mag_s21s, self.phs_s21s, self.mag_s11s, self.mag_s22s, self.phase_values
