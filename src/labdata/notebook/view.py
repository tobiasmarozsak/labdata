import os
from os import PathLike
from pathlib import Path
import pprint
import sys

import numpy as np
import pandas as pd

if sys.platform == "win32":
    import ctypes
    import win32com.client
    import win32gui

import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets

from labdata import config
from labdata.load import list_file, load_file
from labdata.tools.mapping import ravel

try:
    from labdata.notebook import watch
except ImportError:
    watch = None

_VIEWERS = []


class _ComboBoxStyle(QtWidgets.QProxyStyle):
    """Keep the platform style but use a normal list instead of a menu popup."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QtWidgets.QStyle.StyleHint.SH_ComboBox_Popup:
            return 0
        return super().styleHint(hint, option, widget, returnData)


class _TablePrinter(pprint.PrettyPrinter):
    """Render NumPy scalars like their ordinary Python equivalents."""

    def format(self, obj, context, maxlevels, level):
        if isinstance(obj, np.generic):
            obj = obj.item()
        return super().format(obj, context, maxlevels, level)


_TABLE_PRINTER = _TablePrinter(sort_dicts=False, compact=True)


def _use_ipython_event_loop(app):
    """Let IPython own Qt's event loop instead of nesting QApplication.exec()."""
    try:
        from IPython import get_ipython

        shell = get_ipython()
        if shell is not None and getattr(shell, "kernel", None) is not None:
            shell.enable_gui("qt6")
            app.setQuitOnLastWindowClosed(False)
            return True
    except (ImportError, RuntimeError, ValueError):
        pass
    return False


def _activate_window(window):
    if sys.platform == "win32":
        win32com.client.Dispatch("WScript.Shell").SendKeys("%")
        handle = win32gui.FindWindow(None, window.windowTitle())
        if handle:
            win32gui.SetForegroundWindow(handle)

    window.raise_()
    window.activateWindow()
    window.wdgImageView.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
    handle = window.windowHandle()
    if handle is not None:
        handle.requestActivate()


def viewer(data, live=False):
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    uses_ipython_event_loop = _use_ipython_event_loop(app)
    if not uses_ipython_event_loop:
        app.setQuitOnLastWindowClosed(True)

    if live:
        window = LiveViewer()
    else:
        window = Viewer()
    window.update(data)
    window.show()
    _VIEWERS.append(window)
    window.destroyed.connect(lambda: _VIEWERS.remove(window) if window in _VIEWERS else None)
    QtCore.QTimer.singleShot(0, lambda: _activate_window(window))

    if not uses_ipython_event_loop:
        app.exec()


class Viewer(QtWidgets.QMainWindow):
    fileChanged = QtCore.pyqtSignal(list)

    title = "Viewer"

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        stylesheet = Path(config.VIEW_QSS).read_text(encoding="utf-8")
        self.setStyleSheet(stylesheet)

        self.init_gui()
        self.init_con()

        self.setWindowTitle(self.title)
        self.showMaximized()



    def init_gui(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()

        self.wdgDataInfo = WdgDataInfo()
        self.wdgImageInfo = WdgImageInfo()
        self.wdgDataView = WdgDataView()
        self.wdgImageView = WdgImageView()

        self.wdgSplitter = QtWidgets.QSplitter()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.wdgDataInfo)
        vbox.addWidget(self.wdgImageInfo)
        vbox.addWidget(self.wdgDataView)
        wdg = QtWidgets.QWidget()
        wdg.setObjectName("controlsPanel")
        wdg.setLayout(vbox)
        self.wdgSplitter.addWidget(wdg)

        self.wdgSplitter.addWidget(self.wdgImageView)

        self.wdgSplitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.wdgSplitter.setHandleWidth(1)
        self.setCentralWidget(self.wdgSplitter)
        self.wdgSplitter.setSizes([200, screen.width()-200])


    def init_con(self):
        self.wdgImageInfo.colorbarEnabled.connect(self.wdgImageView.enable_colorbar)
        self.wdgImageInfo.colorbarChanged.connect(self.wdgImageView.set_colorbar)
        self.wdgImageView.colorbarChanged.connect(self.wdgImageInfo.set_colorbar)

        self.wdgImageInfo.roiEnabled.connect(self.wdgImageView.enable_roi)
        self.wdgImageInfo.roiChanged.connect(self.wdgImageView.set_roi)
        self.wdgImageView.roiChanged.connect(self.wdgImageInfo.set_roi)

        self.wdgImageInfo.crosshairEnabled.connect(self.wdgImageView.enable_crosshair)
        self.wdgImageInfo.crosshairChanged.connect(self.wdgImageView.set_crosshair)
        self.wdgImageView.crosshairChanged.connect(self.wdgImageInfo.set_crosshair)

        self.wdgDataInfo.varChanged.connect(self.wdgDataView.update)
        self.wdgDataInfo.imgChanged.connect(self.wdgImageView.set_image)

    def update(self, data):
        self.wdgDataInfo.update(DataLoader(data))


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()


    def closeEvent(self, event):
        if sys.platform == "win32":
            ctypes.WinDLL("ole32.dll").OleFlushClipboard()



