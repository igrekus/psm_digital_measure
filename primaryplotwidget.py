import errno
import itertools
import os

from PyQt5.QtWidgets import QGridLayout, QWidget
from mytools.plotwidget import PlotWidget


class PrimaryPlotWidget(QWidget):

    params = {
        0: {
            '11': {
                'title': 'SWR in',
                'xlabel': 'F, GHz',
                'xlim': [1, 1.6],
                'ylabel': 'loss, dB',
                'ylim': []
            },
            '12': {
                'title': 'SWR out',
                'xlabel': 'F, GHz',
                'xlim': [1, 1.6],
                'ylabel': 'loss, dB',
                'ylim': []
            },
            '21': {
                'title': f'Phase',
                'xlabel': 'F, GHz',
                'xlim': [1, 1.6],
                'ylabel': 'phase, deg',
                'ylim': []
            },
            '22': {
                'title': 'Phase error',
                'xlabel': 'F, GHz',
                'xlim': [1, 1.6],
                'ylabel': 'Phase error, deg',
                'ylim': []
            }
        },
    }

    def __init__(self, parent=None, result=None):
        super().__init__(parent)

        self._result = result

        self._grid = QGridLayout()

        self._plot11 = PlotWidget(parent=None, toolbar=True)
        self._plot12 = PlotWidget(parent=None, toolbar=True)
        self._plot21 = PlotWidget(parent=None, toolbar=True)
        self._plot22 = PlotWidget(parent=None, toolbar=True)

        self._grid.addWidget(self._plot11, 0, 0)
        self._grid.addWidget(self._plot12, 0, 1)
        self._grid.addWidget(self._plot21, 1, 0)
        self._grid.addWidget(self._plot22, 1, 1)

        self.setLayout(self._grid)

        self._init()

    def _init(self, dev_id=0):

        def setup_plot(plot, pars: dict):
            # plot.set_tight_layout(True)
            plot.subplots_adjust(bottom=0.150)
            plot.set_title(pars['title'])
            plot.set_xlabel(pars['xlabel'], labelpad=-2)
            plot.set_ylabel(pars['ylabel'], labelpad=-2)
            plot.set_xlim(pars['xlim'][0], pars['xlim'][1])
            # plot.set_ylim(pars['ylim'][0], pars['ylim'][1])
            plot.grid(b=True, which='major', color='0.5', linestyle='-')
            plot.tight_layout()

        setup_plot(self._plot11, self.params[dev_id]['11'])
        setup_plot(self._plot12, self.params[dev_id]['12'])
        setup_plot(self._plot21, self.params[dev_id]['21'])
        setup_plot(self._plot22, self.params[dev_id]['22'])

    def clear(self):
        self._plot11.clear()
        self._plot12.clear()
        self._plot21.clear()
        self._plot22.clear()

    def plot(self, dev_id=0):
        self.clear()
        self._init(dev_id)
        self._result.process()

        print('plotting primary stats')

        swr_out = self._result.swr_out
        swr_in = self._result.swr_in
        phase = self._result.phase
        phase_err = self._result.phase_err

        freqs = [f / 1_000_000_000 for f in self._result.freqs]

        for sw_in, sw_out, ph, ph_e in zip(swr_in, swr_out, phase, phase_err):
            self._plot11.plot(freqs, sw_in)
            self._plot12.plot(freqs, sw_out)
            self._plot21.plot(freqs, ph)
            self._plot22.plot(freqs, ph_e)

        # for xs, ys in zip(self._domain.errorPerCodeXs, self._domain.errorPerCodeYs):
        #     self._plot12.plot(xs, ys)
        #
        # for xs, ys in zip(self._domain.inputInverseLossXs, self._domain.inputInverseLossYs):
        #     self._plot21.plot(xs, ys)
        #
        # for xs, ys in zip(self._domain.outputInverseLossXs, self._domain.outputInverseLossYs):
        #     self._plot22.plot(xs, ys)

    def save(self, img_path='./image'):
        try:
            os.makedirs(img_path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise IOError('Error creating image dir.')

        for plot, name in zip([self._plot11, self._plot12, self._plot21, self._plot22], ['stats.png', 'cutoff.png', 'delta.png', 'double-triple.png']):
            plot.savefig(img_path + name, dpi=400)


