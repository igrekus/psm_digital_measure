from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget

from mytools.plotwidget import PlotWidget


class PowSweepWidget(QWidget):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent)
        self._controller = controller

        self._ui = uic.loadUi('powsweepwidget.ui', self)

        self._plot = PlotWidget(parent=None, toolbar=True)
        self._ui.verticalLayout.addWidget(self._plot)

    @pyqtSlot
    def on_btnPowSweep_clicked(self):
        self._controller.pow_sweep()