class LiveViewer(Viewer):

    title = "LiveViewer"

    def __init__(self):
        super().__init__()
        watch.connect(self.liveupdate, config.DATA_FOLDER)

    def liveupdate(self, event):
        path = os.path.dirname(os.path.normpath(event["dst"]))
        self.update(list_file(path))

    def closeEvent(self, event):
        super().closeEvent(event)
        watch.disconnect(self.liveupdate)



class WdgDataInfo(QtWidgets.QFrame):
    varChanged = QtCore.pyqtSignal(dict)
    imgChanged = QtCore.pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()

        self.dataloader = None
        self.img_dict = {}
        self.var_dict = {}

        self.init_gui()
        self.init_con()


    def init_gui(self):
        self.setObjectName("dataInfoPanel")

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        # BUTTONS NEXT, PREVIOUS
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        self.btnPrevious = QtWidgets.QPushButton("Previous")
        self.btnPrevious.setFixedHeight(50)
        self.btnPrevious.setFixedWidth(205)
        self.btnPrevious.setShortcut('left')
        hbox.addWidget(self.btnPrevious)

        self.btnNext = QtWidgets.QPushButton("Next")
        self.btnNext.setFixedHeight(50)
        self.btnNext.setFixedWidth(205)
        self.btnNext.setShortcut('right')
        hbox.addWidget(self.btnNext)

        hbox.addStretch(1)

        # INDEX
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        lbl = QtWidgets.QLabel("INDEX:")
        lbl.setFixedWidth(100)
        hbox.addWidget(lbl)

        self.cboIndex = QtWidgets.QComboBox()
        self.cboIndex.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.cboIndex.setFixedWidth(320)
        hbox.addWidget(self.cboIndex)

        hbox.addStretch(1)


        # IMAGE
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        lbl = QtWidgets.QLabel("IMAGE:")
        lbl.setFixedWidth(100)
        hbox.addWidget(lbl)

        self.cboImage = QtWidgets.QComboBox()
        self.cboImage.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.cboImage.setFixedWidth(320)
        self.cboImage.addItems(["None"])
        hbox.addWidget(self.cboImage)

        hbox.addStretch(1)

        # ANALYSIS SELECTOR
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        lbl = QtWidgets.QLabel("PLUGIN:")
        lbl.setFixedWidth(100)
        hbox.addWidget(lbl)

        self.cboPlugin = QtWidgets.QComboBox()
        self.cboPlugin.setFixedWidth(320)
        self.cboPlugin.addItems(["None"])
        hbox.addWidget(self.cboPlugin)

        hbox.addStretch(1)

        for combo in (self.cboIndex, self.cboImage, self.cboPlugin):
            combo.setMinimumHeight(28)
            style = _ComboBoxStyle("Fusion")
            style.setParent(combo)
            combo.setStyle(style)
            palette = style.standardPalette()
            palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#202124"))
            palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#202124"))
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#202124"))
            combo.setPalette(palette)
            view = QtWidgets.QListView(combo)
            view.setStyle(style)
            view.setItemDelegate(QtWidgets.QStyledItemDelegate(view))
            combo.setView(view)




    def init_con(self):
        self.btnPrevious.clicked.connect(self.on_btnPrevious_clicked)
        self.btnNext.clicked.connect(self.on_btnNext_clicked)
        self.cboIndex.currentIndexChanged.connect(self.on_cboIndex_changed)
        self.cboImage.currentTextChanged.connect(self.on_cboImage_changed)



    def update(self, dataloader):
        self.dataloader = dataloader
        self.cboIndex.blockSignals(True)
        self.cboIndex.clear()
        self.cboIndex.addItems([str(n+1) + " / " + str(self.dataloader.num()) for n in np.arange(self.dataloader.num())[::-1]])
        self.cboIndex.setCurrentIndex(-1)
        self.cboIndex.blockSignals(False)
        if self.dataloader.num():
            self.cboIndex.setCurrentIndex(0)
        else:
            self.img_dict = {}
            self.var_dict = {}
            self.cboImage.clear()
            self.on_cboImage_changed()
            self.varChanged.emit(self.var_dict)




    def on_btnPrevious_clicked(self):
        index = self.cboIndex.currentIndex()
        if index == self.cboIndex.count() - 1:
            index = 0
        else:
            index = index + 1
        self.cboIndex.setCurrentIndex(index)


    def on_btnNext_clicked(self):
        index = self.cboIndex.currentIndex()
        if index == 0:
            index = self.cboIndex.count() - 1
        else:
            index = index - 1
        self.cboIndex.setCurrentIndex(index)


    def on_cboIndex_changed(self):
        ind = int(self.cboIndex.currentText().split("/")[0]) - 1
        if ind < 0:
            self.img_dict = {}
            self.var_dict = {}
        else:
            self.img_dict, self.var_dict = self.dataloader.load(ind)

        img = self.cboImage.currentText()
        self.cboImage.blockSignals(True)
        self.cboImage.clear()
        if len(self.img_dict) > 0:
            img_list = [key for key in self.img_dict]
            if img not in img_list:
                img = img_list[0]
                for item in img_list:
                    image_type = item.rsplit(config.SEPARATOR, 1)[-1]
                    if image_type == config.DEFAULT_IMAGE:
                        img = item
                        break

            self.cboImage.addItems(img_list)
            self.cboImage.setCurrentIndex(-1)
        self.cboImage.blockSignals(False)
        if len(self.img_dict) > 0:
            self.cboImage.setCurrentText(img)
        else:
            self.on_cboImage_changed()

        self.varChanged.emit(self.var_dict)


    def on_cboImage_changed(self):
        img = self.cboImage.currentText()
        if self.img_dict.get(img, None) is not None:
            self.imgChanged.emit(self.img_dict[self.cboImage.currentText()])
        else:
            self.imgChanged.emit(np.array([[]]))


