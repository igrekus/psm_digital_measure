import itertools

from PyQt5 import uic
from PyQt5.QtChart import QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QPointF, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget


class PlotWidget(QChartView):

    def __init__(self, parent=None, xrange=(0, 10), yrange=(0, 10), ticks=5):
        super().__init__(parent=parent)

        self.setRenderHint(QPainter.Antialiasing)

        self._chart = self.chart()
        self._axis_x = QValueAxis()
        self._axis_y = QValueAxis()

        self._chart.addAxis(self._axis_x, Qt.AlignBottom)
        self._chart.addAxis(self._axis_y, Qt.AlignLeft)

        self._axis_x.setTickCount(ticks)
        self._axis_x.setRange(*xrange)

        self._axis_y.setTickCount(ticks)
        self._axis_y.setRange(*yrange)

        self._chart.legend().hide()

    def plot(self, xs_arr, ys_arr):
        self._chart.removeAllSeries()
        for xs, ys in zip(xs_arr, ys_arr):
            series = QLineSeries(self)
            series.attachAxis(self._axis_x)
            series.attachAxis(self._axis_y)
            series.replace([QPointF(x, y) for x, y in zip(xs, ys)])
            self._chart.addSeries(series)

    @property
    def axes_titles(self):
        return self._axis_x.titleText(), self._axis_y.titleText()

    @axes_titles.setter
    def axes_titles(self, value):
        x, y = value
        self._axis_x.setTitleText(x)
        self._axis_y.setTitleText(y)

    @property
    def title(self):
        return self._chart.title()

    @title.setter
    def title(self, value):
        self._chart.setTitle(value)

    @property
    def legend(self):
        return self._chart.legend()

    def setXRange(self, *args):
        self._axis_x.setRange(*args)

    def setYRange(self, *args):
        self._axis_y.setRange(*args)


