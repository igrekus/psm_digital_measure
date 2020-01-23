import time

from os.path import isfile
from PyQt5.QtCore import QObject, pyqtSlot

from arduino.programmerfactory import ProgrammerFactory
from instr.instrumentfactory import NetworkAnalyzerFactory
from measureresult import MeasureResult

is_mock = True


class InstrumentController(QObject):
    phases = [
        22.5,
        45.0,
        90.0,
        180.0
    ]

    states = {
        # i: f'{i:06b}' for i in range(64)
        i: i for i in range(64)
    }

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

        self.secondaryParams = {
            'Pin': -10,
            'F1': 4,
            'F2': 8,
            'State': 0
        }

        self.span = 0.1

        self._instruments = dict()
        self.found = False
        self.present = False
        self.hasResult = False

        # self.result = MeasureResult() if not mock_enabled \
        #     else MeasureResultMock(self.deviceParams, self.secondaryParams)
        self.result = MeasureResultMock(self.deviceParams, self.secondaryParams)

        self._freqs = list()
        self._mag_s11s = list()
        self._mag_s22s = list()
        self._mag_s21s = list()
        self._phs_s21s = list()
        self._phase_values = list()

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

        self._clear()
        self._init()

        self._freqs = parse_float_list(self.read_freqs(chan=1, parameter='CH1_S21'))

        self._measure_s_params()

        result = MeasureResult(self._freqs, self._mag_s11s, self._mag_s22s, self._mag_s21s, self._phs_s21s, self._phase_values)
        return result

    def _clear(self):
        self._freqs = list()
        self._mag_s11s = list()
        self._mag_s22s = list()
        self._mag_s21s = list()
        self._phs_s21s = list()
        self._phase_values = list()

    def _init(self):
        pna = self._instruments['Анализатор']
        prog = self._instruments['Программатор']

        pna.send('SYST:PRES')
        pna.query('*OPC?')
        pna.send('CALC:PAR:DEL:ALL')

        pna.send('DISP:WIND2 ON')

        pna.send('CALC1:PAR:DEF "CH1_S21",S21')
        pna.send('CALC2:PAR:DEF "CH2_S21",S21')
        pna.send('CALC1:PAR:DEF "CH1_S11",S11')
        pna.send('CALC1:PAR:DEF "CH1_S22",S22')

        # c:\program files\agilent\newtowrk analyzer\UserCalSets
        # TODO calibration
        # pna.send('SENS1:CORR:CSET:ACT "-20dBm_1.1-1.4G",1')
        # pna.send('SENS2:CORR:CSET:ACT "-20dBm_1.1-1.4G",1')

        # TODO point count
        # pna.send(f'SENS1:SWE:POIN 201')
        # pna.send(f'SENS2:SWE:POIN 201')

        pna.send('DISP:WIND1:TRAC1:FEED "CH1_S21"')
        pna.send('DISP:WIND2:TRAC1:FEED "CH2_S21"')
        pna.send('DISP:WIND1:TRAC2:FEED "CH1_S11"')
        pna.send('DISP:WIND1:TRAC3:FEED "CH1_S22"')

        pna.send('SENS1:SWE:MODE CONT')
        pna.send('SENS2:SWE:MODE CONT')

        pna.send('CALC1:FORM MLOG')
        pna.send('DISP:WIND1:TRAC1:Y:SCAL:AUTO')
        pna.send('CALC2:FORM UPH')
        pna.send('DISP:WIND2:TRAC1:Y:SCAL:AUTO')

        pna.send(f'FORM:DATA ASCII')

        prog.set_lpf_code(0)

    def _measure_s_params(self):
        prog = self._instruments['Программатор']

        for state in self.states.values():
            self._phase_values.append(self._phase_for_state(state))

            prog.set_lpf_code(state)

            if not is_mock:
                time.sleep(0.1)

            # TODO extract measurement class
            self._mag_s21s.append(parse_float_list(self.read_measurement(chan=1, parameter='CH1_S21')))
            self._phs_s21s.append(parse_float_list(self.read_measurement(chan=2, parameter='CH2_S21')))
            self._mag_s11s.append(parse_float_list(self.read_measurement(chan=1, parameter='CH1_S11')))
            self._mag_s22s.append(parse_float_list(self.read_measurement(chan=1, parameter='CH1_S22')))

            if not is_mock:
                time.sleep(0.1)

    def _phase_for_state(self, pattern):
        # TODO calculate phase by bit pattern
        # return sum([ph * pt for ph, pt in zip(self.phases, pattern)])
        return 42

    def read_measurement(self, chan=1, parameter=''):
        pna = self._instruments['Анализатор']
        pna.send(f'CALC{chan}:PAR:SEL "{parameter}"')
        pna.query('*OPC?')
        return pna.query(f'CALC{chan}:DATA? FDATA')

    def read_freqs(self, chan=1, parameter=''):
        pna = self._instruments['Анализатор']
        pna.send(f'CALC{chan}:PAR:SEL "{parameter}"')
        pna.query(f'*OPC?')
        return pna.query(f'SENS{chan}:X?')

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


def parse_float_list(lst):
    return [float(x) for x in lst.split(',')]