class WdgImageInfo(QtWidgets.QFrame):
    roiChanged = QtCore.pyqtSignal(list)
    roiEnabled = QtCore.pyqtSignal(bool)
    crosshairChanged = QtCore.pyqtSignal(list)
    crosshairEnabled = QtCore.pyqtSignal(bool)
    colorbarChanged = QtCore.pyqtSignal(list)
    colorbarEnabled = QtCore.pyqtSignal(bool)


    def __init__(self):
        super().__init__()

        self.init_gui()
        self.init_con()


    def init_gui(self):
        self.setObjectName("imageInfoPanel")

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        # COLORBAR
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        lb = QtWidgets.QLabel("COLORBAR:")
        lb.setFixedWidth(100)
        hbox.addWidget(lb)

        self.txtColorbar = QtWidgets.QLineEdit()
        self.txtColorbar.setFixedWidth(240)
        hbox.addWidget(self.txtColorbar)

        self.chkColorbar = QtWidgets.QCheckBox()
        self.chkColorbar.setChecked(False)
        hbox.addWidget(self.chkColorbar)
        hbox.addWidget(QtWidgets.QLabel("Update"))

        hbox.addStretch(1)

        # CROSSHAIR
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        lb = QtWidgets.QLabel("CROSSHAIR:")
        lb.setFixedWidth(100)
        hbox.addWidget(lb)

        self.txtCrosshair = QtWidgets.QLineEdit()
        self.txtCrosshair.setFixedWidth(240)
        hbox.addWidget(self.txtCrosshair)

        self.chkCrosshair = QtWidgets.QCheckBox()
        self.chkCrosshair.setChecked(False)
        self.chkCrosshair.setShortcut('up')
        hbox.addWidget(self.chkCrosshair)
        hbox.addWidget(QtWidgets.QLabel("Activate"))

        hbox.addStretch(1)

        # ROI
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        lb = QtWidgets.QLabel("ROI:")
        lb.setFixedWidth(100)
        hbox.addWidget(lb)

        self.txtRoi = QtWidgets.QLineEdit()
        self.txtRoi.setFixedWidth(240)
        hbox.addWidget(self.txtRoi)

        self.chkRoi = QtWidgets.QCheckBox()
        self.chkRoi.setChecked(False)
        self.chkRoi.setShortcut('down')
        hbox.addWidget(self.chkRoi)
        hbox.addWidget(QtWidgets.QLabel("Activate"))

        hbox.addStretch(1)


    def init_con(self):
        self.txtColorbar.returnPressed.connect(self.on_txtColorbar_changed)
        self.chkColorbar.stateChanged.connect(self.on_chkColorbar_changed)
        self.txtCrosshair.returnPressed.connect(self.on_txtCrosshair_changed)
        self.chkCrosshair.stateChanged.connect(self.on_chkCrosshair_changed)
        self.txtRoi.returnPressed.connect(self.on_txtRoi_changed)
        self.chkRoi.stateChanged.connect(self.on_chkRoi_changed)


    def on_chkColorbar_changed(self, state):
        self.colorbarEnabled.emit(state)

    def on_chkRoi_changed(self, state):
        self.roiEnabled.emit(state)

    def on_chkCrosshair_changed(self, state):
        self.crosshairEnabled.emit(state)

    def on_txtColorbar_changed(self):
        self.colorbarChanged.emit(self.get_colorbar())
        self.chkColorbar.setChecked(False)

    def on_txtRoi_changed(self):
        self.roiChanged.emit(self.get_roi())
        self.chkRoi.setChecked(True)

    def on_txtCrosshair_changed(self):
        self.crosshairChanged.emit(self.get_crosshair())
        self.chkCrosshair.setChecked(True)


    def get_roi(self):
        text = self.txtRoi.text()
        roi = [float(s) for s in text.strip("()").split(",")]
        return roi

    def set_roi(self, roi):
        text = "({:}, {:}, {:}, {:})".format(*roi)
        self.txtRoi.setText(text)

    def get_crosshair(self):
        text = self.txtCrosshair.text()
        pos = [float(c) for c in text.strip("()").split(",")]
        return pos

    def set_crosshair(self, pos):
        text = "({:}, {:})".format(*pos)
        self.txtCrosshair.setText(text)

    def get_colorbar(self):
        text = self.txtColorbar.text()
        limits = [float(s) for s in text.strip("()").split(",")]
        return limits

    def set_colorbar(self, limits):
        text = "({:.1f}, {:.1f})".format(*limits)
        self.txtColorbar.setText(text)