class PrimaryPlotWidget(QWidget):

    startMeasure = pyqtSignal()
    exportResult = pyqtSignal()

    def __init__(self, parent=None, result=None):
        super().__init__(parent=parent)

        self._ui = uic.loadUi('primaryplotwidget.ui', self)
        self._result = result

        self._plotS21 = PlotWidget(self, (0, 8), (-10, 10), 5)
        self._ui.plotGrid.addWidget(self._plotS21, 0, 0)
        self._plotS21.axes_titles = 'F, ГГц', 'S21, дБм'

        self._plotVswrIn = PlotWidget(self, (0, 8), (-10, 10), 5)
        self._ui.plotGrid.addWidget(self._plotVswrIn, 0, 1)
        self._plotVswrIn.axes_titles = 'F, ГГц', 'КСВ вх, дБм'

        self._plotVswrOut = PlotWidget(self, (0, 8), (-10, 10), 5)
        self._ui.plotGrid.addWidget(self._plotVswrOut, 1, 0)
        self._plotVswrOut.axes_titles = 'F, ГГц', 'КСВ вых, дБм'

        self._plotS21PhaseErr = PlotWidget(self)
        self._ui.plotGrid.addWidget(self._plotS21PhaseErr, 1, 1)
        self._plotS21PhaseErr.axes_titles = 'F, ГГц', 'φ ош, град'

        self._plotS21PhaseRmse = PlotWidget(self, (0, 8), (-10, 10), 5)
        self._ui.plotGrid.addWidget(self._plotS21PhaseRmse, 0, 2)
        self._plotS21PhaseRmse.axes_titles = 'F, ГГц', 'φ ско'

        self._plotS21Err = PlotWidget(self, (0, 8), (-10, 10), 5)
        self._ui.plotGrid.addWidget(self._plotS21Err, 1, 2)
        self._plotS21Err.axes_titles = 'F, ГГц', 'S21 ош, дБ'

        self._plotS21Rmse = PlotWidget(self, (0, 8), (-10, 10), 5)
        self._ui.plotGrid.addWidget(self._plotS21Rmse, 0, 3)
        self._plotS21Rmse.axes_titles = 'F, ГГц', 'S21 ско'

        self._ready = False

    def preparePlots(self, params):
        f1 = params['F1']
        f2 = params['F2']
        self._plotS21.setXRange(f1, f2)
        self._plotVswrIn.setXRange(f1, f2)
        self._plotVswrOut.setXRange(f1, f2)

    def plot(self):
        s21s = self._result.s21
        freqs = self._result.freqs
        vswr_in = self._result.vswr_in
        vswr_out = self._result.vswr_out
        phase_errs = self._result.phase_err
        phase_rmse = self._result.phase_rmse
        s21_err = self._result.s21_err
        s21_rmse = self._result.s21_rmse
        n = len(s21s)

        self._plotS21.setYRange(min(min(s) for s in s21s), max(max(s) for s in s21s))
        self._plotS21.plot(xs_arr=itertools.repeat(freqs, n), ys_arr=s21s)

        self._plotVswrIn.setYRange(min(min(s) for s in vswr_in), max(max(s) for s in vswr_in))
        self._plotVswrIn.plot(xs_arr=itertools.repeat(freqs, n), ys_arr=vswr_in)

        self._plotVswrOut.setYRange(min(min(s) for s in vswr_out), max(max(s) for s in vswr_out))
        self._plotVswrOut.plot(xs_arr=itertools.repeat(freqs, n), ys_arr=vswr_out)

        self._plotS21PhaseErr.setYRange(min(min(s) for s in phase_errs), max(max(s) for s in phase_errs))
        self._plotS21PhaseErr.plot(xs_arr=itertools.repeat(freqs, n - 1), ys_arr=phase_errs)

        self._plotS21PhaseRmse.setYRange(min(min(s) for s in phase_rmse), max(max(s) for s in phase_rmse))
        self._plotS21PhaseRmse.plot(xs_arr=itertools.repeat(freqs, n - 1), ys_arr=phase_rmse)

        self._plotS21Err.setYRange(min(min(s) for s in s21_err), max(max(s) for s in s21_err))
        self._plotS21Err.plot(xs_arr=itertools.repeat(freqs, n - 1), ys_arr=s21_err)

        self._plotS21Rmse.setYRange(min(min(s) for s in s21_rmse), max(max(s) for s in s21_rmse))
        self._plotS21Rmse.plot(xs_arr=itertools.repeat(freqs, n - 1), ys_arr=s21_rmse)

    # event handlers
    @pyqtSlot()
    def on_btnMeasure_clicked(self):
        self.startMeasure.emit()

    @pyqtSlot()
    def on_btnExport_clicked(self):
        self.exportResult.emit()

    @pyqtSlot(bool)
    def on_checkV1_toggled(self, value):
        self._params.v_sup1_on = value

    @pyqtSlot(bool)
    def on_checkV2_toggled(self, value):
        self._params.v_sup2_on = value

    @pyqtSlot(float)
    def on_spinV1_valueChanged(self, value):
        self._params.v_sup1 = value

    @pyqtSlot(float)
    def on_spinV2_valueChanged(self, value):
        self._params.v_sup2 = value

    @pyqtSlot(float)
    def on_spinDutVstart_valueChanged(self, value):
        self._params.v_dut_start = value

    @pyqtSlot(float)
    def on_spinDutVend_valueChanged(self, value):
        self._params.v_dut_end = value

    @pyqtSlot(float)
    def on_spinDutVstep_valueChanged(self, value):
        self._params.v_dut_step = value

    @pyqtSlot(float)
    def on_spinOffsetF1_valueChanged(self, value):
        self._params.f_offset1 = value * 1_000

    @pyqtSlot(float)
    def on_spinOffsetF2_valueChanged(self, value):
        self._params.f_offset2 = value * 1_000

    @pyqtSlot(float)
    def on_spinOffsetF3_valueChanged(self, value):
        self._params.f_offset3 = value * 1_000

    @pyqtSlot(float)
    def on_spinOffsetF4_valueChanged(self, value):
        self._params.f_offset4 = value * 1_000

    # props
    @property
    def ready(self):
        return self._ready

    @ready.setter
    def ready(self, value):
        self._ui.btnMeasure.setEnabled(value)
        self._ready = value

    @property
    def params(self):
        return self._params
