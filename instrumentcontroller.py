from os.path import isfile
from collections import defaultdict

from PyQt5.QtCore import QObject, pyqtSlot

from arduino.programmerfactory import ProgrammerFactory
from instr.instrumentfactory import NetworkAnalyzerFactory


class MeasureResult:
    def __init__(self):
        self.headers = list()
    def init(self):
        raise NotImplementedError()
    def process_raw_data(self, *args, **kwargs):
        raise NotImplementedError()


class MeasureResultMock(MeasureResult):
    def __init__(self, device, secondary):
        super().__init__()
        self.devices: list = list(device.keys())
        self.secondary: dict = secondary

        self.headersCache = dict()
        self._generators = defaultdict(list)
        self.data = list()

    def init(self):
        self.headersCache.clear()
        self._generators.clear()
        self.data.clear()
        return True


class InstrumentController(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.requiredInstruments = {
            'Анализатор': NetworkAnalyzerFactory('GPIB2::18::INSTR'),
            'Программатор': ProgrammerFactory('COM5')
        }

        self.deviceParams = {
            'Цифровой фазовращатель': {
                'F': [1.15, 1.35, 1.75, 1.92, 2.25, 2.54, 2.7, 3, 3.47, 3.86, 4.25],
                'mul': 2,
                'P1': 15,
                'P2': 21,
                'Istat': [None, None, None],
                'Idyn': [None, None, None]
            },
        }

        if isfile('./params.ini'):
            import ast
            with open('./params.ini', 'rt', encoding='utf-8') as f:
                raw = ''.join(f.readlines())
                self.deviceParams = ast.literal_eval(raw)

        self.secondaryParams = {'F': 1.0, 'dF': 0.1, 'Pmin': 10.0, 'Pmax': 20.0, 'dP1': 1.0, 'dP2': 1.0}

        self.span = 0.1

        self._instruments = dict()
        self.found = False
        self.present = False
        self.hasResult = False

        # self.result = MeasureResult() if not mock_enabled \
        #     else MeasureResultMock(self.deviceParams, self.secondaryParams)
        self.result = MeasureResultMock(self.deviceParams, self.secondaryParams)

    def __str__(self):
        return f'{self._instruments}'

    def connect(self, addrs):
        print(f'searching for {addrs}')
        for k, v in addrs.items():
            self.requiredInstruments[k].addr = v
        self.found = self._find()

    def _find(self):
        self._instruments = {
            k: v.find() for k, v in self.requiredInstruments.items()
        }
        return all(self._instruments.values())

    def check(self, params):
        print(f'call check with {params}')
        device, secondary = params
        self.present = self._check(device, secondary)
        print('sample pass')

    def _check(self, device, secondary):
        print(f'launch check with {self.deviceParams[device]} {self.secondaryParams}')
        return self.result.init() and self._runCheck(self.deviceParams[device], self.secondaryParams)

    def _runCheck(self, param, secondary):
        print(f'run check with {param}, {secondary}')
        return True

    def measure(self, params):
        print(f'call measure with {params}')
        device, secondary = params
        raw_data = self._measure(device, secondary)
        self.hasResult = bool(raw_data)

        if self.hasResult:
            self._export_to_xlsx(raw_data)

    def _measure(self, device, secondary):
        param = self.deviceParams[device]
        secondary = self.secondaryParams
        print(f'launch measure with {param} {secondary}')

        self._instruments['Генератор 1'].set_modulation(state='OFF')
        self._instruments['Генератор 2'].set_modulation(state='OFF')
        self._instruments['Анализатор'].set_autocalibrate(state='OFF')
        self._instruments['Анализатор'].set_span(value=self.span, unit='MHz')
        self._instruments['Анализатор'].set_marker_mode(marker=1, mode='POS')

        freqs = [1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
        pows = [param['P1'] + 0.5 * i for i in range(int((secondary['Pmax'] - secondary['Pmin']) / 0.5))]
        dF = secondary['dF']

        result = list()
        for freq in freqs:
            self._instruments['Генератор 1'].set_freq(value=freq, unit='GHz')
            self._instruments['Генератор 2'].set_freq(value=freq, unit='GHz')
            for pow in pows:
                self._instruments['Генератор 1'].set_pow(value=pow + secondary['dP1'], unit='dBm')
                self._instruments['Генератор 2'].set_pow(value=pow + secondary['dP2'], unit='dBm')
                temp = list()
                analyzer_freqs = [freq, freq - dF, freq + dF, freq + 2 * dF]
                for measure_freq in analyzer_freqs:
                    self._instruments['Анализатор'].set_measure_center_freq(value=measure_freq, unit='GHz')
                    temp.append(self._instruments['Анализатор'].read_pow(marker=1))
                result.append(temp)

        return result

    def _export_to_xlsx(self, result):
        print('exporting result')
        # xslx_result(result)
        # xlsx_result.save('out.xlsx')

    @pyqtSlot(dict)
    def on_secondary_changed(self, params):
        self.secondaryParams = params

    @property
    def status(self):
        return [i.status for i in self._instruments.values()]