class WdgImageView(pg.GraphicsLayoutWidget):
    roiChanged = QtCore.pyqtSignal(list)
    crosshairChanged = QtCore.pyqtSignal(list)
    colorbarChanged = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self.image = None
        self.autolevels = False

        self.init_gui()
        self.init_con()


    def init_gui(self):
        background = "#202124"
        self.setBackground(background)
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        size = int(0.15 * min(screen.width(), screen.height()))

        # PLOTS
        self.pltY = self.addPlot(0,0)
        self.pltX = self.addPlot(1,1)
        self.pltXY = self.addPlot(0,1)

        self.pltY.setMaximumWidth(size)
        self.pltX.setMaximumHeight(size)
        self.pltX.showGrid(x=True, y=True)
        self.pltY.showGrid(x=True, y=True)
        self.pltXY.setAspectLocked(True)
        for plot in (self.pltX, self.pltY, self.pltXY):
            plot.getViewBox().setBackgroundColor(background)
            for axis_name in ("left", "bottom", "right", "top"):
                axis = plot.getAxis(axis_name)
                axis.setPen("#d8d8d8")
                axis.setTextPen("#d8d8d8")


        # IMAGE
        # ImageItem renders NaNs transparently.  A black item limited to the
        # image bounds keeps NaNs black without darkening the surrounding plot.
        self.imgBackground = QtWidgets.QGraphicsRectItem()
        self.imgBackground.setBrush(pg.mkBrush("k"))
        self.imgBackground.setPen(pg.mkPen(None))
        self.imgBackground.setZValue(-1)
        self.pltXY.addItem(self.imgBackground)

        self.imgXY = pg.ImageItem()
        self.imgXY.setBorder("g")
        self.pltXY.addItem(self.imgXY)

        # COLORBAR
        self.wdgColorbar = pg.HistogramLUTItem()
        self.wdgColorbar.gradient.loadPreset("flame")
        self.wdgColorbar.setImageItem(self.imgXY)
        self.wdgColorbar.setLevels(*config.DEFAULT_COLORBAR)
        self.wdgColorbar.vb.setBackgroundColor(background)
        self.wdgColorbar.axis.setPen("#d8d8d8")
        self.wdgColorbar.axis.setTextPen("#d8d8d8")
        self.addItem(self.wdgColorbar, 0, 2)

        # ROI
        self.wdgRoi = pg.ROI([0, 0], movable=True, pen=pg.mkPen(color="g", width=2), hoverPen=pg.mkPen(color="g", width=5))
        self.wdgRoi.handleSize = 10
        self.wdgRoi.addScaleHandle([0.5, 1], [0.5, 0.5])
        self.wdgRoi.addScaleHandle([0, 0.5], [0.5, 0.5])
        self.wdgRoi.addScaleHandle([0, 0], [1, 1])
        self.wdgRoi.addScaleHandle([1, 0], [0, 1])
        self.wdgRoi.addScaleHandle([0, 1], [1, 0])
        self.wdgRoi.addScaleHandle([1, 1], [0, 0])
        self.wdgRoi.hide()
        self.pltXY.addItem(self.wdgRoi)

        # CROSSHAIR
        self.wdgYCrosshair = pg.InfiniteLine(pos=0, angle=0, movable=True, pen=pg.mkPen(color="y", width=1), hoverPen=pg.mkPen(color="y", width=5))
        self.wdgXCrosshair = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen(color="y", width=1), hoverPen=pg.mkPen(color="y", width=5))
        self.wdgYCrosshair.hide()
        self.wdgXCrosshair.hide()
        self.pltXY.addItem(self.wdgYCrosshair)
        self.pltXY.addItem(self.wdgXCrosshair)


    def init_con(self):
        self.wdgColorbar.sigLevelChangeFinished.connect(self.on_wdgColorbar_changed)
        self.wdgRoi.sigRegionChangeFinished.connect(self.on_wdgRoi_changed)
        self.wdgXCrosshair.sigPositionChangeFinished.connect(self.on_wdgCrosshair_changed)
        self.wdgYCrosshair.sigPositionChangeFinished.connect(self.on_wdgCrosshair_changed)


    def on_wdgColorbar_changed(self):
        self.colorbarChanged.emit(self.get_colorbar())

    def on_wdgRoi_changed(self):
        self.roiChanged.emit(self.get_roi())
        self.refresh()

    def on_wdgCrosshair_changed(self):
        self.crosshairChanged.emit(self.get_crosshair())
        self.refresh()


    def set_image(self, image):
        self.image = np.asarray(image, dtype=float)
        if self.image.ndim != 2 or 0 in self.image.shape:
            self.imgXY.clear()
            self.imgBackground.setRect(QtCore.QRectF())
            self.refresh()
            return
        self.imgXY.setImage(self.image.T, autoLevels=self.autolevels)
        self.imgBackground.setRect(self.imgXY.boundingRect())
        self.on_wdgColorbar_changed()

        crosshair = self.wdgXCrosshair.isVisible() and self.wdgYCrosshair.isVisible()
        if not crosshair and not self.wdgRoi.isVisible():
            size = min(self.image.shape) * 0.25
            centre = np.asarray(self.image.shape) / 2
            self.wdgRoi.setPos(centre[1] - size / 2, centre[0] - size / 2, update=False)
            self.wdgRoi.setSize((size, size), update=True)
            self.wdgYCrosshair.setPos(centre[0])
            self.wdgXCrosshair.setPos(centre[1])
            self.roiChanged.emit(self.get_roi())
            self.crosshairChanged.emit(self.get_crosshair())

        self.refresh()

    def refresh(self):
        self.pltX.clear()
        self.pltY.clear()

        if self.image is None or self.image.ndim != 2 or 0 in self.image.shape:
            return

        roi = self.get_roi() if self.wdgRoi.isVisible() else [0, self.image.shape[0], 0, self.image.shape[1]]
        roi[0] = max(0, min(roi[0], self.image.shape[0]))
        roi[1] = max(roi[0], min(roi[1], self.image.shape[0]))
        roi[2] = max(0, min(roi[2], self.image.shape[1]))
        roi[3] = max(roi[2], min(roi[3], self.image.shape[1]))
        image = self.image[roi[0]:roi[1], roi[2]:roi[3]]
        if 0 in image.shape:
            return

        ind_y = roi[0] + np.arange(image.shape[0])
        if self.wdgXCrosshair.isVisible():
            pos_x = round(self.wdgXCrosshair.value()) - roi[2]
            if 0 <= pos_x < image.shape[1]:
                self.pltY.plot(image[:, pos_x], ind_y)
        else:
            self.pltY.plot(np.nansum(image, axis=1), ind_y)

        ind_x = roi[2] + np.arange(image.shape[1])
        if self.wdgYCrosshair.isVisible():
            pos_y = round(self.wdgYCrosshair.value()) - roi[0]
            if 0 <= pos_y < image.shape[0]:
                self.pltX.plot(ind_x, image[pos_y, :])
        else:
            self.pltX.plot(ind_x, np.nansum(image, axis=0))



    def enable_colorbar(self, enabled):
        self.autolevels = enabled
        if self.autolevels:
            self.imgXY.setImage(self.image.T, autoLevels=True)


    def enable_roi(self, enabled):
        if enabled and self.wdgXCrosshair.isVisible() and self.wdgYCrosshair.isVisible():
            size = np.asarray(self.wdgRoi.size())[::-1]
            pos_y = self.wdgYCrosshair.value() - size[0] / 2
            pos_x = self.wdgXCrosshair.value() - size[1] / 2
            self.wdgRoi.setPos(pos_x, pos_y, update=False)
            self.wdgRoi.setSize((size[1], size[0]), update=True)
        if enabled:
            self.wdgRoi.show()
        else:
            self.wdgRoi.hide()
        self.refresh()


    def enable_crosshair(self, enabled):
        if enabled and self.wdgRoi.isVisible():
            pos = np.asarray(self.wdgRoi.pos())[::-1]
            size = np.asarray(self.wdgRoi.size())[::-1]
            pos = pos + size / 2
            self.wdgYCrosshair.setPos(pos[0])
            self.wdgXCrosshair.setPos(pos[1])
        if enabled:
            self.wdgYCrosshair.show()
            self.wdgXCrosshair.show()
        else:
            self.wdgYCrosshair.hide()
            self.wdgXCrosshair.hide()
        self.refresh()


    def get_roi(self):
        pos = np.asarray(self.wdgRoi.pos())[::-1]
        size = np.asarray(self.wdgRoi.size())[::-1]
        roi = [round(pos[0]), round(pos[0]+size[0]), round(pos[1]), round(pos[1]+size[1])]
        return roi

    def set_roi(self, roi):
        self.wdgRoi.setPos(roi[2], roi[0])
        self.wdgRoi.setSize((roi[3]-roi[2], roi[1]-roi[0]))
        self.refresh()

    def get_crosshair(self):
        pos = [round(self.wdgYCrosshair.value()), round(self.wdgXCrosshair.value())]
        return pos

    def set_crosshair(self, pos):
        self.wdgYCrosshair.setPos(pos[0])
        self.wdgXCrosshair.setPos(pos[1])
        self.refresh()

    def get_colorbar(self):
        limits = list(self.wdgColorbar.getLevels())
        return limits

    def set_colorbar(self, limits):
        self.wdgColorbar.setLevels(*limits)




