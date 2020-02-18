import datetime
import time

from os.path import isfile
from PyQt5.QtCore import QObject, pyqtSlot

from arduino.programmerfactory import ProgrammerFactory
from instr.instrumentfactory import NetworkAnalyzerFactory, mock_enabled
from measureresult import MeasureResult


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
            'Анализатор': NetworkAnalyzerFactory('GPIB0::9::INSTR'),
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
        self.sweep_points = 51

        self._instruments = dict()
        self.found = False
        self.present = False
        self.hasResult = False

        self.result = MeasureResult()

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
        return self._runCheck(self.deviceParams[device], self.secondaryParams)

    def _runCheck(self, param, secondary):
        print(f'run check with {param}, {secondary}')
        return True

    def measure(self, params):
        print(f'call measure with {params}')
        device, secondary = params
        res = self._measure(device, secondary)
        self.result.raw_data = self.sweep_points, res, self._phase_values
        self.hasResult = bool(self.result)

    def _measure(self, device, secondary):
        param = self.deviceParams[device]
        secondary = self.secondaryParams
        print(f'launch measure with {param} {secondary}')

        self._clear()
        self._init(secondary)

        return self._measure_s_params()

    def _clear(self):
        self._phase_values.clear()

    def _init(self, params):
        pna = self._instruments['Анализатор']
        prog = self._instruments['Программатор']
#
        pna.send('SYST:PRES')
        pna.query('*OPC?')
        # pna.send('CALC:PAR:DEL:ALL')

        pna.send('CALC1:PAR:DEF "CH1_S21",S21')

        # c:\program files\agilent\newtowrk analyzer\UserCalSets
        # TODO calibration
        # pna.send('SENS1:CORR:CSET:ACT "-20dBm_1.1-1.4G",1')
        # pna.send('SENS2:CORR:CSET:ACT "-20dBm_1.1-1.4G",1')

        pna.send(f'SENS1:SWE:POIN {self.sweep_points}')

        pna.send(f'SENS1:FREQ:STAR {params["F1"]}GHz')
        pna.send(f'SENS1:FREQ:STOP {params["F2"]}GHz')

        pna.send('SENS1:SWE:MODE CONT')
        pna.send(f'FORM:DATA ASCII')

        prog.set_lpf_code(0)

    def _measure_s_params(self):
        pna = self._instruments['Анализатор']
        prog = self._instruments['Программатор']

        out = []
        for state in [v for i, v in enumerate(self.states.values()) if i in [0, 1, 2, 4, 8, 16, 32, 63]]:
            self._phase_values.append(self._phase_for_state(state))

            prog.set_lpf_code(state)

            if not mock_enabled:
                time.sleep(0.4)

            pna.send(f'CALC1:PAR:SEL "CH1_S21"')
            pna.query('*OPC?')
            # res = pna.query(f'CALC1:DATA:SNP? 2')
            out.append(parse_float_list(res))

            if not mock_enabled:
                time.sleep(0.4)
        return out

    def _phase_for_state(self, pattern):
        # TODO calculate phase by bit pattern
        # return sum([ph * pt for ph, pt in zip(self.phases, pattern)])
        return pattern

    def pow_sweep(self):
        print('pow sweep')
        return [4, 5, 6], [4, 5, 6]

    @pyqtSlot(dict)
    def on_secondary_changed(self, params):
        self.secondaryParams = params

    @property
    def status(self):
        return [i.status for i in self._instruments.values()]


def parse_float_list(lst):
    return [float(x) for x in lst.split(',')]
