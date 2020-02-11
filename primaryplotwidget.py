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


class PrimaryPlotWidget(QWidget):

    startMeasure = pyqtSignal()
    exportResult = pyqtSignal()

    def __init__(self, parent=None, result=None):
        super().__init__(parent=parent)

        self._ui = uic.loadUi('primaryplotwidget.ui', self)
        self._result = result

        self._plotFreq = PlotWidget(self)
        self._ui.plotGrid.addWidget(self._plotFreq, 0, 0)
        self._plotFreq.axes_titles = 'Ctrl voltage, V', 'Freq, MHz'

        self._plotKvco = PlotWidget(self)
        self._ui.plotGrid.addWidget(self._plotKvco, 0, 1)
        self._plotKvco.axes_titles = 'Ctrl voltage, V', 'Kvco, MHz/V'

        self._plotSupply1Current = PlotWidget(self)
        self._ui.plotGrid.addWidget(self._plotSupply1Current, 1, 0)
        self._plotSupply1Current.axes_titles = 'Ctrl voltage, V', 'Src current, mA'

        self._plotPower = PlotWidget(self)
        self._ui.plotGrid.addWidget(self._plotPower, 1, 1)
        self._plotPower.axes_titles = 'Ctrl voltage, V', 'Pow, dBm'

        self._plotPushing = PlotWidget(self)
        self._ui.plotGrid.addWidget(self._plotPushing, 2, 0)
        self._plotPushing.axes_titles = 'Ctrl voltage, V', 'Pushing, Mhz/V'

        self._ready = False

    def plotResult(self, result):
        self._plotFreq.plot(xs=result.tune_voltage, ys=result.frequency)
        self._plotKvco.plot(xs=result.tune_voltage, ys=result.kvco)
        self._plotSupply1Current.plot(xs=result.tune_voltage, ys=result.supply_current)
        self._plotPower.plot(xs=result.tune_voltage, ys=result.power)
        self._plotPushing.plot(xs=result.tune_voltage, ys=result.pushing)
        self._plotPhaseNoise.plot(xs=result.tune_voltage, ys=result.noise)

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