class WdgDataView(QtWidgets.QTableView):
    def __init__(self):
        super().__init__()

        self.init_gui()


    def init_gui(self):
        self.setModel(TableModel({}))
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 200)
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setMinimumHeight(28)
        self.verticalHeader().setDefaultSectionSize(27)
        self.verticalHeader().setVisible(False)


    def update(self, var):
        self.setModel(TableModel(var))
        parent = self
        while not isinstance(parent, Viewer):
            parent = parent.parent()
        title = parent.title
        if "FILE" in var:
            title += " - " + str(var["FILE"])
        parent.setWindowTitle(title)





class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.headers = ['NAME', 'VALUE']

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            if index.column() == 0:
                return TableModel.formatter(list(self.data.keys())[row])
            elif index.column() == 1:
                return TableModel.formatter(list(self.data.values())[row])
        return None

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return self.headers[section]

    @staticmethod
    def formatter(item):
        if isinstance(item, np.generic):
            item = item.item()
        if isinstance(item, float):
            return f"{item:.3g}"
        if isinstance(item, (tuple, list, dict)):
            return _TABLE_PRINTER.pformat(item)
        return str(item)



class DataLoader:
    def __init__(self, data):
        if isinstance(data, pd.DataFrame):
            self.data = [data.iloc[n] for n in range(len(data))]
        elif isinstance(data, (dict, pd.Series)) or DataLoader.is_image(data):
            self.data = [data]
        elif isinstance(data, (str, bytes, PathLike)):
            self.data = list_file(data)
        else:
            self.data = [
                os.fsdecode(item) if isinstance(item, (str, bytes, PathLike)) else item
                for item in data
            ]

    def num(self):
        return len(self.data)


    def load(self, index):
        data = self.data[index]
        if isinstance(data, str):
            loaded = load_file(data)
            if len(loaded) != 1:
                raise ValueError(
                    "A lab load_file function must return one DataFrame row per file"
                )
            data = loaded.iloc[0]

        if isinstance(data, (dict, pd.Series)):
            flat = ravel(data if isinstance(data, dict) else data.to_dict())
            img_dict = {
                key: value
                for key, value in flat.items()
                if DataLoader.is_image(value)
            }
            var_dict = {
                key: value
                for key, value in flat.items()
                if not DataLoader.is_image(value)
            }
        elif DataLoader.is_image(data):
            img_dict = {"IMAGE": data}
            var_dict = {}
        else:
            img_dict = {}
            var_dict = {}

        return img_dict, var_dict


    def img(self, index):
        return self.load(index)[0]


    def var(self, index):
        return self.load(index)[1]


    @staticmethod
    def is_image(obj):
        return isinstance(obj, np.ndarray) and obj.ndim==2


if __name__ == "__main__":
    viewer([], live=True)
